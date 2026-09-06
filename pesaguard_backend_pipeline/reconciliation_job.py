"""
Reconciliation Job (Production Kafka Consumer Service)

Processes M-Pesa transaction events from `mpesa.transactions.raw`, executes multi-tenant
reconciliation checks against connector internal records, atomically records idempotency marks
and audit entries in Postgres, and commits consumer offsets safely.
"""

from __future__ import annotations

import json
import logging
import os
import signal
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    from kafka import KafkaConsumer, KafkaProducer
    HAS_KAFKA = True
except ImportError:
    KafkaConsumer = None  # type: ignore[assignment]
    KafkaProducer = None  # type: ignore[assignment]
    HAS_KAFKA = False

from pesaguard_backend_pipeline.anomaly_rules import check_for_anomalies
from pesaguard_backend_pipeline.base_connector import ConnectorRegistry
from pesaguard_backend_pipeline.logging_utils import configure_logging
from pesaguard_backend_pipeline.reconciliation_engine import evaluate_transaction
from pesaguard_backend_pipeline.event_store import EventStore, ProcessResult
from pesaguard_backend_pipeline.action_audit import ActionAuditEntry
from pesaguard_backend_pipeline.tenant_settings import TenantSettingsStore

configure_logging()
logger = logging.getLogger("pesaguard.reconciliation")

# Kafka & Service Settings
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC_RAW = os.getenv("KAFKA_TOPIC_TRANSACTIONS", "mpesa.transactions.raw")
TOPIC_MATCHED = os.getenv("KAFKA_TOPIC_MATCHED", "mpesa.transactions.matched")
TOPIC_DISCREPANCIES = os.getenv("KAFKA_TOPIC_DISCREPANCIES", "mpesa.discrepancies")
DEFAULT_TENANT_ID = os.getenv("TENANT_ID", "default")
WINDOW_MINUTES = int(os.getenv("RECONCILIATION_WINDOW_MINUTES", "15"))

# Database Engine & Event Store Setup
#
# Audit writes (idempotency ledger + ActionAuditEntry) may be directed at a separate
# database from the transactional data via AUDIT_DATABASE_URL. Both engines use
# pool_pre_ping; the audit engine additionally gets explicit pool sizing for Postgres.
DB_URL = os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")
AUDIT_DB_URL = os.getenv("AUDIT_DATABASE_URL", DB_URL)

_audit_engine_kwargs = {"pool_pre_ping": True}
if not AUDIT_DB_URL.startswith("sqlite"):
    _audit_engine_kwargs.update({"pool_size": 5, "max_overflow": 10})

engine_for_audit = create_engine(AUDIT_DB_URL, **_audit_engine_kwargs)
AuditSession = sessionmaker(bind=engine_for_audit, expire_on_commit=False)

# The EventStore MUST be bound to the audit database: it is the store that owns the
# idempotency ledger (ProcessedTransaction) rows written by mark_processed_in_session()
# through AuditSession below. Binding it to DB_URL instead would make already_processed()
# read from a different database than the one being written to, so the pre-flight
# duplicate gate would never observe its own writes (silently useless whenever
# AUDIT_DATABASE_URL differs from DATABASE_URL, as in docker-compose).
event_store = EventStore(database_url=AUDIT_DB_URL)
settings_store = TenantSettingsStore()

# Ensure audit tables exist when module is imported (helps tests and first-run environments)
try:
    from pesaguard_backend_pipeline.models import Base as _Base
    _Base.metadata.create_all(engine_for_audit)
except Exception:
    pass


def _signal_handler(signum, frame):
    """Graceful shutdown signal listener for containerized deployments."""
    global _RUNNING
    logger.info("Received termination signal (%s). Initiating graceful shutdown...", signum)
    _RUNNING = False


# NOTE: Signal handlers are deliberately NOT registered at import time. Registering
# them here would replace the caller's (e.g. pytest's) SIGINT handling for the whole
# process whenever this module is imported, which previously aborted unrelated test
# setup. run() installs them only while the consumer is actually running and restores
# the previous handlers on exit.
_RUNNING = True



def _persist_atomically(event: Dict[str, Any], evaluation: Dict[str, Any], trans_id: str, tenant_id: str) -> ProcessResult:
    """
    Atomically commit the idempotency ledger entry and audit log record
    within a SINGLE database transaction.
    """
    session = AuditSession()
    try:
        result = event_store.mark_processed_in_session(session, event, tenant_id=tenant_id)

        if result in (ProcessResult.DUPLICATE, ProcessResult.ERROR):
            session.rollback()
            return result

        is_discrepancy = evaluation.get("status") in {"needs_review", "missing_payment"} or bool(evaluation.get("anomalies"))
        audit_entry = ActionAuditEntry(
            id=f"audit_{int(datetime.now(timezone.utc).timestamp() * 1000)}_{trans_id}",
            tenant_id=tenant_id,
            actor="reconciliation_job",
            action="discrepancy_flagged" if is_discrepancy else "matched",
            details={
                "trans_id": trans_id,
                "status": evaluation.get("status"),
                "match": evaluation.get("match"),
                "anomalies": evaluation.get("anomalies", []),
            },
            created_at=datetime.now(timezone.utc),
        )
        session.add(audit_entry)
        session.commit()
        return ProcessResult.STORED

    except Exception as exc:
        logger.exception("Atomic persist transaction failed for trans_id=%s — rolling back: %s", trans_id, exc)
        session.rollback()
        return ProcessResult.ERROR
    finally:
        session.close()


def _commit_offset(consumer: Any, message: Any = None) -> None:
    """Commit Kafka offsets when the consumer exposes it, otherwise no-op for test doubles."""
    commit_fn = getattr(consumer, "commit", None)
    if commit_fn is None:
        return

    try:
        if message is None:
            commit_fn()
        else:
            commit_fn(message=message)
    except TypeError:
        if message is None:
            commit_fn()
        else:
            commit_fn(message)
    except Exception as exc:
        logger.warning("Failed to commit offset: %s", exc)


def _publish_downstream(evaluation: Dict[str, Any], trans_id: str, producer: Any, tenant_id: str) -> None:
    """Best-effort publish of reconciliation results to downstream Kafka topics."""
    is_discrepancy = evaluation.get("status") in {"needs_review", "missing_payment"} or bool(evaluation.get("anomalies"))
    topic = TOPIC_DISCREPANCIES if is_discrepancy else TOPIC_MATCHED

    try:
        key_bytes = str(trans_id).encode("utf-8")
        val_bytes = json.dumps(evaluation, ensure_ascii=False).encode("utf-8")
        
        try:
            future = producer.send(topic, key=key_bytes, value=val_bytes)
        except TypeError:
            future = producer.send(topic, val_bytes)
        if hasattr(producer, "flush"):
            producer.flush(timeout=5)
        if future is not None and hasattr(future, "get"):
            future.get(timeout=5)

        if is_discrepancy:
            logger.warning("Discrepancy event published for trans_id=%s to topic=%s", trans_id, topic)
        else:
            logger.info("Transaction %s cleanly reconciled and published to %s", trans_id, topic)

    except Exception as exc:
        logger.exception(
            "Failed publishing trans_id=%s to downstream topic=%s. DB record remains authoritative.",
            trans_id, topic
        )


def run():
    """Main execution loop for the reconciliation Kafka consumer service."""
    global _RUNNING
    _RUNNING = True

    # Install graceful-shutdown handlers only while the consumer runs, and restore
    # whatever the caller had installed afterwards so importing/invoking this module
    # never leaves a process-wide handler behind.
    previous_sigint = signal.signal(signal.SIGINT, _signal_handler)
    previous_sigterm = signal.signal(signal.SIGTERM, _signal_handler)

    if not HAS_KAFKA and (KafkaConsumer is None or KafkaProducer is None):
        logger.error("Kafka client dependencies unavailable. Reconciliation job exiting.")
        signal.signal(signal.SIGINT, previous_sigint)
        signal.signal(signal.SIGTERM, previous_sigterm)
        sys.exit(1)

    logger.info("Initializing Reconciliation Job consumer on topic='%s'...", TOPIC_RAW)

    consumer = KafkaConsumer(
        TOPIC_RAW,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        group_id="pesaguard-reconciliation-v2",
        auto_offset_reset="earliest",
        enable_auto_commit=False,  # Manual offset commits after DB persistence
    )

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        retries=3,
        acks="all",
    )

    connector_registry = ConnectorRegistry.from_env()
    logger.info("Reconciliation worker active and listening for M-Pesa callbacks...")

    if not hasattr(consumer, "poll"):
        for message in consumer:
            event = message.value
            trans_id = str(event.get("TransID") or event.get("trans_id") or "unknown").strip()
            tenant_id = str(event.get("tenant_id") or event.get("TenantID") or DEFAULT_TENANT_ID)

            try:
                try:
                    already_processed = event_store.already_processed(trans_id)
                except Exception:
                    already_processed = False

                if already_processed:
                    logger.info("Idempotency: skipping duplicate trans_id=%s for tenant_id=%s", trans_id, tenant_id)
                    try:
                        _commit_offset(consumer, message=message)
                    except Exception:
                        logger.warning("Failed to commit offset for duplicate trans_id=%s", trans_id)
                    continue

                seen_trans_ids: Set[str] = set()
                anomalies = check_for_anomalies(event, seen_trans_ids)

                connector = connector_registry.get_connector(tenant_id)
                internal_records = (
                    connector.fetch_recent_records(since_minutes=WINDOW_MINUTES) if connector else []
                )

                tenant_cfg = settings_store.get(tenant_id)
                evaluation = evaluate_transaction(
                    event,
                    internal_records,
                    seen_trans_ids,
                    window_minutes=WINDOW_MINUTES,
                    tenant_settings=tenant_cfg,
                )

                evaluation["tenant_id"] = tenant_id
                evaluation["event"] = event
                evaluation["checked_at"] = datetime.now(timezone.utc).isoformat()
                evaluation["anomalies"] = list(set(anomalies + evaluation.get("anomalies", [])))

                logger.info(
                    "Reconciled trans_id=%s tenant_id=%s status=%s severity=%s",
                    trans_id, tenant_id, evaluation["status"], evaluation["severity"]
                )

                persist_result = _persist_atomically(event, evaluation, trans_id, tenant_id)

                if persist_result == ProcessResult.DUPLICATE:
                    logger.info("Duplicate trans_id=%s caught during flush, advancing offset.", trans_id)
                    _commit_offset(consumer, message=message)
                    continue

                if persist_result == ProcessResult.ERROR:
                    logger.error("Persistence failed for trans_id=%s. Offset NOT committed for retry.", trans_id)
                    logger.warning("Publishing downstream event despite persistence failure for trans_id=%s.", trans_id)
                else:
                    _commit_offset(consumer, message=message)

                _publish_downstream(evaluation, trans_id, producer, tenant_id)

            except Exception as exc:
                logger.exception("Unexpected error processing trans_id=%s in reconciliation loop: %s", trans_id, exc)

            if not _RUNNING:
                break
    else:
        while _RUNNING:
            message_batch = consumer.poll(timeout_ms=1000)
            if not message_batch:
                continue

            for tp, messages in message_batch.items():
                for message in messages:
                    if not _RUNNING:
                        break

                    event = message.value
                    trans_id = str(event.get("TransID") or event.get("trans_id") or "unknown").strip()
                    tenant_id = str(event.get("tenant_id") or event.get("TenantID") or DEFAULT_TENANT_ID)

                    try:
                        try:
                            already_processed = event_store.already_processed(trans_id)
                        except Exception:
                            already_processed = False

                        if already_processed:
                            logger.info("Idempotency: skipping duplicate trans_id=%s for tenant_id=%s", trans_id, tenant_id)
                            _commit_offset(consumer, message=message)
                            continue

                        seen_trans_ids: Set[str] = set()
                        anomalies = check_for_anomalies(event, seen_trans_ids)

                        connector = connector_registry.get_connector(tenant_id)
                        internal_records = (
                            connector.fetch_recent_records(since_minutes=WINDOW_MINUTES) if connector else []
                        )

                        tenant_cfg = settings_store.get(tenant_id)
                        evaluation = evaluate_transaction(
                            event,
                            internal_records,
                            seen_trans_ids,
                            window_minutes=WINDOW_MINUTES,
                            tenant_settings=tenant_cfg,
                        )

                        evaluation["tenant_id"] = tenant_id
                        evaluation["event"] = event
                        evaluation["checked_at"] = datetime.now(timezone.utc).isoformat()
                        evaluation["anomalies"] = list(set(anomalies + evaluation.get("anomalies", [])))

                        logger.info(
                            "Reconciled trans_id=%s tenant_id=%s status=%s severity=%s",
                            trans_id, tenant_id, evaluation["status"], evaluation["severity"]
                        )

                        persist_result = _persist_atomically(event, evaluation, trans_id, tenant_id)

                        if persist_result == ProcessResult.DUPLICATE:
                            logger.info("Duplicate trans_id=%s caught during flush, advancing offset.", trans_id)
                            _commit_offset(consumer, message=message)
                            continue

                        if persist_result == ProcessResult.ERROR:
                            logger.error("Persistence failed for trans_id=%s. Offset NOT committed for retry.", trans_id)
                            logger.warning("Publishing downstream event despite persistence failure for trans_id=%s.", trans_id)
                        else:
                            _commit_offset(consumer, message=message)

                        _publish_downstream(evaluation, trans_id, producer, tenant_id)

                    except Exception as exc:
                        logger.exception("Unexpected error processing trans_id=%s in reconciliation loop: %s", trans_id, exc)

    logger.info("Cleaning up Kafka consumer resources...")
    # Restore the caller's original signal handlers so this service never leaves a
    # process-wide handler installed after it stops running.
    signal.signal(signal.SIGINT, previous_sigint)
    signal.signal(signal.SIGTERM, previous_sigterm)
    try:
        consumer.close()
        producer.close(timeout=5)
    except Exception as exc:
        logger.debug("Error during consumer shutdown: %s", exc)
    logger.info("Reconciliation Job stopped cleanly.")


if __name__ == "__main__":
    run()

