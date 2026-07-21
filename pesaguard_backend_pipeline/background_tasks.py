"""Background task support for PesaGuard webhook ingestion."""

import os
from typing import Any, Dict

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RQ_QUEUE_NAME = os.getenv("RQ_QUEUE_NAME", "transaction_events")


def enqueue_transaction_event(topic: str, payload: dict) -> Dict[str, Any]:
    try:
        import redis
        from rq import Queue, Connection
    except ImportError as exc:
        return {
            "status": "failed",
            "error": "rq or redis package not installed",
            "details": str(exc),
        }

    try:
        redis_conn = redis.from_url(REDIS_URL, socket_connect_timeout=5, socket_timeout=5)
        with Connection(redis_conn):
            queue = Queue(name=RQ_QUEUE_NAME, connection=redis_conn)
            job = queue.enqueue(_publish_transaction_event, topic, payload, job_timeout=30)
        return {
            "status": "queued",
            "job_id": getattr(job, "id", None),
            "queue": RQ_QUEUE_NAME,
        }
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def _publish_transaction_event(topic: str, payload: dict) -> None:
    from producer import publish_transaction_event

    publish_transaction_event(topic, payload)


def generate_reports(report_type: str = "daily", tenant_id: str | None = None) -> dict:
    """Generate simple reconciliation summary reports per tenant and persist them.

    report_type: "daily" or "weekly"
    tenant_id: optional tenant filter for single-tenant report generation.
    Returns a dict with status and created_report_count.
    """
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from models import Report, Discrepancy
        from tenant_settings import TenantSettingsStore
        from datetime import datetime, timedelta
        import uuid
        import os
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}

    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)

    now = datetime.utcnow()
    if report_type == "daily":
        period_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_start = period_end - timedelta(days=1)
    else:
        # weekly: previous calendar week
        period_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_start = period_end - timedelta(days=7)

    store = TenantSettingsStore()
    if tenant_id:
        tenants = [tenant_id]
    else:
        tenants = list(store._data.keys()) if hasattr(store, "_data") else ["default"]
    created = 0

    with Session() as session:
        for tenant in tenants:
            try:
                count = (
                    session.query(Discrepancy)
                    .filter(Discrepancy.tenant_id == tenant)
                    .filter(Discrepancy.detected_at >= period_start)
                    .filter(Discrepancy.detected_at < period_end)
                    .count()
                )
                report = Report(
                    id=f"rpt_{uuid.uuid4().hex[:12]}",
                    tenant_id=tenant,
                    report_type=report_type,
                    period_start=period_start,
                    period_end=period_end,
                    content={"discrepancy_count": count},
                    status="generated",
                )
                session.add(report)
                created += 1
            except Exception:
                session.rollback()
                continue

        session.commit()

    return {"status": "ok", "created_reports": created, "period_start": period_start.isoformat(), "period_end": period_end.isoformat()}
