"""
PesaGuard Webhook Receiver
Receives M-Pesa Daraja callbacks (C2B/B2C/STK Push confirmation),
validates payload, and pushes to Kafka for downstream reconciliation.
"""
import logging
import os
import sys
import hashlib
import secrets
import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request, Response
from werkzeug.exceptions import HTTPException

from pesaguard_backend_pipeline.security_helpers import (
    get_client_ip,
    is_allowed_source,
    is_payload_within_limit,
    sanitize_error_message,
)
from pesaguard_backend_pipeline.rate_limiter import RateLimiter

from pesaguard_backend_pipeline.event_store import EventStore, ProcessResult
from pesaguard_backend_pipeline.health import build_health_payload
from pesaguard_backend_pipeline.logging_utils import configure_logging, set_correlation_id, get_correlation_id
from pesaguard_backend_pipeline.validators import (
    extract_canonical_event,
    validate_airtel_payload,
    validate_daraja_payload,
)
from pesaguard_backend_pipeline.background_tasks import enqueue_transaction_event
from pesaguard_backend_pipeline.producer import publish_transaction_event
from pesaguard_backend_pipeline.tenant_settings import TenantSettingsStore
from pesaguard_backend_pipeline.metrics import build_metrics_payload
from pesaguard_backend_pipeline.auth_rbac import get_current_user, require_auth
from pesaguard_backend_pipeline.api_gateway import ApiGateway, ApiGatewayConfig
from pesaguard_backend_pipeline.shared.airtel.config import AirtelConfig
from pesaguard_backend_pipeline.shared.airtel.payment_client import AirtelPaymentClient
from pesaguard_backend_pipeline.shared.bank.config import BankConfig
from pesaguard_backend_pipeline.shared.bank.payment_client import BankPaymentClient
from pesaguard_backend_pipeline.bank_service import BankService
from pesaguard_backend_pipeline.base_connector import ConnectorRegistry
from pesaguard_backend_pipeline.settlement_engine import SettlementEngine
from flask import abort
import time
from flask import Response

configure_logging()
init_observability = None
try:
    from pesaguard_backend_pipeline.logging_utils import configure_logging, set_correlation_id, get_correlation_id, init_observability
    init_observability()
except Exception:
    pass
logger = logging.getLogger("pesaguard.webhook")

app = Flask(__name__)
api_gateway = ApiGateway(
    app,
    ApiGatewayConfig(
        default_version="v1",
        require_auth=False,
        allowed_origins=["*"],
        rate_limit_per_minute=int(os.getenv("PESAGUARD_WEBHOOK_RATE_LIMIT_PER_MINUTE", "30")),
        allow_json_validation=True,
        cache_ttl_seconds=60,
    ),
)
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("PESAGUARD_WEBHOOK_MAX_BODY_BYTES", "1048576"))
event_store = EventStore()
webhook_rate_limiter = RateLimiter()
webhook_rate_limiter.set_limits(int(os.getenv("PESAGUARD_WEBHOOK_RATE_LIMIT_PER_MINUTE", "30")))

KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_TRANSACTIONS", "mpesa.transactions.raw")


def _request_id_value() -> str:
    return (
        request.headers.get("X-Request-ID")
        or request.headers.get("X-Correlation-ID")
        or str(uuid.uuid4())
    )


def _standard_response(payload: dict, status: int = 200, meta: dict | None = None):
    body = {
        "status": "success" if 200 <= status < 400 else "error",
        "data": payload,
        "request_id": _request_id_value(),
        "tenant_id": os.getenv("TENANT_ID", "default"),
    }
    if meta:
        body["meta"] = meta
    return jsonify(body), status


def _standard_error(code: str, message: str, status_code: int = 400, details: dict | None = None):
    body = {
        "status": "error",
        "error": {"code": code, "message": message},
        "request_id": _request_id_value(),
        "tenant_id": os.getenv("TENANT_ID", "default"),
        "ResultCode": 1,
        "ResultDesc": message,
    }
    if details:
        body["error"]["details"] = details
    return jsonify(body), status_code

# Simple admin-auth for pilot Admin API endpoints
tenant_store = TenantSettingsStore()


def _account_context():
    """Return the authenticated principal and tenant-scoped account record."""
    user = get_current_user()
    # The fallback only exists when API authentication is deliberately disabled
    # for local development and tests. Production always requires a JWT.
    if user is None:
        user_id = request.headers.get("X-PesaGuard-User-ID", "local-user")
        username = request.headers.get("X-PesaGuard-Username", user_id)
        tenant_id = os.getenv("TENANT_ID", "default")
    else:
        user_id, username, tenant_id = user.user_id, user.username, user.tenant_id

    settings = tenant_store.get(tenant_id)
    accounts = dict(settings.get("accounts") or {})
    account = dict(accounts.get(str(user_id)) or {})
    account.setdefault("display_name", username)
    account.setdefault("email", username if "@" in username else "")
    account.setdefault("job_title", "")
    account.setdefault("phone", "")
    account.setdefault("avatar_url", "")
    account.setdefault("timezone", "Africa/Nairobi")
    account.setdefault("language", tenant_store.resolve_locale(tenant_id, str(user_id)))
    account.setdefault("appearance", "system")
    account.setdefault("privacy", {"mask_sensitive_data": True, "share_profile": False, "security_alerts": True})
    account.setdefault("notifications", {"email_alerts": True, "product_updates": False, "weekly_digest": True})
    account.setdefault("api_tokens", [])
    return tenant_id, str(user_id), username, accounts, account


def _public_account(account, user_id, username):
    """Return account data without token secrets or internal hashes."""
    tokens = [
        {key: value for key, value in token.items() if key not in {"secret_hash"}}
        for token in account.get("api_tokens", [])
    ]
    return {
        "user_id": user_id,
        "username": username,
        **{key: value for key, value in account.items() if key != "api_tokens"},
        "api_tokens": tokens,
    }


def _save_account(tenant_id, user_id, accounts, account):
    accounts[str(user_id)] = account
    tenant_store.update(tenant_id, {"accounts": accounts})


@app.route("/account/me", methods=["GET"])
@require_auth()
def get_account_me():
    tenant_id, user_id, username, _accounts, account = _account_context()
    return jsonify({"tenant_id": tenant_id, "account": _public_account(account, user_id, username)}), 200


@app.route("/account/me", methods=["PATCH"])
@require_auth()
def update_account_me():
    payload = request.get_json(silent=True) or {}
    tenant_id, user_id, username, accounts, account = _account_context()
    allowed_text = {"display_name", "job_title", "phone", "avatar_url", "timezone", "appearance", "language"}
    for key in allowed_text:
        if key in payload:
            value = payload[key]
            if not isinstance(value, str) or len(value.strip()) > 160:
                return jsonify({"error": f"invalid_{key}"}), 400
            account[key] = value.strip()
    for key in {"privacy", "notifications"}:
        if key in payload:
            value = payload[key]
            if not isinstance(value, dict) or not all(isinstance(item, bool) for item in value.values()):
                return jsonify({"error": f"invalid_{key}"}), 400
            account[key] = {**account.get(key, {}), **value}
    _save_account(tenant_id, user_id, accounts, account)
    return jsonify({"account": _public_account(account, user_id, username)}), 200


@app.route("/account/me/api-tokens", methods=["POST"])
@require_auth()
def create_account_api_token():
    payload = request.get_json(silent=True) or {}
    label = str(payload.get("label", "")).strip()
    scopes = payload.get("scopes", ["read:discrepancies"])
    if not label or len(label) > 80 or not isinstance(scopes, list) or not all(isinstance(scope, str) for scope in scopes):
        return jsonify({"error": "invalid_token_request"}), 400
    tenant_id, user_id, username, accounts, account = _account_context()
    secret = f"pg_{secrets.token_urlsafe(30)}"
    token = {
        "id": secrets.token_hex(8), "label": label, "scopes": scopes[:12],
        "prefix": secret[:11], "created_at": datetime.now(timezone.utc).isoformat(),
        "last_used_at": None, "secret_hash": hashlib.sha256(secret.encode("utf-8")).hexdigest(),
    }
    account["api_tokens"] = [*account.get("api_tokens", []), token]
    _save_account(tenant_id, user_id, accounts, account)
    return jsonify({"token": {key: value for key, value in token.items() if key != "secret_hash"}, "secret": secret}), 201


@app.route("/account/me/api-tokens/<token_id>", methods=["DELETE"])
@require_auth()
def revoke_account_api_token(token_id: str):
    tenant_id, user_id, username, accounts, account = _account_context()
    tokens = account.get("api_tokens", [])
    remaining = [token for token in tokens if token.get("id") != token_id]
    if len(remaining) == len(tokens):
        return jsonify({"error": "token_not_found"}), 404
    account["api_tokens"] = remaining
    _save_account(tenant_id, user_id, accounts, account)
    return jsonify({"account": _public_account(account, user_id, username)}), 200


@app.route("/account/me/credential-requests", methods=["POST"])
@require_auth()
def create_credential_request():
    """Record a verified email/password change request for the identity provider."""
    payload = request.get_json(silent=True) or {}
    request_type = payload.get("type")
    if request_type not in {"email_change", "password_change", "account_deletion"}:
        return jsonify({"error": "invalid_request_type"}), 400
    if request_type == "email_change":
        email = str(payload.get("email", "")).strip().lower()
        if "@" not in email or len(email) > 160:
            return jsonify({"error": "invalid_email"}), 400
    tenant_id, user_id, username, accounts, account = _account_context()
    requests = list(account.get("credential_requests", []))
    requests.append({"type": request_type, "created_at": datetime.now(timezone.utc).isoformat(), "status": "pending"})
    account["credential_requests"] = requests[-20:]
    _save_account(tenant_id, user_id, accounts, account)
    return jsonify({"status": "pending", "message": "Your identity change request has been recorded for verification."}), 202


def _require_admin():
    token = request.headers.get("X-Admin-Token") or request.args.get("admin_token")
    admin_api_token = os.getenv("PESAGUARD_ADMIN_API_TOKEN")
    if not admin_api_token or token != admin_api_token:
        abort(403)


@app.route("/admin/tenant/<tenant_id>", methods=["GET"])
def admin_get_tenant(tenant_id: str):
    _require_admin()
    return jsonify(tenant_store.get(tenant_id)), 200


@app.route("/admin/tenant/<tenant_id>", methods=["POST"])
def admin_update_tenant(tenant_id: str):
    _require_admin()
    payload = request.get_json(silent=True) or {}
    updated = tenant_store.update(tenant_id, payload)
    return jsonify(updated), 200


@app.route("/admin/tenant/<tenant_id>/residency", methods=["GET"])
def admin_get_residency(tenant_id: str):
    _require_admin()
    return jsonify(tenant_store.get_residency_context(tenant_id)), 200


@app.route("/admin/tenant/<tenant_id>/locale", methods=["POST"])
def admin_set_locale(tenant_id: str):
    _require_admin()
    payload = request.get_json(silent=True) or {}
    preferred = payload.get("preferred_locale")
    if not preferred:
        return jsonify({"error": "preferred_locale required"}), 400
    updated = tenant_store.update(tenant_id, {"preferred_locale": preferred})
    return jsonify(updated), 200


@app.route("/tenant/current", methods=["GET"])
def public_get_current_tenant():
    """Public, read-only endpoint returning limited tenant preferences for the current runtime tenant."""
    tenant_id = os.getenv("TENANT_ID", "default")
    settings = tenant_store.get(tenant_id)
    public = {
        "tenant_id": tenant_id,
        "preferred_locale": settings.get("preferred_locale"),
        "deployment_region": settings.get("deployment_region"),
    }
    return jsonify(public), 200


@app.route("/tenant/current/locale", methods=["GET"])
def public_get_current_locale():
    """Return tenant default, optional user override, and effective locale."""
    tenant_id = os.getenv("TENANT_ID", "default")
    user_id = request.args.get("user_id")
    settings = tenant_store.get(tenant_id)
    user_locale = None
    if user_id:
        overrides = settings.get("user_locale_overrides") or {}
        if isinstance(overrides, dict):
            user_locale = overrides.get(user_id) or overrides.get(str(user_id))
    effective = tenant_store.resolve_locale(tenant_id, user_id)
    return jsonify({
        "tenant_id": tenant_id,
        "preferred_locale": settings.get("preferred_locale"),
        "user_locale": user_locale,
        "effective_locale": effective,
    }), 200


@app.route("/tenant/current/locale", methods=["POST"])
def public_set_current_tenant_locale():
    """Persist the current tenant's preferred locale through the public tenant endpoint."""
    payload = request.get_json(silent=True) or {}
    preferred = payload.get("preferred_locale")
    if not preferred:
        return jsonify({"error": "preferred_locale required"}), 400

    tenant_id = os.getenv("TENANT_ID", "default")
    updated = tenant_store.update(tenant_id, {"preferred_locale": preferred})
    return jsonify({"tenant_id": tenant_id, "preferred_locale": updated.get("preferred_locale")}), 200


@app.route("/tenant/current/user-locale", methods=["POST"])
def public_set_user_locale():
    """Persist a per-user locale override for the current tenant."""
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id")
    preferred = payload.get("preferred_locale")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    tenant_id = os.getenv("TENANT_ID", "default")
    existing = tenant_store.get(tenant_id)
    overrides = dict(existing.get("user_locale_overrides") or {})
    if preferred is None or preferred == "":
        overrides.pop(str(user_id), None)
    else:
        overrides[str(user_id)] = preferred
    tenant_store.update(tenant_id, {"user_locale_overrides": overrides})
    effective = tenant_store.resolve_locale(tenant_id, str(user_id))
    return jsonify({
        "tenant_id": tenant_id,
        "user_id": str(user_id),
        "user_locale": overrides.get(str(user_id)),
        "effective_locale": effective,
    }), 200


@app.errorhandler(413)
def handle_request_too_large(_error):
    return _standard_error("request_too_large", "Request body too large", 413)


@app.errorhandler(400)
def handle_bad_request(_error):
    return _standard_error("invalid_request", "Invalid request", 400)


@app.errorhandler(Exception)
def handle_internal_error(error):
    if isinstance(error, HTTPException):
        return error

    logger.exception("Unhandled exception in webhook receiver", exc_info=error)
    return _standard_error("internal_server_error", "Internal server error", 500)


@app.before_request
def setup_request_context():
    """Set up per-request context including correlation ID for tracing."""
    correlation_id = (
        request.headers.get("X-Trace-Id")
        or request.headers.get("X-Correlation-ID")
        or request.headers.get("X-Request-ID")
        or get_correlation_id()
    )
    request.environ["pesaguard.request_id"] = correlation_id
    request.environ["pesaguard.correlation_id"] = correlation_id
    set_correlation_id(correlation_id)


@app.after_request
def add_correlation_id_header(response):
    """Add correlation and trace headers to response headers for client tracing."""
    correlation_id = request.environ.get("pesaguard.correlation_id") or get_correlation_id() or _request_id_value()
    request_id = request.environ.get("pesaguard.request_id") or request.headers.get("X-Request-ID") or correlation_id
    tenant_id = request.headers.get("X-Tenant-ID") or os.getenv("TENANT_ID", "default")
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Trace-Id"] = request_id
    response.headers["X-Tenant-ID"] = tenant_id
    return response


@app.route("/status", methods=["GET"])
def status_summary():
    """Public deployment status summary with health and trace metadata."""
    request_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID") or request.headers.get("X-Trace-Id") or get_correlation_id()
    payload = build_health_payload()
    payload["service"] = "pesaguard"
    payload["request_id"] = request_id
    payload["tenant_id"] = request.headers.get("X-Tenant-ID") or os.getenv("TENANT_ID", "default")
    payload["trace_id"] = request_id
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    payload["ux"] = {
        "theme": "premium",
        "status_label": {
            "ok": "Healthy",
            "degraded": "Degraded",
            "failed": "Critical",
        }.get(payload.get("status", "unknown"), "Unknown"),
        "tone": {
            "ok": "success",
            "degraded": "warning",
            "failed": "danger",
        }.get(payload.get("status", "unknown"), "neutral"),
    }
    status_code = 503 if payload.get("status") == "failed" else 200
    return jsonify(payload), status_code


@app.before_request
def enforce_webhook_security():
    if request.method == "OPTIONS":
        return None

    if not is_payload_within_limit(request):
        return jsonify({"ResultCode": 1, "ResultDesc": "Request body too large"}), 413

    if request.path == "/webhook" or request.path.startswith("/webhook/"):
        source_ip = get_client_ip(request)

        if not is_allowed_source(source_ip, request):
            logger.warning("Webhook request rejected: forbidden source IP", extra={"source_ip": source_ip})
            return jsonify({"ResultCode": 1, "ResultDesc": "Forbidden source"}), 403

        allowed, status = webhook_rate_limiter.is_allowed(
            source_ip,
            request.path,
        )
        if not allowed:
            logger.warning("Webhook request rejected: rate limit exceeded", extra={"source_ip": source_ip})
            response = jsonify({"ResultCode": 1, "ResultDesc": "Rate limit exceeded"})
            response.status_code = 429
            response.headers["Retry-After"] = str(status.get("retry_after", 60))
            return response

        daraja_signature = request.headers.get("X-Daraja-Signature")
        if daraja_signature:
            try:
                _verify_daraja_signature(request.data, daraja_signature)
            except Exception as e:
                logger.warning("Webhook signature verification failed", extra={"error": str(e), "source_ip": source_ip})
                return jsonify({"ResultCode": 1, "ResultDesc": "Invalid signature"}), 403


@app.route("/metrics", methods=["GET"])
def metrics():
    try:
        # If prometheus_client is available, prefer its dynamic metrics
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
    except Exception:
        return Response(build_metrics_payload(), mimetype="text/plain; version=0.0.4")


@app.route("/admin/processed/<trans_id>", methods=["GET"])
def admin_get_processed(trans_id: str):
    _require_admin()
    record = event_store.get_processed(trans_id)
    if not record:
        return jsonify({"error": "not_found"}), 404
    return jsonify(record), 200


def _verify_daraja_signature(request_body: bytes, signature: str) -> None:
    """Verify incoming webhook signature from Daraja.
    Raises ValueError if signature is invalid.
    Reference: https://developer.safaricom.co.ke/webhook-signature-validation"""
    import hashlib
    import hmac
    consumer_secret = os.getenv("DARAJA_CONSUMER_SECRET", "")
    if not consumer_secret:
        raise ValueError("DARAJA_CONSUMER_SECRET not configured")

    expected_signature = hmac.new(
        consumer_secret.encode(),
        request_body,
        hashlib.sha256
    ).hexdigest().upper()

    if signature.upper() != expected_signature:
        raise ValueError("Signature mismatch")


@app.route("/health", methods=["GET"])
def health():
    payload = build_health_payload()
    status_code = 503 if payload.get("status") == "failed" else 200
    return jsonify(payload), status_code


@app.route("/webhook/mpesa/confirmation", methods=["POST"])
def mpesa_confirmation():
    """
    Handles C2B confirmation callbacks from Daraja.
    Docs: https://developer.safaricom.co.ke/

    IMPORTANT: the HTTP status/ResultCode returned here directly controls whether
    Daraja retries. STORED and DUPLICATE both mean "safely recorded, no retry
    needed" -> 200. ERROR means "not actually stored" -> non-200, so Daraja retries
    instead of the transaction silently vanishing.
    """
    payload = request.get_json(silent=True)

    if not payload:
        logger.warning("Empty or invalid JSON payload received")
        try:
            event_store.write_dead_letter(None, reason="invalid_json", error_detail="empty_or_invalid_json", tenant_id=os.getenv("TENANT_ID", "default"))
        except Exception:
            logger.debug("Failed to persist dead-letter for invalid JSON payload", exc_info=True)
        return jsonify({"ResultCode": 1, "ResultDesc": "Invalid payload"}), 400

    if not is_payload_within_limit(request):
        return jsonify({"ResultCode": 1, "ResultDesc": "Request body too large"}), 413

    is_valid, error = validate_daraja_payload(payload)
    if not is_valid:
        logger.warning("Payload validation failed: %s", error)
        try:
            event_store.write_dead_letter(payload, reason="validation_failed", error_detail=str(error), tenant_id=os.getenv("TENANT_ID", "default"))
        except Exception:
            logger.debug("Failed to persist dead-letter for validation failure", exc_info=True)
        return jsonify({"ResultCode": 1, "ResultDesc": sanitize_error_message(error)}), 400

    trans_id = payload.get("TransID")
    tenant_id = os.getenv("TENANT_ID", "default")
    source_ip = get_client_ip(request)
    signature_verified = False
    daraja_signature = request.headers.get("X-Daraja-Signature")
    if daraja_signature:
        try:
            _verify_daraja_signature(request.data, daraja_signature)
            signature_verified = True
        except Exception:
            # This should not happen because enforce_webhook_security already verified
            signature_verified = False

    # Fast-path optimization only — NOT the authoritative gate. Two near-simultaneous
    # callbacks can both pass this check before either has written anything; the real
    # guarantee is the unique constraint enforced inside mark_processed() below.
    if event_store.already_processed(str(trans_id)):
        logger.info("Duplicate transaction (pre-check)", extra={"tenant_id": tenant_id, "trans_id": trans_id, "source_ip": source_ip})
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted (duplicate ignored)"}), 200

    # Authoritative idempotency write. Branch on the ACTUAL result — never assume
    # success and never treat an error the same as a duplicate.
    result = event_store.mark_processed(
        payload,
        tenant_id=tenant_id,
        source_ip=source_ip,
        signature_verified=signature_verified,
    )

    if result == ProcessResult.DUPLICATE:
        # A concurrent callback won the race between the pre-check above and this
        # write. Already safely stored by the other request — do not enqueue again,
        # do not process twice downstream.
        logger.info("Duplicate transaction (caught at write time)", extra={"tenant_id": tenant_id, "trans_id": trans_id})
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted (duplicate ignored)"}), 200

    if result == ProcessResult.ERROR:
        # Genuine failure — the transaction was NOT stored. Returning 200 here would
        # cause Daraja to treat this as delivered and never retry, silently losing a
        # real transaction. Return a non-zero ResultCode with a 500 so Daraja retries.
        logger.error("Failed to record transaction, requesting Daraja retry", extra={"tenant_id": tenant_id, "trans_id": trans_id})
        return jsonify({"ResultCode": 1, "ResultDesc": "Temporary processing error, please retry"}), 500

    # result == ProcessResult.STORED: genuinely new, safely persisted. Proceed to
    # enqueue for downstream reconciliation exactly once. Measure end-to-end
    # processing time and update the idempotency ledger status so operators
    # can observe whether publication to downstream systems succeeded.
    start_ns = time.time_ns()

    try:
        import redis
        redis_conn = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), socket_connect_timeout=2)
        cache_key = f"processed_trans_id:{trans_id}"
        redis_conn.set(cache_key, "1", ex=86400)
    except Exception:
        pass  # best-effort cache warm; DB ledger above is the source of truth

    publish_status = "unknown"
    publish_error = None
    try:
        queued = enqueue_transaction_event(KAFKA_TOPIC, payload)
        if queued.get("status") == "queued":
            publish_status = "queued"
            logger.info("Transaction event queued to background job", extra={"trans_id": trans_id})
        else:
            publish_transaction_event(KAFKA_TOPIC, payload)
            publish_status = "published"
            logger.info("Transaction event published to Kafka (sync fallback)", extra={"trans_id": trans_id})
    except Exception as exc:  # noqa: BLE001
        # The transaction IS safely stored (STORED above) — only the downstream
        # publish failed. Log for manual replay; still ack 200 since the source
        # record exists and reconciliation can be re-run against it.
        publish_status = "publish_failed"
        publish_error = str(exc)
        logger.warning("Failed to publish event (queued for manual replay)", extra={"trans_id": trans_id}, exc_info=True)

    # Update processing status with measured latency (best-effort)
    try:
        processing_time_ms = int((time.time_ns() - start_ns) / 1_000_000)
        # Use descriptive status names for operators to inspect
        event_store.update_processing_status(
            trans_id, status=publish_status, error_reason=publish_error, processing_time_ms=processing_time_ms
        )
    except Exception:
        logger.debug("Failed updating processing status for trans_id=%s", trans_id, exc_info=True)

    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200


@app.route("/webhook/mpesa/validation", methods=["POST"])
def mpesa_validation():
    """
    Handles C2B validation callbacks (pre-confirmation).
    Return here to accept/reject a transaction before it completes.
    """
    payload = request.get_json(silent=True) or {}
    logger.info("Validation request for: %s", payload.get("TransID", "unknown"))
    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200


@app.route("/admin/airtel/payments", methods=["POST"])
def admin_airtel_payment():
    """Issue an Airtel Money payout via the tenant-configured provider credentials."""
    _require_admin()
    payload = request.get_json(silent=True) or {}

    tenant_id = payload.get("tenant_id") or request.headers.get("X-Tenant-ID") or os.getenv("TENANT_ID", "default")
    amount = payload.get("amount")
    currency = payload.get("currency") or "UGX"
    reference = payload.get("reference") or payload.get("payment_reference") or f"AIR-{uuid.uuid4().hex[:12]}"
    msisdn = payload.get("msisdn") or payload.get("phone_number") or ""
    description = payload.get("description") or "PesaGuard Airtel payment"

    try:
        amount_value = float(amount)
    except (TypeError, ValueError):
        return jsonify({"error": "amount must be numeric"}), 400

    if amount_value <= 0:
        return jsonify({"error": "amount must be greater than zero"}), 400

    credentials = AirtelConfig(tenant_id=tenant_id).get_credentials()
    if not credentials.get("api_key") or not credentials.get("api_secret"):
        return jsonify({"error": "Airtel credentials are not configured for this tenant"}), 503

    client = AirtelPaymentClient(tenant_id=tenant_id, credentials=credentials)
    try:
        result = client.request_payment(
            amount=amount_value,
            currency=str(currency).upper(),
            reference=str(reference),
            msisdn=str(msisdn),
            description=str(description),
        )
    except Exception as exc:  # pragma: no cover - network/credential path
        logger.exception("Airtel payment request failed for tenant=%s", tenant_id)
        return jsonify({"error": "airtel_payment_failed", "message": str(exc)}), 502

    return jsonify({
        "status": result.get("status") if isinstance(result, dict) else "accepted",
        "tenant_id": tenant_id,
        "transaction_id": result.get("transactionId") if isinstance(result, dict) else None,
        "reference": str(reference),
        "amount": amount_value,
        "currency": str(currency).upper(),
        "payload": result,
    }), 200


@app.route("/admin/airtel/payments/contracts", methods=["GET"])
def admin_airtel_payment_contracts():
    """Return request/response examples for the Airtel Money payout contract."""
    _require_admin()
    return jsonify({
        "payment_channel": "MOBILE_MONEY",
        "provider": "AIRTEL_MONEY",
        "method": "POST",
        "endpoint": "/admin/airtel/payments",
        "request_example": {
            "tenant_id": "tenant-airtel",
            "amount": 2500,
            "currency": "UGX",
            "reference": "INV-AIR-777",
            "msisdn": "256700000001",
            "description": "Loan repayment",
        },
        "success_response_example": {
            "status": "accepted",
            "tenant_id": "tenant-airtel",
            "transaction_id": "AIR-123",
            "reference": "INV-AIR-777",
            "amount": 2500,
            "currency": "UGX",
            "payload": {"status": "accepted", "transactionId": "AIR-123"},
        },
        "error_response_example": {
            "error": "airtel_payment_failed",
            "message": "Airtel credentials are not configured for this tenant",
        },
        "notes": [
            "The amount must be numeric and greater than zero.",
            "Airtel payouts require tenant credentials configured in the Airtel config store.",
            "The request is authenticated by the platform admin token before dispatch.",
        ],
    }), 200


@app.route("/admin/bank/payments", methods=["POST"])
def admin_bank_payment():
    """Issue a bank transfer request via tenant-configured bank credentials."""
    _require_admin()
    payload = request.get_json(silent=True) or {}

    tenant_id = payload.get("tenant_id") or request.headers.get("X-Tenant-ID") or os.getenv("TENANT_ID", "default")
    amount = payload.get("amount")
    currency = payload.get("currency") or "KES"
    reference = payload.get("reference") or payload.get("payment_reference") or f"BANK-{uuid.uuid4().hex[:12]}"
    account_number = payload.get("account_number") or payload.get("accountNumber") or ""
    bank_name = payload.get("bank_name") or payload.get("bankName") or ""
    narration = payload.get("narration") or payload.get("description") or "PesaGuard bank transfer"

    try:
        amount_value = float(amount)
    except (TypeError, ValueError):
        return jsonify({"error": "amount must be numeric"}), 400

    if amount_value <= 0:
        return jsonify({"error": "amount must be greater than zero"}), 400

    credentials = BankConfig(tenant_id=tenant_id).get_credentials()
    if not credentials.get("api_key") or not credentials.get("api_secret"):
        return jsonify({"error": "Bank credentials are not configured for this tenant"}), 503

    client = BankPaymentClient(tenant_id=tenant_id, credentials=credentials)
    try:
        result = client.request_payment(
            amount=amount_value,
            currency=str(currency).upper(),
            reference=str(reference),
            account_number=str(account_number),
            bank_name=str(bank_name),
            narration=str(narration),
        )
    except Exception as exc:  # pragma: no cover - network/credential path
        logger.exception("Bank payment request failed for tenant=%s", tenant_id)
        return jsonify({"error": "bank_payment_failed", "message": str(exc)}), 502

    return jsonify({
        "status": result.get("status") if isinstance(result, dict) else "processed",
        "tenant_id": tenant_id,
        "transaction_id": result.get("transactionId") if isinstance(result, dict) else None,
        "reference": str(reference),
        "amount": amount_value,
        "currency": str(currency).upper(),
        "payload": result,
    }), 200


@app.route("/admin/bank/payments/contracts", methods=["GET"])
def admin_bank_payment_contracts():
    """Return request/response examples for the bank transfer payout contract."""
    _require_admin()
    return jsonify({
        "payment_channel": "BANK",
        "provider": "KCB",
        "method": "POST",
        "endpoint": "/admin/bank/payments",
        "request_example": {
            "tenant_id": "tenant-bank",
            "amount": 400,
            "currency": "KES",
            "reference": "INV-BANK-400",
            "account_number": "1234567890",
            "bank_name": "KCB",
            "narration": "Invoice settlement",
        },
        "success_response_example": {
            "status": "processed",
            "tenant_id": "tenant-bank",
            "transaction_id": "BANK-123",
            "reference": "INV-BANK-400",
            "amount": 400,
            "currency": "KES",
            "payload": {"status": "processed", "transactionId": "BANK-123"},
        },
        "error_response_example": {
            "error": "bank_payment_failed",
            "message": "Bank credentials are not configured for this tenant",
        },
        "notes": [
            "The amount must be numeric and greater than zero.",
            "The bank route requires a tenant-configured API key and secret for the bank provider.",
            "The request is authenticated by the platform admin token before dispatch.",
        ],
    }), 200


@app.route("/admin/bank/ingest", methods=["POST"])
def admin_bank_statement_ingest():
    """Dispatch bank statement ingestion across API, CSV, Excel, PDF, SFTP, webhook, and scheduled sources."""
    _require_admin()
    payload = request.get_json(silent=True) or {}
    tenant_id = payload.get("tenant_id") or request.headers.get("X-Tenant-ID") or os.getenv("TENANT_ID", "default")
    service = BankService(tenant_id=tenant_id)
    source_type = str(payload.get("source_type") or payload.get("type") or "api").lower()

    try:
        if source_type in {"api", "bank_api", "bank-api"}:
            rows = payload.get("records") or []
            if not isinstance(rows, list):
                return jsonify({"error": "records must be a list"}), 400
            ingested = service.ingest_statement(rows)
        elif source_type in {"csv", "manual", "manual_upload", "uploaded_csv"}:
            csv_text = payload.get("csv_text") or payload.get("content") or ""
            if not csv_text:
                return jsonify({"error": "csv_text is required"}), 400
            ingested = service.ingest_manual_upload(csv_text, file_name=str(payload.get("file_name") or "statement.csv"), account_id=payload.get("account_id"))
        elif source_type in {"excel", "xlsx"}:
            excel_bytes = payload.get("excel_bytes") or payload.get("content") or b""
            if not excel_bytes:
                return jsonify({"error": "excel_bytes is required"}), 400
            if isinstance(excel_bytes, str):
                import base64
                try:
                    excel_bytes = base64.b64decode(excel_bytes)
                except Exception:
                    excel_bytes = excel_bytes.encode("utf-8")
            ingested = service.ingest_excel(excel_bytes, account_id=payload.get("account_id"), bank_name=payload.get("bank_name"))
        elif source_type == "pdf":
            pdf_text = payload.get("pdf_text") or payload.get("content") or ""
            if not pdf_text:
                return jsonify({"error": "pdf_text is required"}), 400
            ingested = service.ingest_pdf_statement(pdf_text, account_id=payload.get("account_id"), bank_name=payload.get("bank_name"))
        elif source_type == "sftp":
            host = payload.get("host")
            remote_path = payload.get("remote_path")
            if not host or not remote_path:
                return jsonify({"error": "host and remote_path are required for SFTP ingestion"}), 400
            ingested = service.ingest_sftp_statement(
                host=str(host),
                remote_path=str(remote_path),
                username=str(payload.get("username") or ""),
                password=str(payload.get("password") or ""),
            )
        elif source_type in {"webhook", "callback"}:
            if "payload" not in payload:
                return jsonify({"error": "payload is required for webhook ingestion"}), 400
            ingested = [service.ingest_webhook(payload["payload"])]
        elif source_type == "scheduled":
            schedule = payload.get("schedule") or {}
            if not isinstance(schedule, dict):
                return jsonify({"error": "schedule must be an object"}), 400
            scheduled = service.schedule_statement_retrieval(schedule)
            fetcher = payload.get("fetcher")
            if isinstance(fetcher, str):
                content = fetcher
            else:
                content = payload.get("content") or ""
            ingested = service.run_scheduled_statement_retrieval(scheduled, fetcher=(lambda content=content: content) if content else None)
        else:
            return jsonify({"error": f"unsupported_source_type:{source_type}"}), 400
    except Exception as exc:  # pragma: no cover - external-source paths
        logger.exception("Bank ingestion failed for tenant=%s, source=%s", tenant_id, source_type)
        return jsonify({"error": "bank_ingestion_failed", "message": str(exc)}), 502

    # Post-ingest: run reconciliation against the tenant's internal ledger
    try:
        connector_registry = ConnectorRegistry.from_env()
        connector = connector_registry.get_connector(tenant_id)
        ledger_records = connector.fetch_recent_records(since_minutes=int(os.getenv("RECONCILIATION_WINDOW_MINUTES", "15"))) if connector else []

        settlement_engine = SettlementEngine(tenant_id=tenant_id)
        recon = settlement_engine.reconcile_bank_and_ledger(ingested, ledger_records)

        # Optionally attempt automated settlements for unmatched ledger rows
        auto_settle = os.getenv("AUTO_SETTLE_ON_INGEST", "0") == "1"
        settle_summary = None
        if auto_settle and recon.get("unmatched_ledger_rows"):
            bank_cfg = BankConfig(tenant_id=tenant_id)
            creds = bank_cfg.get_credentials()
            if creds.get("api_key") and creds.get("api_secret"):
                client = BankPaymentClient(tenant_id=tenant_id, credentials=creds)
                settle_summary = settlement_engine.settle_unmatched_ledger(recon.get("unmatched_ledger_rows", []), bank_client=client, dry_run=os.getenv("AUTO_SETTLE_DRY_RUN", "1") != "0")
            else:
                settle_summary = {"attempted": 0, "reason": "bank_credentials_missing"}

    except Exception:
        logger.exception("Reconciliation/settlement post-ingest failed for tenant=%s", tenant_id)
        recon = {"status": "error", "reason": "recon_failed"}
        settle_summary = {"attempted": 0, "reason": "recon_failed"}

    return jsonify({
        "status": "ingested",
        "tenant_id": tenant_id,
        "source_type": source_type,
        "count": len(ingested),
        "records": ingested,
        "reconciliation": recon,
        "auto_settlement": settle_summary,
    }), 200


@app.route("/admin/bank/ingest/contracts", methods=["GET"])
def admin_bank_ingest_contracts():
    """Return dedicated request/response examples for each supported bank ingestion contract."""
    _require_admin()
    return jsonify({
        "source_types": {
            "csv": {
                "method": "POST",
                "endpoint": "/admin/bank/ingest",
                "example": {
                    "source_type": "csv",
                    "tenant_id": "tenant-bank",
                    "account_id": "acct-100",
                    "bank_name": "KCB",
                    "csv_text": "date,reference,accountId,amount,narration,status\n2026-09-06,CSV-100,acct-100,2500,Payroll deposit,POSTED\n",
                },
            },
            "excel": {
                "method": "POST",
                "endpoint": "/admin/bank/ingest",
                "example": {
                    "source_type": "excel",
                    "tenant_id": "tenant-bank",
                    "account_id": "acct-100",
                    "bank_name": "KCB",
                    "excel_bytes": "base64-encoded-xlsx-bytes",
                },
            },
            "sftp": {
                "method": "POST",
                "endpoint": "/admin/bank/ingest",
                "example": {
                    "source_type": "sftp",
                    "tenant_id": "tenant-bank",
                    "host": "sftp.bank.local",
                    "remote_path": "/incoming/statement.csv",
                    "username": "ops-user",
                    "password": "super-secret",
                },
            },
            "webhook": {
                "method": "POST",
                "endpoint": "/admin/bank/ingest",
                "example": {
                    "source_type": "webhook",
                    "tenant_id": "tenant-bank",
                    "payload": {
                        "accountId": "acct-100",
                        "reference": "WEB-200",
                        "amount": "-120",
                        "narration": "Webhook bank fee",
                        "status": "POSTED",
                        "bankName": "KCB",
                    },
                },
            },
            "api": {
                "method": "POST",
                "endpoint": "/admin/bank/ingest",
                "example": {
                    "source_type": "api",
                    "tenant_id": "tenant-bank",
                    "records": [
                        {
                            "accountId": "acct-100",
                            "reference": "API-300",
                            "amount": "4500",
                            "narration": "API settlement",
                            "status": "POSTED",
                        }
                    ],
                },
            },
        },
        "notes": [
            "CSV and Excel payloads are ingested into the bank ledger and normalized using the same reconciliation contract as API events.",
            "SFTP calls are treated as remote CSV imports and must provide host, remote_path, and optional credentials.",
            "Webhook imports accept a normalized bank event payload and are idempotent by reference.",
        ],
    }), 200


@app.route("/webhook/airtel/confirmation", methods=["POST"])
def airtel_confirmation():
    """Handle Airtel Money confirmation callbacks and accept them as a valid provider flow.

    Mirrors mpesa_confirmation() so both providers share one contract: validate ->
    dead-letter on rejection -> canonicalize -> idempotent ledger write -> publish
    downstream. The HTTP status/ResultCode returned here controls whether Airtel
    retries, so a genuine ERROR must return non-200.
    """
    tenant_id = os.getenv("TENANT_ID", "default")
    payload = request.get_json(silent=True)

    if not payload:
        logger.warning("Empty or invalid Airtel payload received")
        try:
            event_store.write_dead_letter(None, reason="invalid_json", error_detail="empty_or_invalid_json", tenant_id=tenant_id)
        except Exception:
            logger.debug("Failed to persist dead-letter for invalid Airtel JSON payload", exc_info=True)
        return jsonify({"ResultCode": 1, "ResultDesc": "Invalid payload"}), 400

    if not is_payload_within_limit(request):
        return jsonify({"ResultCode": 1, "ResultDesc": "Request body too large"}), 413

    is_valid, error = validate_airtel_payload(payload)
    if not is_valid:
        logger.warning("Airtel payload validation failed: %s", error)
        try:
            event_store.write_dead_letter(payload, reason="validation_failed", error_detail=str(error), tenant_id=tenant_id)
        except Exception:
            logger.debug("Failed to persist dead-letter for Airtel validation failure", exc_info=True)
        return jsonify({"ResultCode": 1, "ResultDesc": sanitize_error_message(error)}), 400

    # Single source of truth for provider normalization — keeps the Airtel event shape
    # identical to M-Pesa for the reconciliation engine and downstream Kafka consumers.
    canonical = extract_canonical_event(payload, tenant_id=tenant_id)
    if not canonical or not canonical.get("TransID"):
        logger.warning("Airtel payload could not be canonicalized")
        try:
            event_store.write_dead_letter(payload, reason="canonicalization_failed", error_detail="missing_transaction_id", tenant_id=tenant_id)
        except Exception:
            logger.debug("Failed to persist dead-letter for Airtel canonicalization failure", exc_info=True)
        return jsonify({"ResultCode": 1, "ResultDesc": "Invalid payload"}), 400

    trans_id = str(canonical["TransID"])
    source_ip = get_client_ip(request)

    # Fast-path optimization only — NOT the authoritative gate. The unique constraint
    # enforced inside mark_processed() below is what actually prevents double-processing.
    if event_store.already_processed(trans_id):
        logger.info("Duplicate Airtel transaction (pre-check)", extra={"tenant_id": tenant_id, "trans_id": trans_id, "source_ip": source_ip})
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted (duplicate ignored)"}), 200

    result = event_store.mark_processed(canonical, tenant_id=tenant_id, source_ip=source_ip, signature_verified=False)

    if result == ProcessResult.DUPLICATE:
        logger.info("Duplicate Airtel transaction (caught at write time)", extra={"tenant_id": tenant_id, "trans_id": trans_id})
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted (duplicate ignored)"}), 200

    if result == ProcessResult.ERROR:
        # Genuine failure — the transaction was NOT stored. Returning 200 would make
        # Airtel treat this as delivered and never retry, silently losing a real payment.
        logger.error("Failed to record Airtel transaction, requesting retry", extra={"tenant_id": tenant_id, "trans_id": trans_id})
        return jsonify({"ResultCode": 1, "ResultDesc": "Temporary processing error, please retry"}), 500

    # result == ProcessResult.STORED: genuinely new and safely persisted. Enqueue for
    # downstream reconciliation exactly once.
    start_ns = time.time_ns()

    try:
        import redis
        redis_conn = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), socket_connect_timeout=2)
        redis_conn.set(f"processed_trans_id:{trans_id}", "1", ex=86400)
    except Exception:
        pass  # best-effort cache warm; DB ledger above is the source of truth

    publish_status = "unknown"
    publish_error = None
    try:
        queued = enqueue_transaction_event(KAFKA_TOPIC, canonical)
        if queued.get("status") == "queued":
            publish_status = "queued"
            logger.info("Airtel transaction event queued to background job", extra={"trans_id": trans_id})
        else:
            publish_transaction_event(KAFKA_TOPIC, canonical)
            publish_status = "published"
            logger.info("Airtel transaction event published to Kafka (sync fallback)", extra={"trans_id": trans_id})
    except Exception as exc:  # noqa: BLE001
        # The transaction IS safely stored — only the downstream publish failed. Log for
        # manual replay; still ack 200 since reconciliation can be re-run from the ledger.
        publish_status = "publish_failed"
        publish_error = str(exc)
        logger.warning("Failed to publish Airtel event (queued for manual replay)", extra={"trans_id": trans_id}, exc_info=True)

    try:
        processing_time_ms = int((time.time_ns() - start_ns) / 1_000_000)
        event_store.update_processing_status(
            trans_id, status=publish_status, error_reason=publish_error, processing_time_ms=processing_time_ms
        )
    except Exception:
        logger.debug("Failed updating processing status for Airtel trans_id=%s", trans_id, exc_info=True)

    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200


if __name__ == "__main__":
    if os.getenv("PESAGUARD_LOAD_AUX_APPS", "1") == "1":
        for _module in ("app_1", "app_2", "app_4_advanced_features"):
            if f"pesaguard_backend_pipeline.{_module}" in sys.modules:
                continue
            try:
                __import__(f"pesaguard_backend_pipeline.{_module}")
            except Exception:
                logger.warning("Skipping optional module registration for %s", _module, exc_info=True)

    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
