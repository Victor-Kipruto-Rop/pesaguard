"""
SQLAlchemy models for PesaGuard's Postgres store.
Kept minimal for MVP — add indices/partitioning once volume grows.
"""
from sqlalchemy import Column, String, Float, DateTime, Boolean, Text, JSON, Integer, UniqueConstraint, Index
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint('trans_id', name='uq_transaction_trans_id'),
        Index('ix_transaction_trans_id', 'trans_id'),
        Index('ix_transaction_created_at', 'created_at'),
    )

    trans_id = Column(String, primary_key=True)
    trans_amount = Column(Float, nullable=False)
    msisdn = Column(String, nullable=False)
    business_short_code = Column(String, nullable=False)
    trans_time = Column(String, nullable=False)  # raw Daraja string format
    raw_payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ProcessedTransaction(Base):
    """Explicit idempotency ledger: tracks which webhook callbacks have been processed.
    
    Separate from Transaction table for audit clarity. Used by event_store.already_processed()
    and by webhook endpoint to prevent duplicate processing. Unique constraint ensures
    Daraja retries are silently ignored without double-processing.
    """
    __tablename__ = "processed_transactions"
    __table_args__ = (
        UniqueConstraint('daraja_trans_id', name='uq_daraja_trans_id'),
        Index('ix_processed_daraja_id', 'daraja_trans_id'),
        Index('ix_processed_received_at', 'received_at'),
    )

    id = Column(String, primary_key=True)  # UUID for audit trail
    daraja_trans_id = Column(String, nullable=False)  # Daraja M-Pesa TransID
    tenant_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default="received")  # received, validated, stored, failed
    processing_time_ms = Column(Integer, nullable=True)  # latency from webhook receipt to DB store
    received_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # webhook receipt timestamp
    webhook_attempt_number = Column(Integer, default=1)  # which retry attempt from Daraja
    source_ip = Column(String, nullable=True)  # IP of Daraja callback source
    signature_verified = Column(Boolean, default=False)  # whether HMAC signature was valid
    error_reason = Column(String, nullable=True)  # if status=failed, why


class Discrepancy(Base):
    __tablename__ = "discrepancies"
    __table_args__ = (
        Index('ix_discrepancy_trans_id', 'trans_id'),
        Index('ix_discrepancy_tenant_id', 'tenant_id'),
        Index('ix_discrepancy_detected_at', 'detected_at'),
    )

    id = Column(String, primary_key=True)  # e.g. f"{trans_id}-{rule_name}"
    trans_id = Column(String, nullable=False)
    tenant_id = Column(String, nullable=True)
    anomaly_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="needs_review")
    severity = Column(String, nullable=False, default="warning")
    details = Column(Text, nullable=True)
    resolved = Column(Boolean, default=False)
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)
    resolution_note = Column(Text, nullable=True)
    latency_seconds = Column(Integer, nullable=True)
    assignee = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    timeline = Column(JSON, nullable=True, default=list)


class InternalRecord(Base):
    __tablename__ = "internal_records"

    internal_ref = Column(String, primary_key=True)
    amount = Column(Float, nullable=False)
    phone_number = Column(String, nullable=False)
    status = Column(String, nullable=False)
    synced_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class WebhookConfig(Base):
    __tablename__ = "webhook_configs"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    url = Column(String, nullable=False)
    event_types = Column(JSON, nullable=False)  # ["escalation", "resolution", "assignment"]
    active = Column(Boolean, default=True)
    retry_attempts = Column(Integer, default=3)
    timeout_seconds = Column(Integer, default=10)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(String, primary_key=True)
    webhook_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String, nullable=False)  # success, failed, pending
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    attempt_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    delivered_at = Column(DateTime, nullable=True)


class EscalationRule(Base):
    __tablename__ = "escalation_rules"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    condition_field = Column(String, nullable=False)  # e.g., "severity", "age_minutes"
    condition_operator = Column(String, nullable=False)  # e.g., "equals", "greater_than"
    condition_value = Column(String, nullable=False)
    action = Column(String, nullable=False)  # "escalate", "notify", "assign"
    target = Column(String, nullable=True)  # operator ID, webhook ID, etc.
    webhook_url = Column(String, nullable=True)  # optional custom webhook
    active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # higher priority rules execute first
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class OnCallRotation(Base):
    __tablename__ = "on_call_rotations"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    operator_id = Column(String, nullable=False)
    operator_name = Column(String, nullable=True)
    operator_email = Column(String, nullable=True)
    operator_phone = Column(String, nullable=True)
    shift_start = Column(DateTime, nullable=False)
    shift_end = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=False)
    escalation_level = Column(Integer, default=1)  # 1=first line, 2=second, etc.
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class EmailNotification(Base):
    __tablename__ = "email_notifications"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    recipient_email = Column(String, nullable=False)
    report_type = Column(String, nullable=False)  # "reconciliation", "daily_summary", "escalation"
    subject = Column(String, nullable=False)
    status = Column(String, nullable=False)  # "pending", "sent", "failed"
    content_hash = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DeadLetter(Base):
    """Store malformed or rejected webhook payloads for later inspection/replay."""

    __tablename__ = "dead_letters"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=True)
    reason = Column(String, nullable=False)  # e.g., validation_failed, invalid_json
    payload = Column(JSON, nullable=True)
    error_detail = Column(Text, nullable=True)
    attempts = Column(Integer, default=0)
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Report(Base):
    """Scheduled/adhoc generated reports (daily, weekly) for tenants."""

    __tablename__ = "reports"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    report_type = Column(String, nullable=False)  # "daily", "weekly", "monthly"
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    content = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default="generated")  # generated, delivered
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    delivered_at = Column(DateTime, nullable=True)
