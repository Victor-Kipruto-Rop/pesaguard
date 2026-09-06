from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from ..core.interfaces import CommunicationProvider, NotificationRequest
from ..core.exceptions import CommunicationError
from ..core.enums import NotificationStatus
from ..models import CommunicationAttempt, CommunicationNotification


class NotificationService:
    """Persist and submit one notification through an injected provider."""

    def __init__(self, session: Session, provider: CommunicationProvider):
        self.session = session
        self.provider = provider

    def send(self, request: NotificationRequest) -> CommunicationNotification:
        if not request.idempotency_key:
            raise ValueError("idempotency_key is required for notification delivery")
        existing = self.session.query(CommunicationNotification).filter_by(
            tenant_id=request.tenant_id,
            idempotency_key=request.idempotency_key,
        ).one_or_none()
        if existing is not None:
            return existing

        notification = CommunicationNotification(
            id=request.notification_id or f"notification_{uuid.uuid4().hex}",
            tenant_id=request.tenant_id,
            channel=request.channel.value,
            recipient=request.recipient,
            message=request.message,
            template_id=request.template_id,
            priority=request.priority.value,
            status=NotificationStatus.PROCESSING.value,
            idempotency_key=request.idempotency_key,
            provider=self.provider.name,
            correlation_id=request.correlation_id,
            trace_id=request.trace_id,
            metadata_json=dict(request.variables),
        )
        self.session.add(notification)
        self.session.flush()
        attempt = CommunicationAttempt(
            id=f"attempt_{uuid.uuid4().hex}",
            notification_id=notification.id,
            attempt_number=1,
            provider=self.provider.name,
            status=NotificationStatus.PROCESSING.value,
        )
        self.session.add(attempt)
        try:
            result = self.provider.send(request)
        except CommunicationError as exc:
            notification.status = NotificationStatus.RETRYING.value if exc.retryable else NotificationStatus.FAILED.value
            notification.failure_code = exc.code
            notification.failure_reason = str(exc)
            attempt.status = notification.status
            attempt.error_code = exc.code
            attempt.error_detail = str(exc)
        else:
            notification.status = result.status
            notification.provider_message_id = result.provider_message_id
            attempt.status = result.status
            attempt.provider_message_id = result.provider_message_id
            notification.metadata_json = {
                **dict(notification.metadata_json or {}),
                "provider_response": dict(result.raw_response),
            }
        self.session.flush()
        return notification
