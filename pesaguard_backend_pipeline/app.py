"""
PesaGuard Webhook Receiver
Receives M-Pesa Daraja callbacks (C2B/B2C/STK Push confirmation),
validates payload, and pushes to Kafka for downstream reconciliation.
"""
import logging
import os

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from security_helpers import (
    get_client_ip,
    is_allowed_source,
    is_payload_within_limit,
    sanitize_error_message,
)
from rate_limiter import RateLimiter

from event_store import EventStore
from health import build_health_payload
from logging_utils import configure_logging
from validators import validate_daraja_payload
from producer import publish_transaction_event
from tenant_settings import TenantSettingsStore
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
    # Only expose non-sensitive, UX preferences
    public = {
        "tenant_id": tenant_id,
        "preferred_locale": settings.get("preferred_locale"),
        "deployment_region": settings.get("deployment_region"),
    }
    return jsonify(public), 200


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
def enforce_webhook_security():
    if request.method == "OPTIONS":
        return None

    if not is_payload_within_limit(request):
        return jsonify({"ResultCode": 1, "ResultDesc": "Request body too large"}), 413

    if request.path.startswith("/webhook"):
        if not is_allowed_source(get_client_ip(request), request):
            return jsonify({"ResultCode": 1, "ResultDesc": "Forbidden source"}), 403

        allowed, status = webhook_rate_limiter.is_allowed(
            get_client_ip(request),
            request.path,
        )
        if not allowed:
            response = jsonify({"ResultCode": 1, "ResultDesc": "Rate limit exceeded"})
            response.status_code = 429
            response.headers["Retry-After"] = str(status.get("retry_after", 60))
            return response


@app.route("/health", methods=["GET"])
def health():
    return jsonify(build_health_payload()), 200


@app.route("/webhook/mpesa/confirmation", methods=["POST"])
def mpesa_confirmation():
    """
    Handles C2B confirmation callbacks from Daraja.
    Docs: https://developer.safaricom.co.ke/
    """
    payload = request.get_json(silent=True)

    if not payload:
        logger.warning("Empty or invalid JSON payload received")
        return jsonify({"ResultCode": 1, "ResultDesc": "Invalid payload"}), 400

    if not is_payload_within_limit(request):
        return jsonify({"ResultCode": 1, "ResultDesc": "Request body too large"}), 413

    is_valid, error = validate_daraja_payload(payload)
    if not is_valid:
        logger.warning("Payload validation failed: %s", error)
        return jsonify({"ResultCode": 1, "ResultDesc": sanitize_error_message(error)}), 400

    trans_id = payload.get("TransID")
    if event_store.already_processed(str(trans_id)):
        logger.info("Duplicate transaction already stored", extra={"tenant_id": os.getenv("TENANT_ID", "default"), "trans_id": trans_id})
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted (duplicate ignored)"}), 200

    try:
        event_store.mark_processed(payload)
        publish_transaction_event(KAFKA_TOPIC, payload)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to publish event to Kafka", extra={"tenant_id": os.getenv("TENANT_ID", "default"), "trans_id": trans_id})
        # Still return 200 to M-Pesa to prevent retries storming us;
        # log for manual replay instead.
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted (queued for retry)"}), 200

    logger.info(
        "Transaction event published: %s",
        payload.get("TransID", "unknown"),
    )
    # Daraja expects this exact ack shape
    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200


@app.route("/webhook/mpesa/validation", methods=["POST"])
def mpesa_validation():
    """
    Handles C2B validation callbacks (pre-confirmation).
    Return here to accept/reject a transaction before it completes.
    """
    payload = request.get_json(silent=True) or {}
    logger.info("Validation request for: %s", payload.get("TransID", "unknown"))
    # Default: accept all. Add business rules here if needed
    # (e.g. reject if account number format is wrong).
    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
