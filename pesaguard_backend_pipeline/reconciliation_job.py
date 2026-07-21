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
  5. Emit to `mpesa.transactions.matched` or `mpesa.discrepancies`
  6. Persist audit entries in atomic transaction
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
from event_store import EventStore
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

# Local DB session for audit writes + idempotency checks
DB_URL = os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")
engine_for_audit = create_engine(DB_URL, pool_pre_ping=True)
AuditSession = sessionmaker(bind=engine_for_audit, expire_on_commit=False)
event_store = EventStore(database_url=DB_URL)

# Ensure audit tables exist when module is imported (helps tests and first-run environments)
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
        enable_auto_commit=True,
    )
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    logger.info("Reconciliation job started, listening on %s", TOPIC_RAW)

    # Idempotency now backed by database-level unique constraint on ProcessedTransaction.daraja_trans_id
    # This ensures horizontal scalability (multiple reconciliation instances won't duplicate-process)
    connector_registry = ConnectorRegistry.from_env()

    for message in consumer:
        event = message.value
        trans_id = event.get("TransID", "unknown")
        
        try:
            # Step 1: Database-backed idempotency check (ProcessedTransaction table)
            if event_store.already_processed(trans_id):
                logger.info("Idempotency: skipping duplicate trans_id=%s (already processed)", trans_id)
                continue
            
            # Step 2: Anomaly detection (independent of idempotency)
            seen_trans_ids = set()  # Local set within message processing
            anomalies = check_for_anomalies(event, seen_trans_ids)
            
            # Step 3: Fetch matching internal records
            connector = connector_registry.get_connector(TENANT_ID)
            internal_records = connector.fetch_recent_records(since_minutes=WINDOW_MINUTES) if connector else []
            
            # Step 4: Evaluate reconciliation (uses local seen_trans_ids, not global)
            tenant_cfg = settings_store.get(TENANT_ID)
            evaluation = evaluate_transaction(
                event,
                internal_records,
                seen_trans_ids,  # Local set for this message only
                window_minutes=WINDOW_MINUTES,
                tenant_settings=tenant_cfg
            )
            
            # Step 5: Enrich evaluation
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
                    "severity": evaluation["severity"]
                }
            )
            
            # Step 6: Persist idempotency record in database (marks as processed)
            event_store.mark_processed(event, tenant_id=TENANT_ID)
            
            # Step 7: Route to topic + dispatch alerts
            if evaluation["status"] in {"needs_review", "missing_payment"} or anomalies:
                producer.send(TOPIC_DISCREPANCIES, value=evaluation)
                try:
                    dispatch_discrepancy_alert(evaluation, tenant_id=TENANT_ID)
                except TypeError:
                    dispatch_discrepancy_alert(evaluation)
                
                logger.warning("Discrepancy flagged for %s: %s", trans_id, evaluation)
                
                # Step 8: Audit trail (atomic with reconciliation decision)
                try:
                    audit_session = AuditSession()
                    audit_session.add(ActionAuditEntry(
                        id=f"audit_{int(datetime.now(timezone.utc).timestamp()*1000)}_{trans_id}",
                        tenant_id=TENANT_ID,
                        actor="reconciliation_job",
                        action="discrepancy_flagged",
                        details={
                            "trans_id": trans_id,
                            "status": evaluation.get("status"),
                            "match": evaluation.get("match"),
                            "anomalies": evaluation.get("anomalies", [])
                        },
                    ))
                    audit_session.commit()
                except Exception:
                    logger.exception("Failed to write audit entry for discrepancy trans_id=%s", trans_id)
                finally:
                    try:
                        audit_session.close()
                    except Exception:
                        pass
            else:
                producer.send(TOPIC_MATCHED, value=evaluation)
                logger.info("Transaction %s reconciled cleanly", trans_id)
                
                # Audit trail for successful matches
                try:
                    audit_session = AuditSession()
                    audit_session.add(ActionAuditEntry(
                        id=f"audit_{int(datetime.now(timezone.utc).timestamp()*1000)}_{trans_id}",
                        tenant_id=TENANT_ID,
                        actor="reconciliation_job",
                        action="matched",
                        details={
                            "trans_id": trans_id,
                            "match": evaluation.get("match"),
                        },
                    ))
                    audit_session.commit()
                except Exception:
                    logger.exception("Failed to write audit entry for matched transaction trans_id=%s", trans_id)
                finally:
                    try:
                        audit_session.close()
                    except Exception:
                        pass
        
        except Exception as e:
            logger.exception("Error processing message trans_id=%s", trans_id)
            # Continue on error to prevent blocking the consumer


if __name__ == "__main__":
    run()
