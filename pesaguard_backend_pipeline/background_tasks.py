"""
Enterprise-grade background task queue and async worker management for PesaGuard.
Handles distributed job enqueueing, RQ failure hooks, dead-letter recording, and scheduled report generation.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger("pesaguard.background_tasks")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RQ_QUEUE_NAME = os.getenv("RQ_QUEUE_NAME", "transaction_events")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")

# Global thread-safe engine for task-level database persistence
_task_db_engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
)
TaskSessionLocal = sessionmaker(bind=_task_db_engine, expire_on_commit=False)


def handle_job_failure(job, connection, type, value, traceback) -> None:
    """
    RQ Failure Handler Callback.
    Executes automatically when a background RQ job exhausts all retry attempts.
    Logs high-severity alerts and writes job details to the DeadLetter repository.
    """
    job_id = getattr(job, "id", "unknown")
    func_name = getattr(job, "func_name", "unknown")
    args = getattr(job, "args", [])
    
    logger.error(
        "CRITICAL: Async job failed permanently. Job ID: %s, Function: %s, Error: %s",
        job_id, func_name, value, exc_info=(type, value, traceback)
    )

    # Persist job failure into DeadLetter store if job payload is present
    try:
        from models import DeadLetter
        session = TaskSessionLocal()
        try:
            payload = args[1] if len(args) > 1 and isinstance(args[1], dict) else {"raw_args": str(args)}
            dead_letter = DeadLetter(
                id=f"dlq_job_{job_id}",
                tenant_id=payload.get("tenant_id", "default") if isinstance(payload, dict) else "default",
                reason="background_job_failed",
                error_detail=f"Job {func_name} failed: {str(value)}",
                payload=payload,
                created_at=datetime.now(timezone.utc),
            )
            session.add(dead_letter)
            session.commit()
            logger.info("Successfully recorded job failure %s to DeadLetter table.", job_id)
        except Exception as exc:
            logger.exception("Failed writing job failure %s to DeadLetter table: %s", job_id, exc)
            session.rollback()
        finally:
            session.close()
    except Exception as exc:
        logger.error("Could not import DeadLetter model for failure handling: %s", exc)


def enqueue_transaction_event(topic: str, payload: dict) -> Dict[str, Any]:
    """
    Enqueue a transaction event into Redis/RQ for background Kafka publishing.
    Configures exponential retries and explicit failure callbacks.
    """
    if not isinstance(payload, dict):
        logger.error("Invalid transaction payload provided for enqueueing: %s", type(payload))
        return {"status": "failed", "error": "invalid_payload_type"}

    try:
        import redis
        from rq import Queue, Retry
    except ImportError as exc:
        logger.error("RQ or Redis dependencies missing in runtime environment: %s", exc)
        return {
            "status": "failed",
            "error": "rq_or_redis_not_installed",
            "details": str(exc),
        }

    try:
        redis_conn = redis.from_url(REDIS_URL, socket_connect_timeout=5, socket_timeout=5)
        queue = Queue(name=RQ_QUEUE_NAME, connection=redis_conn)
        
        # Enqueue with 3 retries (10s, 30s, 60s delays) and job failure handler
        job = queue.enqueue(
            _publish_transaction_event,
            topic,
            payload,
            job_timeout=30,
            retry=Retry(max=3, interval=[10, 30, 60]),
            on_failure=handle_job_failure,
        )
        
        trans_id = payload.get("TransID", "unknown")
        logger.info("Enqueued transaction event job_id=%s trans_id=%s to queue=%s", job.id, trans_id, RQ_QUEUE_NAME)
        
        return {
            "status": "queued",
            "job_id": job.id,
            "queue": RQ_QUEUE_NAME,
        }
    except Exception as exc:
        logger.exception("Failed to enqueue transaction event to Redis: %s", exc)
        return {"status": "failed", "error": str(exc)}


def _publish_transaction_event(topic: str, payload: dict) -> None:
    """Worker job function that wraps synchronous Kafka publishing."""
    from producer import publish_transaction_event
    publish_transaction_event(topic, payload)


def _list_tenant_ids(store: Any) -> List[str]:
    """Safely discover all active tenant IDs from the TenantSettingsStore."""
    if hasattr(store, "list_tenant_ids") and callable(store.list_tenant_ids):
        return list(store.list_tenant_ids())
    
    if hasattr(store, "get_all_tenants") and callable(store.get_all_tenants):
        return list(store.get_all_tenants().keys())

    if hasattr(store, "_data") and isinstance(store._data, dict):
        logger.warning("TenantSettingsStore lacks list_tenant_ids(); falling back to internal _data structure.")
        return list(store._data.keys())

    logger.warning("Unable to dynamically inspect tenants from store. Defaulting to ['default'].")
    return ["default"]


def generate_reports(report_type: str = "daily", tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate automated reconciliation summary reports per tenant and persist them.
    Executes with dedicated database sessions per tenant to guarantee transaction isolation.
    
    Args:
        report_type: "daily" or "weekly"
        tenant_id: Optional single-tenant filter override.
    """
    try:
        from models import Discrepancy, Report
        from tenant_settings import TenantSettingsStore
    except Exception as exc:
        logger.error("Failed to load required dependencies for report generation: %s", exc)
        return {"status": "failed", "error": str(exc)}

    now = datetime.now(timezone.utc)
    if report_type == "daily":
        period_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_start = period_end - timedelta(days=1)
    elif report_type == "weekly":
        period_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_start = period_end - timedelta(days=7)
    else:
        return {"status": "failed", "error": f"invalid_report_type: {report_type}"}

    store = TenantSettingsStore()
    if tenant_id:
        tenants = [tenant_id]
    else:
        try:
            tenants = _list_tenant_ids(store)
        except Exception as exc:
            logger.exception("Failed determining tenant list for report generation: %s", exc)
            return {"status": "failed", "error": "could_not_determine_tenant_list"}

    created_count = 0
    failed_tenants: List[str] = []

    # Execute isolated per-tenant report generation transactions
    for tenant in tenants:
        session = TaskSessionLocal()
        try:
            discrepancy_count = (
                session.query(Discrepancy)
                .filter(Discrepancy.tenant_id == tenant)
                .filter(Discrepancy.detected_at >= period_start)
                .filter(Discrepancy.detected_at < period_end)
                .count()
            )

            report = Report(
                id=f"rpt_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}",
                tenant_id=tenant,
                report_type=report_type,
                period_start=period_start,
                period_end=period_end,
                content={
                    "discrepancy_count": discrepancy_count,
                    "generated_at": now.isoformat(),
                    "period_days": 1 if report_type == "daily" else 7,
                },
                status="generated",
                created_at=now,
            )
            session.add(report)
            session.commit()
            created_count += 1
            logger.info("Successfully generated %s report for tenant_id=%s", report_type, tenant)

        except Exception as exc:
            logger.exception("Failed generating %s report for tenant_id=%s: %s", report_type, tenant, exc)
            session.rollback()
            failed_tenants.append(tenant)
        finally:
            session.close()

    return {
        "status": "ok" if not failed_tenants else "partial_failure",
        "report_type": report_type,
        "created_reports": created_count,
        "failed_tenants": failed_tenants,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
    }
