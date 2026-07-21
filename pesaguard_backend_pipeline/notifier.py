"""
Dispatches alerts when a discrepancy is detected.
MVP: Slack webhook only. Add SMS (Africa's Talking) / email once needed.

Retry Logic:
  - Email: up to 3 retries on transient errors (connection, timeout)
  - SMS: up to 2 retries on transient errors
  - Slack: up to 2 retries with exponential backoff
  
All failures logged with tenant_id, trans_id for troubleshooting.
"""
import json
import logging
import os
import time
import urllib.request
import smtplib
from email.message import EmailMessage
from typing import Optional, Dict, Any

from africas_talking import AfricasTalkingClient
from alert_template_loader import load_alert_fields, render_message_template
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

# Retry configuration
SLACK_RETRIES = int(os.getenv("ALERT_SLACK_RETRIES", "2"))
SMS_RETRIES = int(os.getenv("ALERT_SMS_RETRIES", "2"))
EMAIL_RETRIES = int(os.getenv("ALERT_EMAIL_RETRIES", "3"))
RETRY_BACKOFF_SECONDS = float(os.getenv("ALERT_RETRY_BACKOFF_SECONDS", "1.0"))

sms_client = AfricasTalkingClient()


def send_slack_alert(discrepancy: dict, locale: str = "en", max_retries: int = SLACK_RETRIES) -> bool:
    """Send alert to Slack with retries on transient failures.
    
    Args:
        discrepancy: Discrepancy alert dict
        locale: Message locale (en, sw, etc.)
        max_retries: Maximum number of retry attempts
        
    Returns:
        True if successfully sent, False if all retries exhausted
    """
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not configured; alert will only be logged")
        logger.warning("Discrepancy: %s", discrepancy)
        return False

    trans_id = discrepancy.get("trans_id", "unknown")
    tenant_id = discrepancy.get("tenant_id", "default")
    
    text = _format_slack_alert_text(discrepancy, locale=locale)
    body = json.dumps({"text": text}).encode("utf-8")
    
    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(
                SLACK_WEBHOOK_URL,
                data=body,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    logger.info(
                        "Slack alert sent successfully",
                        extra={"trans_id": trans_id, "tenant_id": tenant_id}
                    )
                    return True
                else:
                    logger.error(
                        f"Slack alert failed with status {resp.status}",
                        extra={"trans_id": trans_id, "tenant_id": tenant_id, "attempt": attempt + 1}
                    )
        except urllib.error.URLError as e:
            if attempt < max_retries:
                backoff = RETRY_BACKOFF_SECONDS * (2 ** attempt)
                logger.warning(
                    f"Slack alert failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}, retrying in {backoff:.1f}s",
                    extra={"trans_id": trans_id, "tenant_id": tenant_id}
                )
                time.sleep(backoff)
            else:
                logger.error(
                    f"Slack alert failed after {max_retries + 1} attempts: {str(e)}",
                    extra={"trans_id": trans_id, "tenant_id": tenant_id}
                )
                return False
        except Exception as e:
            logger.error(
                f"Unexpected error sending Slack alert: {str(e)}",
                extra={"trans_id": trans_id, "tenant_id": tenant_id},
                exc_info=True
            )
            return False
    
    return False


def send_sms_alert(discrepancy: dict, locale: str = "en", max_retries: int = SMS_RETRIES) -> bool:
    """Send alert via SMS with retries on transient failures.
    
    Args:
        discrepancy: Discrepancy alert dict
        locale: Message locale
        max_retries: Maximum retry attempts
        
    Returns:
        True if successfully sent
    """
    recipient = os.getenv('SMS_ALERT_RECIPIENT', '')
    trans_id = discrepancy.get("trans_id", "unknown")
    tenant_id = discrepancy.get("tenant_id", "default")
    
    if not recipient:
        logger.debug("SMS_ALERT_RECIPIENT not configured; SMS alert skipped")
        return False
    
    message = _format_sms_alert_text(discrepancy, locale=locale)
    
    for attempt in range(max_retries + 1):
        try:
            sms_client.send_sms(recipient, message)
            logger.info(
                "SMS alert sent successfully",
                extra={"trans_id": trans_id, "tenant_id": tenant_id, "recipient": recipient}
            )
            return True
        except Exception as e:
            if attempt < max_retries:
                backoff = RETRY_BACKOFF_SECONDS * (2 ** attempt)
                logger.warning(
                    f"SMS alert failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}, retrying in {backoff:.1f}s",
                    extra={"trans_id": trans_id, "tenant_id": tenant_id}
                )
                time.sleep(backoff)
            else:
                logger.error(
                    f"SMS alert failed after {max_retries + 1} attempts: {str(e)}",
                    extra={"trans_id": trans_id, "tenant_id": tenant_id}
                )
                return False
    
    return False


def send_email_alert(discrepancy: dict, locale: str = "en", max_retries: int = EMAIL_RETRIES) -> bool:
    """Send alert via email with retries on transient failures.
    
    Args:
        discrepancy: Discrepancy alert dict
        locale: Message locale
        max_retries: Maximum retry attempts
        
    Returns:
        True if successfully sent
    """
    recipients = os.getenv("ALERT_EMAIL_RECIPIENTS")
    trans_id = discrepancy.get("trans_id", "unknown")
    tenant_id = discrepancy.get("tenant_id", "default")
    
    if not recipients or not SMTP_HOST:
        logger.debug("Email configuration incomplete; email alert skipped")
        return False
    
    message_text = _format_alert_text(discrepancy, locale=locale)
    msg = EmailMessage()
    msg["Subject"] = f"PesaGuard Alert: {discrepancy.get('severity', 'alert').upper()} - {trans_id}"
    msg["From"] = EMAIL_FROM
    msg["To"] = recipients
    msg.set_content(message_text)

    for attempt in range(max_retries + 1):
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=5) as s:
                if SMTP_USER and SMTP_PASS:
                    s.starttls()
                    s.login(SMTP_USER, SMTP_PASS)
                s.send_message(msg)
            logger.info(
                "Email alert sent successfully",
                extra={"trans_id": trans_id, "tenant_id": tenant_id, "recipients": recipients}
            )
            return True
        except smtplib.SMTPException as e:
            if attempt < max_retries:
                backoff = RETRY_BACKOFF_SECONDS * (2 ** attempt)
                logger.warning(
                    f"Email alert failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}, retrying in {backoff:.1f}s",
                    extra={"trans_id": trans_id, "tenant_id": tenant_id}
                )
                time.sleep(backoff)
            else:
                logger.error(
                    f"Email alert failed after {max_retries + 1} attempts: {str(e)}",
                    extra={"trans_id": trans_id, "tenant_id": tenant_id}
                )
                return False
        except Exception as e:
            logger.error(
                f"Unexpected error sending email alert: {str(e)}",
                extra={"trans_id": trans_id, "tenant_id": tenant_id},
                exc_info=True
            )
            return False
    
    return False


def _template_context(discrepancy: dict) -> dict:
    anomalies = discrepancy.get("anomalies", [])
    amount = discrepancy.get("amount") or discrepancy.get("amount_value")
    return {
        "tenant_name": discrepancy.get("tenant_name") or discrepancy.get("tenant_id") or "default",
        "anomaly_type": ", ".join(anomalies) or discrepancy.get("anomaly_type") or "discrepancy",
        "amount": format_ke_currency(amount) if amount is not None else "N/A",
        "summary": ", ".join(anomalies) or discrepancy.get("status") or "needs_review",
        "trans_id": discrepancy.get("trans_id", discrepancy.get("TransID", "unknown")),
        "severity": discrepancy.get("severity", "warning"),
        "status": discrepancy.get("status", "needs_review"),
    }


def _format_sms_alert_text(discrepancy: dict, locale: str = "en") -> str:
    locale_code = normalise_locale(locale)
    template_name = f"sms_template_{locale_code}.md"
    rendered = render_message_template(template_name, _template_context(discrepancy))
    if rendered:
        return rendered
    return _format_alert_text(discrepancy, locale=locale)


def _format_slack_alert_text(discrepancy: dict, locale: str = "en") -> str:
    locale_code = normalise_locale(locale)
    template_name = f"slack_template_{locale_code}.md"
    rendered = render_message_template(template_name, _template_context(discrepancy))
    if rendered:
        return rendered
    return _format_alert_text(discrepancy, locale=locale)


def _format_alert_text(discrepancy: dict, locale: str = "en") -> str:
    trans_id = discrepancy.get("trans_id", discrepancy.get("TransID", "unknown"))
    anomalies = discrepancy.get("anomalies", [])
    severity = discrepancy.get("severity", "warning")
    status = discrepancy.get("status", "needs_review")
    locale_code = normalise_locale(locale)
    template = load_alert_fields(locale_code)
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
