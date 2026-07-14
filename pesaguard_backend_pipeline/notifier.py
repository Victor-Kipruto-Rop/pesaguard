"""
Dispatches alerts when a discrepancy is detected.
MVP: Slack webhook only. Add SMS (Africa's Talking) / email once needed.
"""
import json
import logging
import os
import urllib.request

from africas_talking import AfricasTalkingClient
import smtplib
from email.message import EmailMessage

from localization_utils import format_ke_currency, format_ke_datetime, normalise_locale

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pesaguard.alerting")

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SMS_RECIPIENT = os.getenv("SMS_ALERT_RECIPIENT", "")
EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM", "noreply@pesaguard.example")
SMTP_HOST = os.getenv("ALERT_SMTP_HOST")
SMTP_PORT = int(os.getenv("ALERT_SMTP_PORT", "25"))
SMTP_USER = os.getenv("ALERT_SMTP_USER")
SMTP_PASS = os.getenv("ALERT_SMTP_PASS")

sms_client = AfricasTalkingClient()


def send_slack_alert(discrepancy: dict, locale: str = "en") -> None:
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not set — skipping alert, logging instead")
        logger.warning("Discrepancy: %s", discrepancy)
        return

    text = _format_alert_text(discrepancy, locale=locale)
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


def send_sms_alert(discrepancy: dict, locale: str = "en") -> None:
    recipient = os.getenv('SMS_ALERT_RECIPIENT', '')
    if not recipient:
        return
    message = _format_alert_text(discrepancy, locale=locale)
    try:
        sms_client.send_sms(recipient, message)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to send SMS alert")


def send_email_alert(discrepancy: dict, locale: str = "en") -> None:
    recipients = os.getenv("ALERT_EMAIL_RECIPIENTS")
    if not recipients or not SMTP_HOST:
        return
    message_text = _format_alert_text(discrepancy, locale=locale)
    msg = EmailMessage()
    msg["Subject"] = f"PesaGuard Alert: {discrepancy.get('severity', 'alert') }"
    msg["From"] = EMAIL_FROM
    msg["To"] = recipients
    msg.set_content(message_text)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=5) as s:
            if SMTP_USER and SMTP_PASS:
                s.starttls()
                s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to send email alert")


def _format_alert_text(discrepancy: dict, locale: str = "en") -> str:
    trans_id = discrepancy.get("trans_id", discrepancy.get("TransID", "unknown"))
    anomalies = discrepancy.get("anomalies", [])
    severity = discrepancy.get("severity", "warning")
    status = discrepancy.get("status", "needs_review")
    locale_code = normalise_locale(locale)
    template = _get_template(locale_code)
    issues = ", ".join(anomalies) or template["no_issues"]
    detected_at = discrepancy.get("checked_at") or discrepancy.get("detected_at") or discrepancy.get("timestamp") or discrepancy.get("created_at") or "unknown"
    detected_at_display = format_ke_datetime(detected_at) or str(detected_at)
    amount = discrepancy.get("amount") or discrepancy.get("amount_value")
    amount_line = ""
    if amount is not None:
        amount_line = f"\n{template['amount']}: {format_ke_currency(amount)}"

    return (
        f":rotating_light: {template['title']}\n"
        f"{template['transaction']}: `{trans_id}`\n"
        f"{template['severity']}: `{severity}`\n"
        f"{template['status']}: `{status}`\n"
        f"{template['issues']}: {issues}\n"
        f"{template['detected_at']}: {detected_at_display}"
        f"{amount_line}"
    )


def _get_template(locale_code: str) -> dict[str, str]:
    """Return localized alert field labels. Reference copies: alerting/templates/sms_template_sw.md, slack_template_sw.md."""
    if locale_code == "sw":
        return {
            "title": "PesaGuard imegundua tofauti",
            "transaction": "Muamala",
            "severity": "Ukali",
            "status": "Hali",
            "issues": "Mambo yaliyotokea",
            "no_issues": "Hakuna maandishi ya ziada",
            "detected_at": "Iligunduliwa saa",
            "amount": "Kiasi",
        }
    return {
        "title": "PesaGuard discrepancy detected",
        "transaction": "Transaction",
        "severity": "Severity",
        "status": "Status",
        "issues": "Issues",
        "no_issues": "No additional details",
        "detected_at": "Detected at",
        "amount": "Amount",
    }
