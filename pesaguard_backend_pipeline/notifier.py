"""
Dispatches alerts when a discrepancy is detected.
MVP: Slack webhook only. Add SMS (Africa's Talking) / email once needed.
"""
import json
import logging
import os
import urllib.request

from africas_talking import AfricasTalkingClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pesaguard.alerting")

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SMS_RECIPIENT = os.getenv("SMS_ALERT_RECIPIENT", "")

sms_client = AfricasTalkingClient()


def send_slack_alert(discrepancy: dict) -> None:
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not set — skipping alert, logging instead")
        logger.warning("Discrepancy: %s", discrepancy)
        return

    text = _format_alert_text(discrepancy)
    body = json.dumps({"text": text}).encode("utf-8")

    req = urllib.request.Request(
        SLACK_WEBHOOK_URL,
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status != 200:
                logger.error("Slack alert failed with status %s", resp.status)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to send Slack alert")


def send_sms_alert(discrepancy: dict) -> None:
    if not SMS_RECIPIENT:
        return
    message = _format_alert_text(discrepancy)
    sms_client.send_sms(SMS_RECIPIENT, message)


def _format_alert_text(discrepancy: dict) -> str:
    trans_id = discrepancy.get("trans_id", discrepancy.get("TransID", "unknown"))
    anomalies = discrepancy.get("anomalies", [])
    severity = discrepancy.get("severity", "warning")
    status = discrepancy.get("status", "needs_review")
    return (
        f":rotating_light: *PesaGuard Discrepancy Detected*\n"
        f"*Transaction:* `{trans_id}`\n"
        f"*Severity:* `{severity}`\n"
        f"*Status:* `{status}`\n"
        f"*Issues:* {', '.join(anomalies)}\n"
        f"*Detected at:* {discrepancy.get('checked_at', 'unknown')}"
    )
