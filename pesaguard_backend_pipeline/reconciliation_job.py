"""
Reconciliation Job (MVP version — plain Kafka consumer loop)

For the pilot, this runs as a simple long-lived Python consumer rather
than a full Flink job. Graduate to PyFlink only once transaction volume
or latency requirements justify the added ops complexity.

Logic:
  1. Consume M-Pesa transaction events from `mpesa.transactions.raw`
  2. Check idempotency using ProcessedTransaction table (database-backed)
  3. Look up matching internal record (via connector)
  4. Compare amount, phone number, timing
  5. Persist idempotency mark + audit entry ATOMICALLY (single transaction)
  6. Manually commit the Kafka consumer offset (only after step 5 succeeds)
  7. Best-effort: emit to `mpesa.transactions.matched` or `mpesa.discrepancies`
"""
import json
import logging
import os
from datetime import datetime, timezone

try:
    from kafka import KafkaConsumer, KafkaProducer
except ImportError:  # pragma: no cover - exercised in lightweight test environments
    KafkaConsumer = None  # type: ignore[assignment]
    KafkaProducer = None  # type: ignore[assignment]

from alerting_service import AlertingService
from anomaly_rules import check_for_anomalies
from base_connector import ConnectorRegistry
from logging_utils import configure_logging
from reconciliation_engine import evaluate_transaction
from event_store import EventStore, ProcessResult
from tenant_settings import TenantSettingsStore
from action_audit import ActionAuditEntry
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

configure_logging()
logger = logging.getLogger("pesaguard.reconciliation")

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC_RAW = os.getenv("KAFKA_TOPIC_TRANSACTIONS", "mpesa.transactions.raw")
TOPIC_MATCHED = os.getenv("KAFKA_TOPIC_MATCHED", "mpesa.transactions.matched")
TOPIC_DISCREPANCIES = os.getenv("KAFKA_TOPIC_DISCREPANCIES", "mpesa.discrepancies")
TENANT_ID = os.getenv("TENANT_ID", "default")
WINDOW_MINUTES = int(os.getenv("RECONCILIATION_WINDOW_MINUTES", "15"))
settings_store = TenantSettingsStore()

DB_URL = os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")
engine_for_audit = create_engine(DB_URL, pool_pre_ping=True)
AuditSession = sessionmaker(bind=engine_for_audit, expire_on_commit=False)
event_store = EventStore(database_url=DB_URL)

try:
    from models import Base as _Base
    _Base.metadata.create_all(engine_for_audit)
except Exception:
    pass


def dispatch_discrepancy_alert(evaluation: dict, tenant_id: str | None = None, **_: object) -> dict:
    if evaluation.get("status") not in {"needs_review", "missing_payment"} and not evaluation.get("anomalies"):
        return {"status": "skipped", "trans_id": evaluation.get("trans_id")}

    service = AlertingService(
        tenant_settings=settings_store.get(tenant_id or TENANT_ID),
    )
    return service.handle_discrepancy(evaluation)


def _persist_atomically(event: dict, evaluation: dict, trans_id: str) -> ProcessResult:
    """Write the idempotency ledger entry AND the audit entry in ONE
    transaction, committing once.

    FIXED: previously these were three independent writes (mark_processed's
    own internal session, a Kafka publish, and a third separate AuditSession)
    with no shared transaction. If the process crashed or Kafka was
    unreachable after the idempotency mark committed but before the audit
    entry was written, the transaction was permanently marked "already
    processed" — so every future retry silently skipped it, with no audit
    trail and no downstream topic message ever produced. The transaction
    effectively vanished from the pipeline while the system believed it had
    been handled.

    Now: mark_processed_in_session() and the ActionAuditEntry write share one
    session; either both are committed together, or the whole transaction
    rolls back and the message is NOT considered processed, so a future
    retry can pick it up cleanly.
    """
    session = AuditSession()
    try:
        result = event_store.mark_processed_in_session(session, event, tenant_id=TENANT_ID)

        if result == ProcessResult.DUPLICATE:
            session.rollback()
            return ProcessResult.DUPLICATE

        if result == ProcessResult.ERROR:
            session.rollback()
            return ProcessResult.ERROR

        is_discrepancy = evaluation["status"] in {"needs_review", "missing_payment"} or evaluation.get("anomalies")
        session.add(ActionAuditEntry(
            id=f"audit_{int(datetime.now(timezone.utc).timestamp() * 1000)}_{trans_id}",
            tenant_id=TENANT_ID,
            actor="reconciliation_job",
            action="discrepancy_flagged" if is_discrepancy else "matched",
            details={
                "trans_id": trans_id,
                "status": evaluation.get("status"),
                "match": evaluation.get("match"),
                "anomalies": evaluation.get("anomalies", []),
            },
        ))
        session.commit()
        return ProcessResult.STORED
    except Exception:
        logger.exception("Atomic persist failed for trans_id=%s — rolling back, message will be retried", trans_id)
        session.rollback()
        return ProcessResult.ERROR
    finally:
        session.close()


def _publish_downstream(evaluation: dict, trans_id: str, producer) -> None:
    """Best-effort publish to the matched/discrepancies Kafka topic.

    This runs AFTER the atomic DB write above has already committed, so the
    database's Transaction/Discrepancy/ActionAuditEntry records are already
    the authoritative, correct account of what happened to this transaction
    even if this publish step fails. A failure here is logged for monitoring
    and manual replay (e.g. a tool that reads Discrepancy rows directly)
    rather than allowed to undo or block the already-committed decision.
    """
    is_discrepancy = evaluation["status"] in {"needs_review", "missing_payment"} or evaluation.get("anomalies")
    topic = TOPIC_DISCREPANCIES if is_discrepancy else TOPIC_MATCHED
    try:
        producer.send(topic, value=evaluation)
        if is_discrepancy:
            logger.warning("Discrepancy flagged for %s: %s", trans_id, evaluation)
            try:
                dispatch_discrepancy_alert(evaluation, tenant_id=TENANT_ID)
            except TypeError:
                dispatch_discrepancy_alert(evaluation)
        else:
            logger.info("Transaction %s reconciled cleanly", trans_id)
    except Exception:
        logger.exception(
            "Failed to publish trans_id=%s to topic=%s — the DB record is already "
            "committed and correct; this only affects downstream Kafka consumers, "
            "which should be reconciled via the Discrepancy/Transaction tables directly "
            "if this keeps happening.",
            trans_id, topic,
        )


def run():
    if KafkaConsumer is None or KafkaProducer is None:
        logger.warning("Kafka dependencies are unavailable; reconciliation flow will not consume or publish events")
        return

    consumer = KafkaConsumer(
        TOPIC_RAW,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        group_id="pesaguard-reconciliation",
        auto_offset_reset="earliest",
        # FIXED: was enable_auto_commit=True, which advances the consumer
        # offset on a timer regardless of whether a message actually finished
        # processing. Combined with the non-atomic writes bug above, a
        # message could be auto-committed as "done" from Kafka's perspective
        # even if it only partially completed — removing any safety net of
        # redelivery on restart. Now offsets are committed manually, only
        # after the atomic DB write for that message has succeeded.
        enable_auto_commit=False,
    )
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    logger.info("Reconciliation job started, listening on %s", TOPIC_RAW)

    connector_registry = ConnectorRegistry.from_env()

    for message in consumer:
        event = message.value
        trans_id = event.get("TransID", "unknown")

        try:
            if event_store.already_processed(trans_id):
                logger.info("Idempotency: skipping duplicate trans_id=%s (already processed)", trans_id)
                consumer.commit()
                continue

            # NOTE: seen_trans_ids is freshly empty for every message, so
            # evaluate_transaction's in-memory duplicate check against it can
            # never fire here — that's expected, not a bug: real duplicate
            # detection for this job is the DB-backed already_processed()
            # check above. This local set only matters for a single
            # evaluate_transaction() call's internal logic.
            seen_trans_ids = set()
            anomalies = check_for_anomalies(event, seen_trans_ids)

            connector = connector_registry.get_connector(TENANT_ID)
            internal_records = connector.fetch_recent_records(since_minutes=WINDOW_MINUTES) if connector else []

            tenant_cfg = settings_store.get(TENANT_ID)
            evaluation = evaluate_transaction(
                event,
                internal_records,
                seen_trans_ids,
                window_minutes=WINDOW_MINUTES,
                tenant_settings=tenant_cfg,
            )

            evaluation["tenant_id"] = TENANT_ID
            evaluation["event"] = event
            evaluation["checked_at"] = datetime.now(timezone.utc).isoformat()
            evaluation["anomalies"] = anomalies + evaluation.get("anomalies", [])

            logger.info(
                "Reconciliation outcome",
                extra={
                    "tenant_id": TENANT_ID,
                    "trans_id": trans_id,
                    "status": evaluation["status"],
                    "severity": evaluation["severity"],
                },
            )

            # Steps 5 + 6: atomic DB write, then manual offset commit — the
            # database is now the authoritative record of what happened to
            # this message, and Kafka won't redeliver it.
            persist_result = _persist_atomically(event, evaluation, trans_id)

            if persist_result == ProcessResult.DUPLICATE:
                logger.info("Duplicate trans_id=%s caught at write time (race with another consumer)", trans_id)
                consumer.commit()
                continue

            if persist_result == ProcessResult.ERROR:
                # Do NOT commit the offset — leave this message for retry
                # (by this consumer on restart, or after a fix) rather than
                # silently treating a failed write as done.
                logger.error("Failed to persist trans_id=%s; offset NOT committed, message will be retried", trans_id)
                continue

            consumer.commit()

            # Step 7: best-effort downstream publish, after the authoritative
            # DB state is already safely committed.
            _publish_downstream(evaluation, trans_id, producer)

        except Exception:
            logger.exception("Error processing message trans_id=%s", trans_id)
            # Do not commit the offset here either — an unexpected error
            # means we don't know the message was fully handled, so leave it
            # for retry rather than silently advancing past it.


if __name__ == "__main__":
    run()
