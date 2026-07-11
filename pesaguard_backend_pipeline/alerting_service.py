import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models import Base, Discrepancy
from notifier import send_slack_alert, send_sms_alert

logger = logging.getLogger("pesaguard.alerting.service")


class AlertingService:
    def __init__(self, session: Optional[Session] = None, tenant_settings: Optional[Dict[str, Any]] = None):
        self.session = session
        self.tenant_settings = tenant_settings or {}
        self._alert_ids: set[str] = set()

    def handle_discrepancy(self, discrepancy: Dict[str, Any]) -> Dict[str, Any]:
        alert_id = discrepancy.get("id") or discrepancy.get("trans_id") or str(uuid.uuid4())
        if alert_id in self._alert_ids:
            return {"status": "deduped", "alert_id": alert_id, "deliveries": []}

        self._alert_ids.add(alert_id)
        severity = (discrepancy.get("severity") or "warning").lower()
        channels = self._resolve_channels(severity)
        deliveries = []
        for channel in channels:
            try:
                if channel == "slack":
                    send_slack_alert(discrepancy)
                elif channel == "sms":
                    send_sms_alert(discrepancy)
                deliveries.append({"channel": channel, "status": "sent"})
            except Exception as exc:  # noqa: BLE001
                logger.exception("Alert delivery failed", extra={"channel": channel, "alert_id": alert_id})
                deliveries.append({"channel": channel, "status": "failed", "error": str(exc)})

        self._store_delivery_log(alert_id, discrepancy, deliveries)
        return {"status": "queued", "alert_id": alert_id, "deliveries": deliveries}

    def _resolve_channels(self, severity: str) -> List[str]:
        configured = self.tenant_settings.get("alert_channels") or ["slack"]
        if severity == "critical":
            return [channel for channel in configured if channel in {"slack", "sms"}]
        if severity == "warning":
            return [channel for channel in configured if channel == "slack"]
        return []

    def _store_delivery_log(self, alert_id: str, discrepancy: Dict[str, Any], deliveries: List[Dict[str, Any]]) -> None:
        if self.session is None:
            return
        self.session.add(
            Discrepancy(
                id=f"alert-{alert_id}",
                trans_id=str(discrepancy.get("trans_id", "unknown")),
                tenant_id=str(discrepancy.get("tenant_id", "default")),
                anomaly_type=str(discrepancy.get("status") or "alert"),
                status="alerted",
                severity=str(discrepancy.get("severity") or "warning"),
                details=json.dumps({"alert_id": alert_id, "deliveries": deliveries}),
                resolved=False,
            )
        )
        self.session.commit()
