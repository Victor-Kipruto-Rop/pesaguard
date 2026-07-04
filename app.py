"""
PesaGuard Webhook Receiver
Receives M-Pesa Daraja callbacks (C2B/B2C/STK Push confirmation),
validates payload, and pushes to Kafka for downstream reconciliation.
"""
import logging
import os

from flask import Flask, jsonify, request

from event_store import EventStore
from health import build_health_payload
from logging_utils import configure_logging
from validators import validate_daraja_payload
from producer import publish_transaction_event

configure_logging()
logger = logging.getLogger("pesaguard.webhook")

app = Flask(__name__)
event_store = EventStore()

KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_TRANSACTIONS", "mpesa.transactions.raw")


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

    is_valid, error = validate_daraja_payload(payload)
    if not is_valid:
        logger.warning("Payload validation failed: %s", error)
        return jsonify({"ResultCode": 1, "ResultDesc": error}), 400

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
