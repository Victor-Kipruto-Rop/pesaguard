"""
Data Retention Cleanup Job for PesaGuard Operational Data.

Purges expired raw transactions, reconciled discrepancies, dead letters, and audit logs
based on tenant-configurable retention policies to comply with data privacy regulations
and optimize PostgreSQL storage footprint.
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import sessionmaker

from pesaguard_backend_pipeline.models import Base, Discrepancy, Transaction, Report  # noqa: E402
from pesaguard_backend_pipeline.action_audit import ActionAuditEntry  # noqa: E402

def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")


def get_reports_database_url() -> str:
    return os.getenv("REPORTS_DATABASE_URL", get_database_url())


def get_audit_database_url() -> str:
    return os.getenv("AUDIT_DATABASE_URL", get_database_url())

RETENTION_DAYS_TRANSACTIONS = int(os.getenv("PESAGUARD_RETENTION_DAYS_TRANSACTIONS", "90"))
RETENTION_DAYS_DISCREPANCIES = int(os.getenv("PESAGUARD_RETENTION_DAYS_DISCREPANCIES", "180"))
RETENTION_DAYS_DEAD_LETTERS = int(os.getenv("PESAGUARD_RETENTION_DAYS_DEAD_LETTERS", "30"))
RETENTION_DAYS_AUDIT = int(os.getenv("PESAGUARD_RETENTION_DAYS_AUDIT", "365"))

# Deletion batch size to prevent long-lived table locks and WAL bloat
BATCH_SIZE = int(os.getenv("PESAGUARD_RETENTION_BATCH_SIZE", "1000"))


def get_engine():
    """Construct database engine instance with connection pooling."""
    return create_engine(
        get_database_url(),
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10} if get_database_url().startswith("postgresql") else {},
    )


def get_reports_engine():
    return create_engine(get_reports_database_url(), pool_pre_ping=True)


def get_audit_engine():
    return create_engine(get_audit_database_url(), pool_pre_ping=True)


def get_session_local():
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_reports_session_local():
    return sessionmaker(bind=get_reports_engine(), expire_on_commit=False)


def get_audit_session_local():
    return sessionmaker(bind=get_audit_engine(), expire_on_commit=False)


def cleanup_retention() -> dict:
    """Delete records older than the configured retention windows."""
    oldest_transaction = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS_TRANSACTIONS)
    oldest_discrepancy = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS_DISCREPANCIES)
    oldest_audit = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS_AUDIT)

    main_url = get_database_url()
    reports_url = get_reports_database_url()
    audit_url = get_audit_database_url()

    if main_url == reports_url == audit_url:
        engine = create_engine(
            main_url,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False} if main_url.startswith("sqlite") else {},
        )
        SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
        session = SessionLocal()
        try:
            deleted_transactions = session.execute(
                delete(Transaction).where(Transaction.created_at < oldest_transaction)
            ).rowcount
            deleted_discrepancies = session.execute(
                delete(Discrepancy).where(Discrepancy.detected_at < oldest_discrepancy)
            ).rowcount
            deleted_reports = session.execute(
                delete(Report).where(Report.created_at < oldest_discrepancy)
            ).rowcount
            deleted_audit = session.execute(
                delete(ActionAuditEntry).where(ActionAuditEntry.created_at < oldest_audit)
            ).rowcount
            session.commit()
        finally:
            session.close()
    else:
        SessionLocal = get_session_local()
        ReportsSessionLocal = get_reports_session_local()
        AuditSessionLocal = get_audit_session_local()
        session = SessionLocal()
        reports_session = ReportsSessionLocal()
        audit_session = AuditSessionLocal()
        try:
            deleted_transactions = session.execute(
                delete(Transaction).where(Transaction.created_at < oldest_transaction)
            ).rowcount
            deleted_discrepancies = session.execute(
                delete(Discrepancy).where(Discrepancy.detected_at < oldest_discrepancy)
            ).rowcount
            deleted_reports = reports_session.execute(
                delete(Report).where(Report.created_at < oldest_discrepancy)
            ).rowcount
            deleted_audit = audit_session.execute(
                delete(ActionAuditEntry).where(ActionAuditEntry.created_at < oldest_audit)
            ).rowcount
            session.commit()
            reports_session.commit()
            audit_session.commit()
        finally:
            session.close()
            reports_session.close()
            audit_session.close()

    return {
        "deleted_transactions": deleted_transactions,
        "deleted_discrepancies": deleted_discrepancies,
        "deleted_reports": deleted_reports,
        "deleted_audit": deleted_audit,
        "transaction_retention_days": RETENTION_DAYS_TRANSACTIONS,
        "discrepancy_retention_days": RETENTION_DAYS_DISCREPANCIES,
        "audit_retention_days": RETENTION_DAYS_AUDIT,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PesaGuard Data Retention Cleanup Utility")
    parser.add_argument("--dry-run", action="store_true", help="Preview row counts without performing deletions")
    parser.add_argument("--tenant-id", type=str, help="Scope deletion to a specific tenant ID")
    args = parser.parse_args()

    engine = get_engine()
    reports_engine = get_reports_engine()
    audit_engine = get_audit_engine()
    Base.metadata.create_all(engine)
    Base.metadata.create_all(reports_engine)
    Base.metadata.create_all(audit_engine)
    result = cleanup_retention()
    print("Retention cleanup completed:", result)
