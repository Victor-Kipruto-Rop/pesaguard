"""Background task support for PesaGuard webhook ingestion."""

import logging
import os
from typing import Any, Dict

logger = logging.getLogger("pesaguard.background_tasks")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RQ_QUEUE_NAME = os.getenv("RQ_QUEUE_NAME", "transaction_events")


def enqueue_transaction_event(topic: str, payload: dict) -> Dict[str, Any]:
    """Enqueue a transaction event for background Kafka publishing.

    NOTE (not fixed here, flagging for follow-up): producer.py's
    publish_transaction_event() now raises on a genuine Kafka delivery
    failure (see that file's fix). Since _publish_transaction_event runs
    inside an RQ worker process, that exception will fail the RQ job — but
    nothing here registers an on_failure callback or otherwise monitors RQ's
    failed-job registry. A sustained Kafka outage would currently pile up
    silently-failed background jobs with zero application-level visibility,
    since this function already returned "queued" and the caller (the
    webhook handler) moved on before the job actually ran. Worth adding an
    RQ failure callback (or a periodic check of the failed job registry)
    that logs/alerts — not done here since it's a monitoring/ops addition,
    not a one-line code fix.
    """
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


def _list_tenant_ids(store) -> list[str]:
    """Get the list of tenant IDs to generate reports for.

    FIXED: previously reached into TenantSettingsStore's private `_data`
    attribute directly (`store._data.keys()`), silently falling back to
    `["default"]` if that attribute didn't exist. That means a future
    refactor of TenantSettingsStore (renamed internal attribute, different
    storage backend, lazy loading) would silently stop generating reports
    for every real tenant — no test failure, no error, just quietly wrong
    behavior. This now fails loudly instead of guessing, so the gap is
    visible immediately rather than discovered later as "why do we only
    have reports for the default tenant."

    TODO: TenantSettingsStore should expose a proper public method (e.g.
    list_tenant_ids()) — this is a stopgap until that exists.
    """
    if hasattr(store, "list_tenant_ids"):
        return list(store.list_tenant_ids())
    if hasattr(store, "_data"):
        logger.warning(
            "TenantSettingsStore has no public list_tenant_ids() method — "
            "falling back to its private _data attribute. This is fragile; "
            "add a public method to TenantSettingsStore."
        )
        return list(store._data.keys())
    raise RuntimeError(
        "Cannot determine tenant list: TenantSettingsStore exposes neither "
        "list_tenant_ids() nor a _data attribute. Refusing to silently "
        "default to a single 'default' tenant, which could hide real "
        "tenants from report generation."
    )


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
        from datetime import datetime, timedelta, timezone
        import uuid
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}

    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)

    now = datetime.now(timezone.utc)
    if report_type == "daily":
        period_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_start = period_end - timedelta(days=1)
    else:
        period_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_start = period_end - timedelta(days=7)

    store = TenantSettingsStore()
    if tenant_id:
        tenants = [tenant_id]
    else:
        try:
            tenants = _list_tenant_ids(store)
        except RuntimeError:
            logger.exception("Failed to determine tenant list for report generation")
            return {"status": "failed", "error": "could_not_determine_tenant_list"}

    created = 0
    failed_tenants = []

    # FIXED: previously all tenants shared ONE session with a SINGLE commit
    # at the very end, but caught per-tenant exceptions with
    # session.rollback() + continue. Since rollback() undoes the entire
    # open transaction, a later tenant's failure silently destroyed any
    # earlier tenant's already-added-but-not-yet-committed Report row —
    # while `created` had already been incremented for that earlier tenant,
    # making the function's own return value wrong about what was actually
    # persisted. Now each tenant gets its own session and its own commit, so
    # one tenant's failure can only roll back that tenant's own work.
    for tenant in tenants:
        with Session() as session:
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
                session.commit()
                created += 1
            except Exception:
                logger.exception("Failed to generate report for tenant=%s", tenant)
                session.rollback()
                failed_tenants.append(tenant)
                continue

    return {
        "status": "ok" if not failed_tenants else "partial",
        "created_reports": created,
        "failed_tenants": failed_tenants,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
    }

