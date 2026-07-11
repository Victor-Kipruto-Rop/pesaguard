"""
Reconciliation Job (MVP version — plain Kafka consumer loop)

For the pilot, this runs as a simple long-lived Python consumer rather
than a full Flink job. Graduate to PyFlink only once transaction volume
or latency requirements justify the added ops complexity.

Logic:
  1. Consume M-Pesa transaction events from `mpesa.transactions.raw`
  2. Look up matching internal record (via connector)
  3. Compare amount, phone number, timing
  4. Emit to `mpesa.transactions.matched` or `mpesa.discrepancies`
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
from tenant_settings import TenantSettingsStore

configure_logging()
logger = logging.getLogger("pesaguard.reconciliation")

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC_RAW = os.getenv("KAFKA_TOPIC_TRANSACTIONS", "mpesa.transactions.raw")
TOPIC_MATCHED = os.getenv("KAFKA_TOPIC_MATCHED", "mpesa.transactions.matched")
TOPIC_DISCREPANCIES = os.getenv("KAFKA_TOPIC_DISCREPANCIES", "mpesa.discrepancies")
TENANT_ID = os.getenv("TENANT_ID", "default")
WINDOW_MINUTES = int(os.getenv("RECONCILIATION_WINDOW_MINUTES", "15"))
settings_store = TenantSettingsStore()


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

    # Simple in-memory dedupe window for the MVP.
    # Replace with a Redis set or DB unique constraint once you have
    # more than a handful of transactions per minute.
    seen_trans_ids = set()
    connector_registry = ConnectorRegistry.from_env()

    for message in consumer:
        event = message.value
        trans_id = event.get("TransID", "unknown")

        anomalies = check_for_anomalies(event, seen_trans_ids)
        seen_trans_ids.add(trans_id)

        connector = connector_registry.get_connector(TENANT_ID)
        internal_records = connector.fetch_recent_records(since_minutes=WINDOW_MINUTES) if connector else []
        evaluation = evaluate_transaction(event, internal_records, seen_trans_ids, window_minutes=WINDOW_MINUTES)
        evaluation["tenant_id"] = TENANT_ID
        evaluation["event"] = event
        evaluation["checked_at"] = datetime.now(timezone.utc).isoformat()
        evaluation["anomalies"] = anomalies + evaluation.get("anomalies", [])
        logger.info("Reconciliation outcome", extra={"tenant_id": TENANT_ID, "trans_id": trans_id, "status": evaluation["status"], "severity": evaluation["severity"]})

        if evaluation["status"] in {"needs_review", "missing_payment"} or anomalies:
            producer.send(TOPIC_DISCREPANCIES, value=evaluation)
            try:
                dispatch_discrepancy_alert(evaluation, tenant_id=TENANT_ID)
            except TypeError:
                dispatch_discrepancy_alert(evaluation)
            logger.warning("Discrepancy flagged for %s: %s", trans_id, evaluation)
        else:
            producer.send(TOPIC_MATCHED, value=evaluation)
            logger.info("Transaction %s reconciled cleanly", trans_id)


if __name__ == "__main__":
    run()
