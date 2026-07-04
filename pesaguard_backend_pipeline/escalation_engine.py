"""Custom escalation rules engine for per-tenant escalation workflows."""

import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from models import EscalationRule, Discrepancy, OnCallRotation

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
        # This would integrate with email/SMS/webhook
        return {
            "status": "notification_sent",
            "rule": rule["name"],
            "target": rule.get("target"),
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

        # Webhook would be triggered here
        return {
            "status": "webhook_triggered",
            "url": webhook_url,
            "rule": rule["name"],
        }

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
