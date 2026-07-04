"""
SQLAlchemy models for PesaGuard's Postgres store.
Kept minimal for MVP — add indices/partitioning once volume grows.
"""
from sqlalchemy import Column, String, Float, DateTime, Boolean, Text, JSON, Integer
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()


class Transaction(Base):
    __tablename__ = "transactions"

    trans_id = Column(String, primary_key=True)
    trans_amount = Column(Float, nullable=False)
    msisdn = Column(String, nullable=False)
    business_short_code = Column(String, nullable=False)
    trans_time = Column(String, nullable=False)  # raw Daraja string format
    raw_payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Discrepancy(Base):
    __tablename__ = "discrepancies"

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
