"""Email service for sending notifications and reconciliation reports."""

import smtplib
import logging
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
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
    ) -> Dict[str, Any]:
        """Send reconciliation report via email."""
        subject = f"PesaGuard Reconciliation Report - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        
        html_content = self._build_reconciliation_html(report_data)
        
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
    ) -> Dict[str, Any]:
        """Send escalation notification email."""
        subject = f"PesaGuard Alert: Incident Escalated - {incident_data.get('anomaly_type', 'Unknown')}"
        
        html_content = self._build_escalation_html(incident_data)
        
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
    ) -> Dict[str, Any]:
        """Send daily summary email."""
        subject = f"PesaGuard Daily Summary - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        
        html_content = self._build_summary_html(summary_data)
        
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

    def _build_reconciliation_html(self, data: Dict[str, Any]) -> str:
        """Build HTML for reconciliation report."""
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Reconciliation Report</h2>
                <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                    <tr style="background: #f0f0f0;">
                        <td style="padding: 10px; border: 1px solid #ddd;">Total Discrepancies</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{data.get('total_discrepancies', 0)}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">Resolved</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{data.get('resolved', 0)}</td>
                    </tr>
                    <tr style="background: #f0f0f0;">
                        <td style="padding: 10px; border: 1px solid #ddd;">Pending</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{data.get('pending', 0)}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">SLA Compliance</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{data.get('sla_compliance', 'N/A')}%</td>
                    </tr>
                    <tr style="background: #f0f0f0;">
                        <td style="padding: 10px; border: 1px solid #ddd;">Avg Resolution Time</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{data.get('avg_resolution_time', 'N/A')} minutes</td>
                    </tr>
                </table>
                <p style="margin-top: 30px; color: #666; font-size: 12px;">
                    Generated by PesaGuard • {datetime.now(timezone.utc).isoformat()}
                </p>
            </body>
        </html>
        """

    def _build_escalation_html(self, incident_data: Dict[str, Any]) -> str:
        """Build HTML for escalation notification."""
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2 style="color: #d32f2f;">Incident Escalated</h2>
                <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                    <p><strong>Anomaly Type:</strong> {incident_data.get('anomaly_type', 'Unknown')}</p>
                    <p><strong>Severity:</strong> {incident_data.get('severity', 'Unknown').upper()}</p>
                    <p><strong>Amount:</strong> {incident_data.get('amount', 'N/A')}</p>
                    <p><strong>Transaction ID:</strong> {incident_data.get('trans_id', 'N/A')}</p>
                    <p><strong>Detected At:</strong> {incident_data.get('detected_at', 'N/A')}</p>
                </div>
                <p>Please review and take appropriate action.</p>
            </body>
        </html>
        """

    def _build_summary_html(self, summary_data: Dict[str, Any]) -> str:
        """Build HTML for daily summary."""
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Daily Summary</h2>
                <p>Total Incidents: <strong>{summary_data.get('total_incidents', 0)}</strong></p>
                <p>Resolved Today: <strong>{summary_data.get('resolved_today', 0)}</strong></p>
                <p>Pending: <strong>{summary_data.get('pending', 0)}</strong></p>
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
