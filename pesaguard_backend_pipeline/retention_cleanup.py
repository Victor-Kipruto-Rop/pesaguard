"""Retention cleanup job for PesaGuard operational data."""
import os
from datetime import datetime, timezone, timedelta

from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker

from pesaguard_backend_pipeline.models import Base, Discrepancy, Transaction  # noqa: E402
from pesaguard_backend_pipeline.action_audit import ActionAuditEntry  # noqa: E402

def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")

RETENTION_DAYS_TRANSACTIONS = int(os.getenv("PESAGUARD_RETENTION_DAYS_TRANSACTIONS", "90"))
RETENTION_DAYS_DISCREPANCIES = int(os.getenv("PESAGUARD_RETENTION_DAYS_DISCREPANCIES", "180"))
RETENTION_DAYS_AUDIT = int(os.getenv("PESAGUARD_RETENTION_DAYS_AUDIT", "365"))


def get_engine():
    return create_engine(get_database_url(), pool_pre_ping=True)


def get_session_local():
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def cleanup_retention() -> dict:
    """Delete records older than the configured retention windows."""
    oldest_transaction = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS_TRANSACTIONS)
    oldest_discrepancy = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS_DISCREPANCIES)
    oldest_audit = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS_AUDIT)

    SessionLocal = get_session_local()
    session = SessionLocal()
    try:
        deleted_transactions = session.execute(
            delete(Transaction).where(Transaction.created_at < oldest_transaction)
        ).rowcount
        deleted_discrepancies = session.execute(
            delete(Discrepancy).where(Discrepancy.detected_at < oldest_discrepancy)
        ).rowcount
        deleted_audit = session.execute(
            delete(ActionAuditEntry).where(ActionAuditEntry.created_at < oldest_audit)
        ).rowcount
        session.commit()
    finally:
        session.close()

    return {
        "deleted_transactions": deleted_transactions,
        "deleted_discrepancies": deleted_discrepancies,
        "deleted_audit": deleted_audit,
        "transaction_retention_days": RETENTION_DAYS_TRANSACTIONS,
        "discrepancy_retention_days": RETENTION_DAYS_DISCREPANCIES,
        "audit_retention_days": RETENTION_DAYS_AUDIT,
    }


if __name__ == "__main__":
    engine = get_engine()
    Base.metadata.create_all(engine)
    result = cleanup_retention()
    print("Retention cleanup completed:", result)
