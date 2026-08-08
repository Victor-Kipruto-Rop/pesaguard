"""Robust alerting consumer module for routing and processing discrepancy events."""

from __future__ import annotations

import json
import logging
import os
import signal
import sys
from typing import Any, Callable, Dict, List, Optional

try:
    from kafka import KafkaConsumer
except ImportError:
    KafkaConsumer = None  # type: ignore[assignment]

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pesaguard_backend_pipeline.alerting_service import AlertingService
from pesaguard_backend_pipeline.tenant_settings import TenantSettingsStore

logger = logging.getLogger("pesaguard.alerting.consumer")


class AlertingConsumer:
    """Processes discrepancy events from a topic or in-process list and routes them to the alerting service safely."""

    def __init__(
        self,
        alert_service: Any,
        tenant_settings_provider: Optional[Callable[[str], Dict[str, Any]]] = None,
    ):
        self.alert_service = alert_service
        self.tenant_settings_provider = tenant_settings_provider or (lambda _tenant_id: {})

    def process_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch of messages, enriching them with tenant context and routing to alerting."""
        results: List[Dict[str, Any]] = []
        
        if not messages:
            return results

        for message in messages:
            if not isinstance(message, dict):
                logger.error("Invalid message format encountered; expected dictionary, got %s", type(message))
                results.append({"status": "failed", "reason": "invalid_message_format"})
                continue

            trans_id = message.get("trans_id", "unknown")
            tenant_id = str(message.get("tenant_id") or "default")

            try:
                self._apply_tenant_context(message, tenant_id)
                
                if not hasattr(self.alert_service, "handle_discrepancy"):
                    logger.error("Alert service instance missing 'handle_discrepancy' method")
                    results.append({"status": "failed", "trans_id": trans_id, "reason": "misconfigured_alert_service"})
                    continue

                result = self.alert_service.handle_discrepancy(message)
                results.append(result if isinstance(result, dict) else {"status": "success", "result": result})

            except Exception as e:
                logger.exception("Failed to process alerting message for trans_id=%s tenant_id=%s: %s", trans_id, tenant_id, e)
                results.append({"status": "failed", "trans_id": trans_id, "reason": str(e)})

        return results

    def _apply_tenant_context(self, message: Dict[str, Any], tenant_id: str) -> None:
        """Inject tenant-specific configurations, locales, and fallback channels securely."""
        try:
            settings = self.tenant_settings_provider(tenant_id) or {}
        except Exception as e:
            logger.error("Error retrieving tenant settings for tenant_id=%s: %s", tenant_id, e)
            settings = {}

        if "alert_channels" in settings and "alert_channels" not in message:
            message["alert_channels"] = settings["alert_channels"]
        
        message.setdefault("tenant_id", tenant_id)
        message.setdefault("locale", settings.get("preferred_locale", "en"))
        
        logger.info(
            "Processing discrepancy for alerting",
            extra={
                "tenant_id": tenant_id,
                "trans_id": message.get("trans_id"),
                "locale": message.get("locale"),
            },
        )


def _signal_handler(signum, frame):
    logger.info("Received termination signal (%s), shutting down alerting consumer...", signum)
    sys.exit(0)


def run():
    """Run the alerting consumer service against the configured discrepancy topic."""
    if KafkaConsumer is None:
        logger.error("Kafka client dependencies unavailable. Alerting consumer cannot start.")
        sys.exit(1)

    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic = os.getenv("PESAGUARD_TOPIC_DISCREPANCIES", "mpesa.discrepancies")
    group_id = os.getenv("PESAGUARD_ALERTING_GROUP_ID", "pesaguard-alerting-v1")
    db_url = os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")

    engine = create_engine(db_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    settings_store = TenantSettingsStore()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        group_id=group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )

    logger.info("Alerting consumer started and listening on topic=%s", topic)

    for message in consumer:
        try:
            payload = message.value
            if not isinstance(payload, dict):
                logger.warning("Skipping invalid discrepancy message payload type=%s", type(payload))
                consumer.commit(message=message)
                continue

            tenant_id = str(payload.get("tenant_id") or "default")
            if "alert_channels" not in payload:
                tenant_settings = settings_store.get(tenant_id)
                payload["alert_channels"] = tenant_settings.get("alert_channels")

            alert_service = AlertingService(
                session_factory=SessionLocal,
                tenant_settings=settings_store.get(tenant_id),
            )
            consumer_response = alert_service.handle_discrepancy(payload)
            logger.info("Alerting result for trans_id=%s: %s", payload.get("trans_id"), consumer_response)
            consumer.commit(message=message)
        except Exception as exc:
            logger.exception("Unhandled exception in alerting consumer loop: %s", exc)


if __name__ == "__main__":
    run()
