"""Email service for sending notifications and reconciliation reports."""

import smtplib
import logging
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from localization_utils import format_ke_currency, format_ke_datetime, normalise_locale
from models import EmailNotification

logger = logging.getLogger("pesaguard.email")


class EmailService:
    """Handles email sending for notifications and reports."""

    def __init__(
        self,
        smtp_server: str = "localhost",
        smtp_port: int = 587,
        from_email: str = "noreply@pesaguard.local",
        from_name: str = "PesaGuard",
        username: str = None,
        password: str = None,
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.from_email = from_email
        self.from_name = from_name
        self.username = username
        self.password = password

    def send_reconciliation_report(
        self,
        session: Session,
        tenant_id: str,
        recipient_email: str,
        report_data: Dict[str, Any],
        locale: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send reconciliation report via email."""
        locale_code = normalise_locale(locale)
        if locale_code == "sw":
            subject = f"Ripoti ya upatanishi ya PesaGuard - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        else:
            subject = f"PesaGuard Reconciliation Report - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        
        html_content = self._build_reconciliation_html(report_data, locale=locale)
        
        email_record = EmailNotification(
            id=f"email_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            recipient_email=recipient_email,
            report_type="reconciliation",
            subject=subject,
            status="pending",
        )
        
        success = self._send_email(
            recipient_email,
            subject,
            html_content,
        )
        
        if success:
            email_record.status = "sent"
            email_record.sent_at = datetime.now(timezone.utc)
            logger.info(f"Sent reconciliation report to {recipient_email}")
        else:
            email_record.status = "failed"
            email_record.error_message = "SMTP delivery failed"
            logger.error(f"Failed to send reconciliation report to {recipient_email}")
        
        session.add(email_record)
        session.commit()
        
        return {
            "id": email_record.id,
            "status": email_record.status,
            "recipient": recipient_email,
            "report_type": "reconciliation",
            "sent_at": email_record.sent_at.isoformat() if email_record.sent_at else None,
        }

    def send_escalation_notification(
        self,
        session: Session,
        tenant_id: str,
        recipient_email: str,
        incident_data: Dict[str, Any],
        locale: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send escalation notification email."""
        locale_code = normalise_locale(locale)
        if locale_code == "sw":
            subject = f"PesaGuard Alert: Kipindi kilichopandishwa - {incident_data.get('anomaly_type', 'Unknown')}"
        else:
            subject = f"PesaGuard Alert: Incident Escalated - {incident_data.get('anomaly_type', 'Unknown')}"
        
        html_content = self._build_escalation_html(incident_data, locale=locale)
        
        email_record = EmailNotification(
            id=f"email_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            recipient_email=recipient_email,
            report_type="escalation",
            subject=subject,
            status="pending",
        )
        
        success = self._send_email(
            recipient_email,
            subject,
            html_content,
        )
        
        if success:
            email_record.status = "sent"
            email_record.sent_at = datetime.now(timezone.utc)
            logger.info(f"Sent escalation notification to {recipient_email}")
        else:
            email_record.status = "failed"
            email_record.error_message = "SMTP delivery failed"
        
        session.add(email_record)
        session.commit()
        
        return {
            "id": email_record.id,
            "status": email_record.status,
            "recipient": recipient_email,
        }

    def send_daily_summary(
        self,
        session: Session,
        tenant_id: str,
        recipient_email: str,
        summary_data: Dict[str, Any],
        locale: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send daily summary email."""
        locale_code = normalise_locale(locale)
        if locale_code == "sw":
            subject = f"Muhtasari wa kila siku wa PesaGuard - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        else:
            subject = f"PesaGuard Daily Summary - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        
        html_content = self._build_summary_html(summary_data, locale=locale)
        
        email_record = EmailNotification(
            id=f"email_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            recipient_email=recipient_email,
            report_type="daily_summary",
            subject=subject,
            status="pending",
        )
        
        success = self._send_email(
            recipient_email,
            subject,
            html_content,
        )
        
        if success:
            email_record.status = "sent"
            email_record.sent_at = datetime.now(timezone.utc)
        else:
            email_record.status = "failed"
        
        session.add(email_record)
        session.commit()
        
        return {
            "id": email_record.id,
            "status": email_record.status,
            "recipient": recipient_email,
        }

    def _send_email(
        self,
        recipient_email: str,
        subject: str,
        html_content: str,
    ) -> bool:
        """Send email via SMTP."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = recipient_email
            
            msg.attach(MIMEText(html_content, "html"))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            logger.error(f"SMTP error sending to {recipient_email}: {e}")
            return False

    def _build_reconciliation_html(self, data: Dict[str, Any], locale: Optional[str] = None) -> str:
        """Build HTML for reconciliation report."""
        locale_code = normalise_locale(locale)
        if locale_code == "sw":
            title = "Ripoti ya upatanishi"
            total_label = "Idadi ya tofauti"
            resolved_label = "Zilizotatuliwa"
            pending_label = "Zinazosubiri"
            sla_label = "Utekelezaji wa SLA"
            avg_label = "Wakati wa wastani wa utatuzi"
            generated_label = "Ilichapishwa na PesaGuard"
        else:
            title = "Reconciliation Report"
            total_label = "Total Discrepancies"
            resolved_label = "Resolved"
            pending_label = "Pending"
            sla_label = "SLA Compliance"
            avg_label = "Avg Resolution Time"
            generated_label = "Generated by PesaGuard"
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>{title}</h2>
                <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                    <tr style="background: #f0f0f0;">
                        <td style="padding: 10px; border: 1px solid #ddd;">{total_label}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{data.get('total_discrepancies', 0)}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">{resolved_label}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{data.get('resolved', 0)}</td>
                    </tr>
                    <tr style="background: #f0f0f0;">
                        <td style="padding: 10px; border: 1px solid #ddd;">{pending_label}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{data.get('pending', 0)}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">{sla_label}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{data.get('sla_compliance', 'N/A')}%</td>
                    </tr>
                    <tr style="background: #f0f0f0;">
                        <td style="padding: 10px; border: 1px solid #ddd;">{avg_label}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{data.get('avg_resolution_time', 'N/A')} minutes</td>
                    </tr>
                </table>
                <p style="margin-top: 30px; color: #666; font-size: 12px;">
                    {generated_label} • {datetime.now(timezone.utc).isoformat()}
                </p>
            </body>
        </html>
        """

    def _build_escalation_html(self, incident_data: Dict[str, Any], locale: Optional[str] = None) -> str:
        """Build HTML for escalation notification."""
        locale_code = normalise_locale(locale)
        if locale_code == "sw":
            title = "Kipindi kilichopandishwa"
            anomaly_label = "Aina ya usumbufu"
            severity_label = "Ukali"
            amount_label = "Kiasi"
            trans_label = "Kitambulisho cha muamala"
            detected_label = "Iligunduliwa saa"
            action_text = "Msaada wa utendaji"
        else:
            title = "Incident Escalated"
            anomaly_label = "Anomaly Type"
            severity_label = "Severity"
            amount_label = "Amount"
            trans_label = "Transaction ID"
            detected_label = "Detected At"
            action_text = "Please review and take appropriate action."

        amount_value = incident_data.get("amount", "N/A")
        try:
            amount_value = format_ke_currency(amount_value)
        except Exception:
            amount_value = incident_data.get("amount", "N/A")

        detected_value = incident_data.get("detected_at", "N/A")
        if detected_value != "N/A":
            detected_value = format_ke_datetime(detected_value)

        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2 style="color: #d32f2f;">{title}</h2>
                <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                    <p><strong>{anomaly_label}:</strong> {incident_data.get('anomaly_type', 'Unknown')}</p>
                    <p><strong>{severity_label}:</strong> {str(incident_data.get('severity', 'Unknown')).upper()}</p>
                    <p><strong>{amount_label}:</strong> {amount_value}</p>
                    <p><strong>{trans_label}:</strong> {incident_data.get('trans_id', 'N/A')}</p>
                    <p><strong>{detected_label}:</strong> {detected_value}</p>
                </div>
                <p>{action_text}</p>
            </body>
        </html>
        """

    def _build_summary_html(self, summary_data: Dict[str, Any], locale: Optional[str] = None) -> str:
        """Build HTML for daily summary."""
        locale_code = normalise_locale(locale)
        if locale_code == "sw":
            title = "Muhtasari wa kila siku"
            total_label = "Matukio yote"
            resolved_label = "Zilizotatuliwa leo"
            pending_label = "Zinazosubiri"
        else:
            title = "Daily Summary"
            total_label = "Total Incidents"
            resolved_label = "Resolved Today"
            pending_label = "Pending"
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>{title}</h2>
                <p>{total_label}: <strong>{summary_data.get('total_incidents', 0)}</strong></p>
                <p>{resolved_label}: <strong>{summary_data.get('resolved_today', 0)}</strong></p>
                <p>{pending_label}: <strong>{summary_data.get('pending', 0)}</strong></p>
            </body>
        </html>
        """

    def get_email_history(
        self,
        session: Session,
        tenant_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get email notification history for a tenant."""
        emails = (
            session.query(EmailNotification)
            .filter(EmailNotification.tenant_id == tenant_id)
            .order_by(EmailNotification.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": e.id,
                "recipient": e.recipient_email,
                "report_type": e.report_type,
                "status": e.status,
                "created_at": e.created_at.isoformat(),
                "sent_at": e.sent_at.isoformat() if e.sent_at else None,
            }
            for e in emails
        ]
