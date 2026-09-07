from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint

from pesaguard_backend_pipeline.models import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CommunicationNotification(Base):
    __tablename__ = "communication_notifications"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_communication_notification_idempotency"),
        CheckConstraint("status IN ('created', 'queued', 'processing', 'accepted', 'submitted', 'sent', 'delivered', 'failed', 'rejected', 'expired', 'cancelled', 'retrying', 'dead_letter')", name="ck_communication_notification_status"),
        CheckConstraint("priority IN ('critical', 'high', 'normal', 'low')", name="ck_communication_notification_priority"),
        Index("ix_communication_notification_tenant_status_created", "tenant_id", "status", "created_at"),
        Index("ix_communication_notification_tenant_correlation", "tenant_id", "correlation_id"),
    )

    id = Column(String(64), primary_key=True)
    tenant_id = Column(String(128), nullable=False)
    channel = Column(String(32), nullable=False)
    recipient = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    template_id = Column(String(128), nullable=True)
    priority = Column(String(16), nullable=False, default="normal", server_default="normal")
    status = Column(String(32), nullable=False, default="created", server_default="created")
    idempotency_key = Column(String(255), nullable=False)
    provider = Column(String(64), nullable=True)
    provider_message_id = Column(String(255), nullable=True)
    correlation_id = Column(String(128), nullable=True)
    trace_id = Column(String(128), nullable=True)
    metadata_json = Column("metadata", JSON, nullable=False, default=dict, server_default="{}")
    failure_code = Column(String(64), nullable=True)
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, server_default="now()")
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, server_default="now()")


class CommunicationOutboxEntry(Base):
    __tablename__ = "communication_outbox_entries"
    __table_args__ = (
        UniqueConstraint("notification_id", name="uq_communication_outbox_notification"),
        CheckConstraint("status IN ('pending', 'leased', 'retrying', 'completed', 'dead_letter')", name="ck_communication_outbox_status"),
        CheckConstraint("attempt_count >= 0 AND max_attempts > 0", name="ck_communication_outbox_attempt_counts"),
        Index("ix_communication_outbox_due", "status", "available_at"),
        Index("ix_communication_outbox_lease", "lease_expires_at"),
        Index("ix_communication_outbox_tenant_status", "tenant_id", "status", "created_at"),
    )

    id = Column(String(64), primary_key=True)
    notification_id = Column(String(64), ForeignKey("communication_notifications.id"), nullable=False)
    tenant_id = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False, default="pending", server_default="pending")
    attempt_count = Column(Integer, nullable=False, default=0, server_default="0")
    max_attempts = Column(Integer, nullable=False, default=5, server_default="5")
    available_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, server_default="now()")
    leased_by = Column(String(128), nullable=True)
    lease_expires_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, server_default="now()")
    completed_at = Column(DateTime(timezone=True), nullable=True)


class CommunicationAttempt(Base):
    __tablename__ = "communication_attempts"
    __table_args__ = (
        UniqueConstraint("notification_id", "attempt_number", name="uq_communication_attempt_number"),
        Index("ix_communication_attempt_notification_started", "notification_id", "started_at"),
    )

    id = Column(String(64), primary_key=True)
    notification_id = Column(String(64), ForeignKey("communication_notifications.id"), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    provider = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False)
    provider_message_id = Column(String(255), nullable=True)
    error_code = Column(String(64), nullable=True)
    error_detail = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, server_default="now()")
    completed_at = Column(DateTime(timezone=True), nullable=True)


class CommunicationDeliveryReport(Base):
    __tablename__ = "communication_delivery_reports"
    __table_args__ = (
        UniqueConstraint("provider", "provider_event_id", name="uq_communication_delivery_provider_event"),
        Index("ix_communication_delivery_notification_received", "notification_id", "received_at"),
        Index("ix_communication_delivery_tenant_status_received", "tenant_id", "status", "received_at"),
    )

    id = Column(String(64), primary_key=True)
    notification_id = Column(String(64), ForeignKey("communication_notifications.id"), nullable=True)
    tenant_id = Column(String(128), nullable=False)
    provider = Column(String(64), nullable=False)
    provider_event_id = Column(String(255), nullable=False)
    status = Column(String(32), nullable=False)
    raw_payload = Column(JSON, nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, server_default="now()")
    delivered_at = Column(DateTime(timezone=True), nullable=True)


class CommunicationWebhookEvent(Base):
    __tablename__ = "communication_webhook_events"
    __table_args__ = (
        UniqueConstraint("provider", "provider_event_id", "event_type", name="uq_communication_webhook_event"),
        Index("ix_communication_webhook_tenant_received", "tenant_id", "received_at"),
    )

    id = Column(String(64), primary_key=True)
    tenant_id = Column(String(128), nullable=False)
    provider = Column(String(64), nullable=False)
    provider_event_id = Column(String(255), nullable=False)
    event_type = Column(String(64), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(32), nullable=False, default="received", server_default="received")
    attempt_count = Column(Integer, nullable=False, default=0, server_default="0")
    received_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, server_default="now()")
    processed_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
