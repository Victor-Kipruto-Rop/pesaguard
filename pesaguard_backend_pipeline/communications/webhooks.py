from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Mapping

from sqlalchemy.orm import Session

from .core.enums import NotificationStatus
from .models import CommunicationDeliveryReport, CommunicationNotification, CommunicationWebhookEvent
from .core.state_machine import transition


def verify_signature(raw_body: bytes, signature: str | None, secret: str) -> None:
    if not secret:
        raise ValueError("webhook secret is not configured")
    if not signature:
        raise ValueError("webhook signature is required")
    provided = signature.removeprefix("sha256=").strip()
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(provided, expected):
        raise ValueError("invalid webhook signature")


def process_delivery_webhook(
    session: Session,
    raw_body: bytes,
    *,
    signature: str | None,
    secret: str,
    provider: str = "africas_talking",
) -> dict[str, Any]:
    """Verify and idempotently apply an Africa's Talking delivery callback."""
    verify_signature(raw_body, signature, secret)
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("webhook payload must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("webhook payload must be an object")

    provider_event_id = _required_string(payload, "id", "messageId", "messageID")
    event_type = _required_string(payload, "eventType", default="sms.delivery")
    existing = session.query(CommunicationWebhookEvent).filter_by(
        provider=provider,
        provider_event_id=provider_event_id,
        event_type=event_type,
    ).one_or_none()
    if existing is not None:
        return {"status": "duplicate", "event_id": existing.id}

    provider_message_id = _first_string(payload, "messageId", "messageID", "id")
    notification = session.query(CommunicationNotification).filter_by(
        provider=provider,
        provider_message_id=provider_message_id,
    ).one_or_none()
    if notification is None:
        raise ValueError("delivery callback does not reference a known notification")

    now = datetime.now(timezone.utc)
    status = _map_delivery_status(payload.get("status"))
    event = CommunicationWebhookEvent(
        id=f"communication_webhook_{uuid.uuid4().hex}",
        tenant_id=notification.tenant_id,
        provider=provider,
        provider_event_id=provider_event_id,
        event_type=event_type,
        payload=payload,
        status="processed",
        attempt_count=1,
        processed_at=now,
    )
    report = CommunicationDeliveryReport(
        id=f"delivery_{uuid.uuid4().hex}",
        notification_id=notification.id,
        tenant_id=notification.tenant_id,
        provider=provider,
        provider_event_id=provider_event_id,
        status=status.value,
        raw_payload=payload,
        received_at=now,
        delivered_at=now if status == NotificationStatus.DELIVERED else None,
    )
    notification.status = transition(notification.status, status)
    notification.updated_at = now
    session.add_all([event, report])
    session.flush()
    return {"status": "processed", "event_id": event.id, "notification_id": notification.id}


def _first_string(payload: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _required_string(payload: Mapping[str, Any], *keys: str, default: str | None = None) -> str:
    value = _first_string(payload, *keys)
    if value:
        return value
    if default is not None:
        return default
    raise ValueError(f"webhook field {keys[0]!r} is required")


def _map_delivery_status(value: Any) -> NotificationStatus:
    normalized = str(value or "").strip().casefold()
    if normalized in {"delivered", "delivery", "success"}:
        return NotificationStatus.DELIVERED
    if normalized in {"sent", "submitted"}:
        return NotificationStatus.SUBMITTED
    if normalized in {"expired", "failed", "rejected", "undelivered"}:
        return NotificationStatus.FAILED
    raise ValueError("unsupported delivery status")
