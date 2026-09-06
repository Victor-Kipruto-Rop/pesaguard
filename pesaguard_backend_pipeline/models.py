"""
SQLAlchemy ORM Data Models for PesaGuard's Postgres Store.

Defines schemas for Daraja transactions, idempotency tracking, discrepancy logging,
webhooks, escalation rules, on-call schedules, email audits, and dead-letter queues.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Transaction(Base):
    """Raw M-Pesa transaction events received from Daraja webhooks."""

    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("trans_id", name="uq_transaction_trans_id"),
        Index("ix_transaction_trans_id", "trans_id"),
        Index("ix_transaction_created_at", "created_at"),
        Index("ix_transaction_msisdn", "msisdn"),
    )

    trans_id = Column(String, primary_key=True)
    trans_amount = Column(Float, nullable=False)
    msisdn = Column(String, nullable=False)
    business_short_code = Column(String, nullable=False)
    trans_time = Column(String, nullable=False)  # Raw string timestamp format from Daraja
    raw_payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class ProcessedTransaction(Base):
    """
    Explicit Idempotency Ledger: Tracks which webhook callbacks have been received.
    
    Prevents race conditions and duplicate transaction handling using a unique constraint
    on daraja_trans_id.
    """

    __tablename__ = "processed_transactions"
    __table_args__ = (
        UniqueConstraint("daraja_trans_id", name="uq_daraja_trans_id"),
        Index("ix_processed_daraja_id", "daraja_trans_id"),
        Index("ix_processed_tenant_id", "tenant_id"),
        Index("ix_processed_received_at", "received_at"),
    )

    id = Column(String, primary_key=True)
    daraja_trans_id = Column(String, nullable=False)
    tenant_id = Column(String, nullable=True, default="default")
    status = Column(String, nullable=False, default="received")  # received, validated, stored, failed
    processing_time_ms = Column(Integer, nullable=True)
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    webhook_attempt_number = Column(Integer, default=1)
    source_ip = Column(String, nullable=True)
    signature_verified = Column(Boolean, default=False)
    error_reason = Column(String, nullable=True)


class Discrepancy(Base):
    """Reconciliation anomaly records flagged during transaction checks."""

    __tablename__ = "discrepancies"
    __table_args__ = (
        Index("ix_discrepancy_trans_id", "trans_id"),
        Index("ix_discrepancy_tenant_id", "tenant_id"),
        Index("ix_discrepancy_detected_at", "detected_at"),
        Index("ix_discrepancy_status_resolved", "status", "resolved"),
    )

    id = Column(String, primary_key=True)  # Format: f"{trans_id}-{anomaly_type}"
    trans_id = Column(String, nullable=False)
    tenant_id = Column(String, nullable=True, default="default")
    anomaly_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="needs_review")
    severity = Column(String, nullable=False, default="warning")
    details = Column(Text, nullable=True)
    resolved = Column(Boolean, default=False)
    detected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_note = Column(Text, nullable=True)
    latency_seconds = Column(Integer, nullable=True)
    assignee = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    timeline = Column(JSON, nullable=True, default=list)


class InternalRecord(Base):
    """Customer internal ledger or order system record baseline for comparison."""

    __tablename__ = "internal_records"
    __table_args__ = (
        Index("ix_internal_records_phone", "phone_number"),
        Index("ix_internal_records_synced", "synced_at"),
    )

    internal_ref = Column(String, primary_key=True)
    amount = Column(Float, nullable=False)
    phone_number = Column(String, nullable=False)
    status = Column(String, nullable=False)
    synced_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class WebhookConfig(Base):
    """Registered customer outbound webhook endpoint configurations."""

    __tablename__ = "webhook_configs"
    __table_args__ = (
        Index("ix_webhook_configs_tenant", "tenant_id"),
    )

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    url = Column(String, nullable=False)
    event_types = Column(JSON, nullable=False)  # e.g., ["escalation", "resolution"]
    active = Column(Boolean, default=True)
    retry_attempts = Column(Integer, default=3)
    timeout_seconds = Column(Integer, default=10)
    signing_secret = Column(String, nullable=True)  # Dynamic HMAC signing key
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class WebhookDelivery(Base):
    """Outbound webhook delivery execution and response audit logs."""

    __tablename__ = "webhook_deliveries"
    __table_args__ = (
        Index("ix_webhook_deliveries_webhook_id", "webhook_id"),
        Index("ix_webhook_deliveries_created_at", "created_at"),
    )

    id = Column(String, primary_key=True)
    webhook_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String, nullable=False)  # success, failed, pending
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    attempt_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)


class EscalationRule(Base):
    """Per-tenant automated escalation criteria and notification triggers."""

    __tablename__ = "escalation_rules"
    __table_args__ = (
        Index("ix_escalation_rules_tenant", "tenant_id", "priority"),
    )

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    condition_field = Column(String, nullable=False)  # e.g., "severity", "anomaly_type"
    condition_operator = Column(String, nullable=False)  # e.g., "equals", "greater_than"
    condition_value = Column(String, nullable=False)
    action = Column(String, nullable=False)  # "escalate", "notify", "webhook"
    target = Column(String, nullable=True)
    webhook_url = Column(String, nullable=True)
    active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class OnCallRotation(Base):
    """On-call operational shift rotation schedules."""

    __tablename__ = "on_call_rotations"
    __table_args__ = (
        Index("ix_on_call_tenant_shift", "tenant_id", "shift_start", "shift_end"),
    )

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    operator_id = Column(String, nullable=False)
    operator_name = Column(String, nullable=True)
    operator_email = Column(String, nullable=True)
    operator_phone = Column(String, nullable=True)
    shift_start = Column(DateTime(timezone=True), nullable=False)
    shift_end = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=False)
    escalation_level = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class EmailNotification(Base):
    """Audit log for outgoing email alerts and reconciliation reports."""

    __tablename__ = "email_notifications"
    __table_args__ = (
        Index("ix_email_tenant_created", "tenant_id", "created_at"),
    )

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    recipient_email = Column(String, nullable=False)
    report_type = Column(String, nullable=False)  # "reconciliation", "daily_summary", "escalation"
    subject = Column(String, nullable=False)
    status = Column(String, nullable=False)  # "pending", "sent", "failed"
    content_hash = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class DeadLetter(Base):
    """Failed, malformed, or unprocessable webhook payload repository."""

    __tablename__ = "dead_letters"
    __table_args__ = (
        Index("ix_dead_letters_tenant", "tenant_id"),
        Index("ix_dead_letters_created", "created_at"),
    )

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=True, default="default")
    reason = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    error_detail = Column(Text, nullable=True)
    attempts = Column(Integer, default=0)
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class Report(Base):
    """Persisted daily, weekly, or ad-hoc reconciliation reports."""

    __tablename__ = "reports"
    __table_args__ = (
        Index("ix_reports_tenant_type", "tenant_id", "report_type"),
        Index("ix_reports_created", "created_at"),
    )

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    report_type = Column(String, nullable=False)  # "daily", "weekly", "monthly"
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    content = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default="generated")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)


class OrganizationAccount(Base):
    """Persisted organization payment accounts across payment channels/providers."""

    __tablename__ = "organization_accounts"
    __table_args__ = (
        Index("ix_org_account_org_channel", "organization_id", "payment_channel"),
        Index("ix_org_account_provider", "provider"),
        UniqueConstraint("organization_id", "account_id", name="uq_org_account_org_account_id"),
    )

    id = Column(String, primary_key=True)
    organization_id = Column(String, nullable=False)
    account_id = Column(String, nullable=False)
    payment_channel = Column(String, nullable=False, default="OTHER")
    provider = Column(String, nullable=False, default="UNKNOWN")
    account_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    bank_name = Column(String, nullable=True)
    currency = Column(String, nullable=True, default="KES")
    branch = Column(String, nullable=True)
    account_type = Column(String, nullable=True)
    account_metadata = Column(JSON, nullable=True, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SettlementAttempt(Base):
    """Persisted record of an outbound settlement attempt."""

    __tablename__ = "settlement_attempts"
    __table_args__ = (
        Index("ix_settlement_tenant", "tenant_id"),
        Index("ix_settlement_reference", "reference"),
    )

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    reference = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    account_number = Column(String, nullable=True)
    bank_name = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending")  # pending, requested, success, failed
    response = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    attempt_number = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)


class UserAccount(Base):
    """Persistent user record for local authentication and role assignment."""

    __tablename__ = "user_accounts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "username", name="uq_user_account_tenant_username"),
        Index("ix_user_account_tenant", "tenant_id"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, nullable=False)
    username = Column(String, nullable=False)
    email = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    password_salt = Column(String, nullable=False)
    roles = Column(JSON, nullable=False, default=list)
    permissions = Column(JSON, nullable=False, default=list)
    mfa_enabled = Column(Boolean, default=False)
    status = Column(String, nullable=False, default="active")
    attributes = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class UserSession(Base):
    """Persistent device/session record tied to a user account."""

    __tablename__ = "user_sessions"
    __table_args__ = (
        Index("ix_user_sessions_user", "user_id"),
        Index("ix_user_sessions_tenant", "tenant_id"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    tenant_id = Column(String, nullable=False)
    device_id = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    issued_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)


class ApiKeyRecord(Base):
    """Persistent API key registry for service-to-service access."""

    __tablename__ = "api_key_records"
    __table_args__ = (
        UniqueConstraint("key_value", name="uq_api_key_value"),
        Index("ix_api_key_tenant", "tenant_id"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, nullable=False)
    key_value = Column(String, nullable=False)
    role = Column(String, nullable=False, default="read_only")
    api_metadata = Column("metadata", JSON, nullable=True, default=dict)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)


class OIDCProvider(Base):
    """Persistent external OIDC provider configuration for SSO and tenant-level identity mapping."""

    __tablename__ = "oidc_providers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "issuer", name="uq_oidc_provider_tenant_issuer"),
        Index("ix_oidc_provider_tenant", "tenant_id"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, nullable=False, default="default")
    provider_name = Column(String, nullable=False)
    issuer = Column(String, nullable=False)
    client_id = Column(String, nullable=True)
    client_secret = Column(String, nullable=True)
    authorization_endpoint = Column(String, nullable=True)
    token_endpoint = Column(String, nullable=True)
    userinfo_endpoint = Column(String, nullable=True)
    jwks_uri = Column(String, nullable=True)
    scopes = Column(JSON, nullable=False, default=list)
    enabled = Column(Boolean, default=True)
    allowed_roles = Column(JSON, nullable=True, default=list)
    auto_provision = Column(Boolean, default=False)
    claim_mapping = Column(JSON, nullable=True, default=dict)
    provider_metadata = Column("metadata", JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class MFAChallenge(Base):
    """Simple MFA challenge registry."""

    __tablename__ = "mfa_challenges"
    __table_args__ = (
        Index("ix_mfa_user", "user_id"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    code = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)


class PasswordlessChallenge(Base):
    """Simple passwordless / magic-link challenge registry."""

    __tablename__ = "passwordless_challenges"
    __table_args__ = (
        Index("ix_passwordless_user", "user_id"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    token = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
