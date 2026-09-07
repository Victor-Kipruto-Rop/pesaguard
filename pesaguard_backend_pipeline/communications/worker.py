from __future__ import annotations

import json
import logging
import os
import socket
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy.orm import Session

from .core.enums import CommunicationChannel, CommunicationPriority
from .core.interfaces import NotificationRequest
from .models import CommunicationAttempt, CommunicationNotification
from .outbox import claim_entries, complete_entry, fail_entry
from .providers.factory import build_africas_talking_provider

logger = logging.getLogger(__name__)


def process_outbox_once(session: Session, *, provider_factory: Callable[[], Any] = build_africas_talking_provider, worker_id: str | None = None, limit: int = 50) -> int:
    worker_id = worker_id or f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
    entries = claim_entries(session, worker_id=worker_id, limit=limit)
    for entry in entries:
        notification = session.query(CommunicationNotification).filter_by(id=entry.notification_id).one()
        attempt = CommunicationAttempt(
            id=f"attempt_{uuid.uuid4().hex}",
            notification_id=notification.id,
            attempt_number=entry.attempt_count,
            provider=notification.provider or "unknown",
            status="processing",
            started_at=datetime.now(timezone.utc),
        )
        session.add(attempt)
        try:
            provider = provider_factory()
            request = NotificationRequest(
                tenant_id=notification.tenant_id,
                recipient=notification.recipient,
                message=notification.message,
                channel=CommunicationChannel(notification.channel),
                priority=CommunicationPriority(notification.priority),
                idempotency_key=notification.idempotency_key,
                notification_id=notification.id,
                template_id=notification.template_id,
                variables=notification.metadata_json or {},
                correlation_id=notification.correlation_id,
                trace_id=notification.trace_id,
            )
            result = provider.send(request)
            notification.provider = result.provider
            notification.provider_message_id = result.provider_message_id
            notification.status = result.status
            attempt.status = result.status
            attempt.provider = result.provider
            attempt.provider_message_id = result.provider_message_id
            attempt.completed_at = datetime.now(timezone.utc)
            complete_entry(session, entry, worker_id=worker_id)
        except Exception as exc:
            attempt.status = "retrying" if entry.attempt_count < entry.max_attempts else "dead_letter"
            attempt.error_detail = str(exc)
            attempt.completed_at = datetime.now(timezone.utc)
            fail_entry(session, entry, worker_id=worker_id, error=str(exc), retry_delay_seconds=min(3600, 2 ** entry.attempt_count))
        session.commit()
    return len(entries)


def consume_notification_events(session_factory: Callable[[], Session], *, provider_factory: Callable[[], Any] = build_africas_talking_provider) -> None:
    """Consume notification Kafka events when kafka-python-ng is installed."""
    from kafka import KafkaConsumer

    consumer = KafkaConsumer(
        os.getenv("PESAGUARD_NOTIFICATION_TOPIC", "notification.events"),
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        group_id=os.getenv("PESAGUARD_NOTIFICATION_GROUP", "pesaguard-communications"),
        enable_auto_commit=False,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )
    for message in consumer:
        session = session_factory()
        try:
            event = message.value
            if event.get("recipient"):
                from .application.notification_service import NotificationService
                NotificationService(session, provider_factory()).enqueue(NotificationRequest(
                    tenant_id=event["tenant_id"],
                    recipient=event["recipient"],
                    message=str(event.get("context", {}).get("message", event["event"])),
                    idempotency_key=str(event.get("event_id") or f"{message.topic}:{message.partition}:{message.offset}"),
                    correlation_id=event.get("correlation_id"),
                    trace_id=event.get("trace_id"),
                ))
            session.commit()
            consumer.commit()
        except Exception:
            session.rollback()
            logger.exception("Notification event processing failed")
        finally:
            session.close()
