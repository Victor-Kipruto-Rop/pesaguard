from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

NOTIFICATION_EVENT_TOPIC = "notification.events"
NOTIFICATION_STATUS_TOPIC = "notification.status"
COMMUNICATION_AUDIT_TOPIC = "communication.audit"

SUPPORTED_NOTIFICATION_EVENTS = frozenset({
    "transaction.received",
    "transaction.completed",
    "transaction.failed",
    "transaction.pending",
    "transaction.reversed",
    "transaction.refunded",
    "transaction.duplicate",
    "transaction.mismatch",
    "reconciliation.exception_created",
    "reconciliation.exception_resolved",
    "fraud.suspected",
    "fraud.confirmed",
    "fraud.blocked",
    "security.mfa_required",
    "provider.degraded",
    "provider.failed",
})


def build_notification_event(
    event: str,
    *,
    tenant_id: str,
    recipient: str | None = None,
    context: Mapping[str, Any] | None = None,
    correlation_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    if event not in SUPPORTED_NOTIFICATION_EVENTS:
        raise ValueError(f"unsupported notification event: {event}")
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        raise ValueError("tenant_id must be a non-empty string")
    payload = {
        "event": event,
        "tenant_id": tenant_id.strip(),
        "recipient": recipient.strip() if isinstance(recipient, str) and recipient.strip() else None,
        "context": dict(context or {}),
        "correlation_id": correlation_id,
        "trace_id": trace_id,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": 1,
    }
    return payload


def discrepancy_notification_event(evaluation: Mapping[str, Any], tenant_id: str) -> dict[str, Any]:
    status = str(evaluation.get("status") or "needs_review")
    event = "reconciliation.exception_created" if status in {"needs_review", "missing_payment"} else "transaction.mismatch"
    return build_notification_event(
        event,
        tenant_id=tenant_id,
        context=dict(evaluation),
        correlation_id=str(evaluation.get("trans_id") or ""),
    )


def transaction_notification_event(transaction: Mapping[str, Any], tenant_id: str, event: str = "transaction.received") -> dict[str, Any]:
    return build_notification_event(event, tenant_id=tenant_id, context=dict(transaction), correlation_id=str(transaction.get("trans_id") or ""))


def fraud_notification_event(finding: Mapping[str, Any], tenant_id: str, event: str = "fraud.suspected") -> dict[str, Any]:
    return build_notification_event(event, tenant_id=tenant_id, context=dict(finding), correlation_id=str(finding.get("transaction_id") or finding.get("trans_id") or ""))


def security_notification_event(details: Mapping[str, Any], tenant_id: str, event: str = "security.mfa_required") -> dict[str, Any]:
    return build_notification_event(event, tenant_id=tenant_id, context=dict(details), recipient=details.get("recipient"))


def reconciliation_notification_event(evaluation: Mapping[str, Any], tenant_id: str, resolved: bool = False) -> dict[str, Any]:
    return discrepancy_notification_event({**evaluation, "status": "resolved" if resolved else evaluation.get("status")}, tenant_id)
