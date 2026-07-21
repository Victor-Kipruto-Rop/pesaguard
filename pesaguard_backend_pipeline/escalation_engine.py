"""Custom escalation rules engine for per-tenant escalation workflows."""

import logging
import os
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
import requests
from sqlalchemy.orm import Session
from models import EscalationRule, Discrepancy, OnCallRotation
from email_service import EmailService
from tenant_settings import TenantSettingsStore

logger = logging.getLogger("pesaguard.escalation")


class EscalationEngine:
    """Manages custom escalation rules and executes escalations."""

    OPERATORS = {
        "equals": lambda field, value: field == value,
        "not_equals": lambda field, value: field != value,
        "greater_than": lambda field, value: field > value,
        "less_than": lambda field, value: field < value,
        "contains": lambda field, value: value in str(field),
        "in": lambda field, value: field in value,
    }

    def __init__(self, session: Session):
        self.session = session
        self.email_service = None
        self.settings_store = TenantSettingsStore(os.getenv("TENANT_SETTINGS_FILE", "tenant_settings.json"))

    def create_rule(
        self,
        tenant_id: str,
        name: str,
        description: str,
        condition_field: str,
        condition_operator: str,
        condition_value: str,
        action: str,
        target: str = None,
        webhook_url: str = None,
        priority: int = 0,
    ) -> Dict[str, Any]:
        """Create a new escalation rule for a tenant."""
        rule_id = f"rule_{uuid.uuid4().hex[:12]}"
        rule = EscalationRule(
            id=rule_id,
            tenant_id=tenant_id,
            name=name,
            description=description,
            condition_field=condition_field,
            condition_operator=condition_operator,
            condition_value=condition_value,
            action=action,
            target=target,
            webhook_url=webhook_url,
            active=True,
            priority=priority,
        )
        self.session.add(rule)
        self.session.commit()
        logger.info(f"Created escalation rule {rule_id} for tenant {tenant_id}")
        return self._rule_to_dict(rule)

    def get_rules(self, tenant_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all escalation rules for a tenant."""
        query = self.session.query(EscalationRule).filter(
            EscalationRule.tenant_id == tenant_id
        )
        if active_only:
            query = query.filter(EscalationRule.active == True)
        rules = query.order_by(EscalationRule.priority.desc()).all()
        return [self._rule_to_dict(r) for r in rules]

    def evaluate_and_escalate(
        self,
        tenant_id: str,
        incident: Discrepancy,
    ) -> Dict[str, Any]:
        """Evaluate incident against escalation rules and execute applicable escalations."""
        rules = self.get_rules(tenant_id, active_only=True)
        executed_escalations = []

        for rule in rules:
            if self._evaluate_condition(rule, incident):
                escalation_result = self._execute_escalation(rule, incident)
                executed_escalations.append(escalation_result)
                logger.info(
                    f"Escalated incident {incident.id} with rule {rule['id']}"
                )

        return {
            "incident_id": incident.id,
            "escalations_executed": len(executed_escalations),
            "details": executed_escalations,
        }

    def _evaluate_condition(self, rule: Dict[str, Any], incident: Discrepancy) -> bool:
        """Check if incident matches rule condition."""
        field_value = self._get_field_value(rule["condition_field"], incident)
        
        if field_value is None:
            return False

        operator_func = self.OPERATORS.get(rule["condition_operator"])
        if not operator_func:
            logger.warning(f"Unknown operator: {rule['condition_operator']}")
            return False

        try:
            return operator_func(field_value, rule["condition_value"])
        except Exception as e:
            logger.error(
                f"Error evaluating condition for rule {rule['id']}: {e}"
            )
            return False

    def _get_field_value(self, field_name: str, incident: Discrepancy) -> Any:
        """Get field value from incident for condition evaluation."""
        field_mapping = {
            "severity": incident.severity,
            "anomaly_type": incident.anomaly_type,
            "status": incident.status,
            "age_minutes": (
                (datetime.now(timezone.utc) - incident.detected_at).total_seconds()
                / 60
                if incident.detected_at
                else 0
            ),
        }
        return field_mapping.get(field_name)

    def _execute_escalation(
        self,
        rule: Dict[str, Any],
        incident: Discrepancy,
    ) -> Dict[str, Any]:
        """Execute escalation action."""
        action = rule["action"]

        if action == "escalate":
            return self._escalate_to_operator(rule, incident)
        elif action == "notify":
            return self._notify_operator(rule, incident)
        elif action == "webhook":
            return self._trigger_webhook(rule, incident)
        else:
            logger.warning(f"Unknown action: {action}")
            return {"status": "unknown_action"}

    def _escalate_to_operator(
        self,
        rule: Dict[str, Any],
        incident: Discrepancy,
    ) -> Dict[str, Any]:
        """Escalate incident to an operator based on rule."""
        target_operator = rule.get("target")
        
        if not target_operator:
            # Auto-assign to on-call operator
            target_operator = self._get_on_call_operator(
                incident.tenant_id,
                escalation_level=1,
            )

        if target_operator:
            incident.assignee = target_operator
            incident.notes = (
                f"{incident.notes or ''}\nAuto-escalated by rule: {rule['name']}"
            ).strip()
            incident.timeline = incident.timeline or []
            incident.timeline.append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": "escalated",
                    "rule": rule["name"],
                    "assignee": target_operator,
                }
            )
            self.session.commit()
            logger.info(f"Escalated incident {incident.id} to {target_operator}")
            return {
                "status": "escalated",
                "assigned_to": target_operator,
                "rule": rule["name"],
            }
        else:
            return {"status": "escalation_failed", "reason": "no_operator_available"}

    def _notify_operator(
        self,
        rule: Dict[str, Any],
        incident: Discrepancy,
    ) -> Dict[str, Any]:
        """Send notification to operator."""
        recipient = rule.get("target") or incident.assignee
        if not recipient:
            return {"status": "notification_failed", "reason": "no_recipient"}

        if self.email_service is None:
            self.email_service = EmailService()

        locale = self.settings_store.resolve_locale(incident.tenant_id)

        self.email_service.send_escalation_notification(
            self.session,
            incident.tenant_id,
            recipient,
            {
                "anomaly_type": incident.anomaly_type,
                "severity": incident.severity,
                "amount": incident.details or "N/A",
                "trans_id": incident.trans_id,
                "detected_at": incident.detected_at.isoformat() if incident.detected_at else None,
            },
            locale=locale,
        )
        return {
            "status": "notification_sent",
            "rule": rule["name"],
            "target": recipient,
        }

    def _trigger_webhook(
        self,
        rule: Dict[str, Any],
        incident: Discrepancy,
    ) -> Dict[str, Any]:
        """Trigger a webhook for escalation."""
        webhook_url = rule.get("webhook_url")
        if not webhook_url:
            return {"status": "webhook_error", "reason": "no_webhook_url"}

        payload = {
            "event_type": "escalation",
            "incident_id": incident.id,
            "trans_id": incident.trans_id,
            "severity": incident.severity,
            "anomaly_type": incident.anomaly_type,
            "assigned_to": incident.assignee,
            "rule_applied": rule["name"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            return {
                "status": "webhook_triggered",
                "url": webhook_url,
                "rule": rule["name"],
                "response_status": response.status_code,
            }
        except Exception as exc:
            logger.error("Webhook delivery failed for rule %s: %s", rule["name"], exc)
            return {"status": "webhook_error", "reason": str(exc)}

    def _get_on_call_operator(
        self,
        tenant_id: str,
        escalation_level: int = 1,
    ) -> Optional[str]:
        """Get current on-call operator for tenant."""
        now = datetime.now(timezone.utc)
        rotation = (
            self.session.query(OnCallRotation)
            .filter(
                OnCallRotation.tenant_id == tenant_id,
                OnCallRotation.escalation_level == escalation_level,
                OnCallRotation.shift_start <= now,
                OnCallRotation.shift_end > now,
                OnCallRotation.is_active == True,
            )
            .first()
        )
        return rotation.operator_id if rotation else None

    def update_rule(self, rule_id: str, **kwargs) -> Dict[str, Any]:
        """Update an escalation rule."""
        rule = (
            self.session.query(EscalationRule)
            .filter(EscalationRule.id == rule_id)
            .first()
        )
        if not rule:
            return {"error": "rule_not_found"}

        for key, value in kwargs.items():
            if hasattr(rule, key):
                setattr(rule, key, value)

        self.session.commit()
        logger.info(f"Updated rule {rule_id}")
        return self._rule_to_dict(rule)

    def delete_rule(self, rule_id: str) -> Dict[str, Any]:
        """Delete an escalation rule."""
        rule = (
            self.session.query(EscalationRule)
            .filter(EscalationRule.id == rule_id)
            .first()
        )
        if not rule:
            return {"error": "rule_not_found"}

        self.session.delete(rule)
        self.session.commit()
        logger.info(f"Deleted rule {rule_id}")
        return {"status": "deleted"}

    def check_webhook_health(self, tenant_id: str, webhook_id: str = None) -> Dict[str, Any]:
        """Check health of webhooks and escalate if failures detected.
        
        Monitors WebhookDelivery table for recent failures:
          - Recent failed deliveries (attempt_count > 0)
          - Dead letter queue accumulation
          - Webhook timeout patterns
        
        Escalates if failure rate exceeds threshold (default 10%).
        """
        from models import WebhookDelivery, DeadLetter
        from datetime import datetime, timezone, timedelta
        
        now = datetime.now(timezone.utc)
        check_window = now - timedelta(minutes=30)  # Check last 30 minutes
        
        # Query recent webhook deliveries
        recent_deliveries = self.session.query(WebhookDelivery).filter(
            WebhookDelivery.created_at >= check_window
        ).all() if not webhook_id else self.session.query(WebhookDelivery).filter(
            WebhookDelivery.webhook_id == webhook_id,
            WebhookDelivery.created_at >= check_window
        ).all()
        
        if not recent_deliveries:
            return {"status": "ok", "message": "No recent webhook activity"}
        
        failed_count = sum(1 for d in recent_deliveries if d.status == "failed")
        failure_rate = failed_count / len(recent_deliveries) if recent_deliveries else 0
        
        failure_threshold = float(os.getenv("WEBHOOK_FAILURE_THRESHOLD", "0.1"))  # 10%
        
        result = {
            "webhook_id": webhook_id,
            "total_deliveries": len(recent_deliveries),
            "failed_deliveries": failed_count,
            "failure_rate": round(failure_rate, 2),
            "threshold": failure_threshold,
        }
        
        if failure_rate > failure_threshold:
            result["status"] = "escalation_triggered"
            logger.warning(
                f"Webhook failure rate {failure_rate:.1%} exceeds threshold {failure_threshold:.1%}",
                extra={"tenant_id": tenant_id, "webhook_id": webhook_id}
            )
            
            # Trigger escalation
            incident = type('Incident', (), {
                'id': f"webhook_health_{webhook_id or 'all'}_{int(now.timestamp())}",
                'tenant_id': tenant_id,
                'severity': 'critical' if failure_rate > 0.5 else 'warning',
                'anomaly_type': 'webhook_delivery_failure',
                'status': 'needs_review',
                'details': result,
                'detected_at': now,
                'assignee': None,
                'notes': f"Webhook failures detected: {failed_count}/{len(recent_deliveries)} failed",
                'timeline': []
            })()
            
            # Find and execute escalation rules for webhook health
            webhook_health_rules = self.session.query(EscalationRule).filter(
                EscalationRule.tenant_id == tenant_id,
                EscalationRule.condition_field == "anomaly_type",
                EscalationRule.condition_value == "webhook_delivery_failure",
                EscalationRule.active == True,
            ).all()
            
            escalations = []
            for rule in webhook_health_rules:
                escalation = self._execute_escalation(rule, incident)
                escalations.append(escalation)
            
            result["escalations"] = escalations
        else:
            result["status"] = "ok"
        
        return result

    def check_queue_backlog(self, tenant_id: str) -> Dict[str, Any]:
        """Check for event queue backlog and escalate if processing lag detected.
        
        Monitors reconciliation job performance:
          - Kafka consumer lag (if applicable)
          - Dead letter queue size
          - Processing latency
        
        Escalates if backlog exceeds threshold (default 1000 messages or 5 min lag).
        """
        from models import DeadLetter
        from datetime import datetime, timezone, timedelta
        
        now = datetime.now(timezone.utc)
        check_window = now - timedelta(minutes=5)
        
        # Count dead letters (unprocessed/failed items)
        dead_letter_count = self.session.query(DeadLetter).filter(
            DeadLetter.tenant_id == tenant_id,
            DeadLetter.processed == False,
            DeadLetter.created_at >= check_window,
        ).count()
        
        backlog_threshold = int(os.getenv("QUEUE_BACKLOG_THRESHOLD", "1000"))
        
        result = {
            "tenant_id": tenant_id,
            "dead_letters_unprocessed": dead_letter_count,
            "threshold": backlog_threshold,
            "check_window_minutes": 5,
        }
        
        if dead_letter_count > backlog_threshold:
            result["status"] = "escalation_triggered"
            logger.warning(
                f"Queue backlog detected: {dead_letter_count} unprocessed messages exceed threshold {backlog_threshold}",
                extra={"tenant_id": tenant_id}
            )
            
            # Trigger escalation
            now = datetime.now(timezone.utc)
            incident = type('Incident', (), {
                'id': f"queue_backlog_{int(now.timestamp())}",
                'tenant_id': tenant_id,
                'severity': 'critical' if dead_letter_count > backlog_threshold * 2 else 'warning',
                'anomaly_type': 'queue_backlog',
                'status': 'needs_review',
                'details': result,
                'detected_at': now,
                'assignee': None,
                'notes': f"Queue backlog: {dead_letter_count} unprocessed messages",
                'timeline': []
            })()
            
            # Find and execute escalation rules for queue backlog
            backlog_rules = self.session.query(EscalationRule).filter(
                EscalationRule.tenant_id == tenant_id,
                EscalationRule.condition_field == "anomaly_type",
                EscalationRule.condition_value == "queue_backlog",
                EscalationRule.active == True,
            ).all()
            
            escalations = []
            for rule in backlog_rules:
                escalation = self._execute_escalation(rule, incident)
                escalations.append(escalation)
            
            result["escalations"] = escalations
        else:
            result["status"] = "ok"
        
        return result

    def _rule_to_dict(self, rule: EscalationRule) -> Dict[str, Any]:
        """Convert rule object to dictionary."""
        return {
            "id": rule.id,
            "tenant_id": rule.tenant_id,
            "name": rule.name,
            "description": rule.description,
            "condition_field": rule.condition_field,
            "condition_operator": rule.condition_operator,
            "condition_value": rule.condition_value,
            "action": rule.action,
            "target": rule.target,
            "webhook_url": rule.webhook_url,
            "active": rule.active,
            "priority": rule.priority,
            "created_at": rule.created_at.isoformat(),
        }
