"""
PesaGuard Webhook Receiver
Receives M-Pesa Daraja callbacks (C2B/B2C/STK Push confirmation),
validates payload, and pushes to Kafka for downstream reconciliation.
"""
import logging
import os

from flask import Flask, jsonify, request, Response
from werkzeug.exceptions import HTTPException

from security_helpers import (
    get_client_ip,
    is_allowed_source,
    is_payload_within_limit,
    sanitize_error_message,
)
from rate_limiter import RateLimiter

from event_store import EventStore, ProcessResult
from health import build_health_payload
from logging_utils import configure_logging, set_correlation_id, get_correlation_id
from validators import validate_daraja_payload
from background_tasks import enqueue_transaction_event
from producer import publish_transaction_event
from tenant_settings import TenantSettingsStore
from metrics import build_metrics_payload
from flask import abort

configure_logging()
logger = logging.getLogger("pesaguard.webhook")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("PESAGUARD_WEBHOOK_MAX_BODY_BYTES", "1048576"))
event_store = EventStore()
webhook_rate_limiter = RateLimiter()
webhook_rate_limiter.set_limits(int(os.getenv("PESAGUARD_WEBHOOK_RATE_LIMIT_PER_MINUTE", "30")))

KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_TRANSACTIONS", "mpesa.transactions.raw")

# Simple admin-auth for pilot Admin API endpoints
tenant_store = TenantSettingsStore()


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
    return jsonify({"ResultCode": 1, "ResultDesc": "Request body too large"}), 413


@app.errorhandler(400)
def handle_bad_request(_error):
    return jsonify({"ResultCode": 1, "ResultDesc": "Invalid request"}), 400


@app.errorhandler(Exception)
def handle_internal_error(error):
    if isinstance(error, HTTPException):
        return error

    logger.exception("Unhandled exception in webhook receiver", exc_info=error)
    return jsonify({"ResultCode": 1, "ResultDesc": "Internal server error"}), 500


@app.before_request
def setup_request_context():
    """Set up per-request context including correlation ID for tracing."""
    correlation_id = request.headers.get("X-Correlation-ID") or get_correlation_id()
    set_correlation_id(correlation_id)


@app.after_request
def add_correlation_id_header(response):
    """Add correlation ID to response headers for client tracing."""
    correlation_id = get_correlation_id()
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.before_request
def enforce_webhook_security():
    if request.method == "OPTIONS":
        return None

    if not is_payload_within_limit(request):
        return jsonify({"ResultCode": 1, "ResultDesc": "Request body too large"}), 413

    if request.path.startswith("/webhook"):
        if not is_allowed_source(get_client_ip(request), request):
            logger.warning("Webhook request rejected: forbidden source IP", extra={"source_ip": get_client_ip(request)})
            return jsonify({"ResultCode": 1, "ResultDesc": "Forbidden source"}), 403

        allowed, status = webhook_rate_limiter.is_allowed(
            get_client_ip(request),
            request.path,
        )
        if not allowed:
            logger.warning("Webhook request rejected: rate limit exceeded", extra={"source_ip": get_client_ip(request)})
            response = jsonify({"ResultCode": 1, "ResultDesc": "Rate limit exceeded"})
            response.status_code = 429
            response.headers["Retry-After"] = str(status.get("retry_after", 60))
            return response

        daraja_signature = request.headers.get("X-Daraja-Signature")
        if daraja_signature:
            try:
                _verify_daraja_signature(request.data, daraja_signature)
            except Exception as e:
                logger.warning("Webhook signature verification failed", extra={"error": str(e)})
                return jsonify({"ResultCode": 1, "ResultDesc": "Invalid signature"}), 403


@app.route("/metrics", methods=["GET"])
def metrics():
    return Response(build_metrics_payload(), mimetype="text/plain; version=0.0.4")


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
    status_code = 200 if payload.get("status") == "ok" else 503
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

    # Fast-path optimization only — NOT the authoritative gate. Two near-simultaneous
    # callbacks can both pass this check before either has written anything; the real
    # guarantee is the unique constraint enforced inside mark_processed() below.
    if event_store.already_processed(str(trans_id)):
        logger.info("Duplicate transaction (pre-check)", extra={"tenant_id": tenant_id, "trans_id": trans_id})
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted (duplicate ignored)"}), 200

    # Authoritative idempotency write. Branch on the ACTUAL result — never assume
    # success and never treat an error the same as a duplicate.
    result = event_store.mark_processed(payload, tenant_id=tenant_id)

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
    # enqueue for downstream reconciliation exactly once.
    try:
        import redis
        redis_conn = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), socket_connect_timeout=2)
        cache_key = f"processed_trans_id:{trans_id}"
        redis_conn.set(cache_key, "1", ex=86400)
    except Exception:
        pass  # best-effort cache warm; DB ledger above is the source of truth

    try:
        queued = enqueue_transaction_event(KAFKA_TOPIC, payload)
        if queued.get("status") == "queued":
            logger.info("Transaction event queued to background job", extra={"trans_id": trans_id})
        else:
            publish_transaction_event(KAFKA_TOPIC, payload)
            logger.info("Transaction event published to Kafka (sync fallback)", extra={"trans_id": trans_id})
    except Exception:  # noqa: BLE001
        # The transaction IS safely stored (STORED above) — only the downstream
        # publish failed. Log for manual replay; still ack 200 since the source
        # record exists and reconciliation can be re-run against it.
        logger.warning("Failed to publish event (queued for manual replay)", extra={"trans_id": trans_id}, exc_info=True)

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


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
