import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models import Discrepancy
from notifier import send_email_alert, send_slack_alert, send_sms_alert

logger = logging.getLogger("pesaguard.alerting.service")


class AlertingService:
    def __init__(self, session: Optional[Session] = None, tenant_settings: Optional[Dict[str, Any]] = None):
        self.session = session
        self.tenant_settings = tenant_settings or {}
        self._alert_ids: set[str] = set()

    def handle_discrepancy(self, discrepancy: Dict[str, Any]) -> Dict[str, Any]:
        alert_id = discrepancy.get("id") or discrepancy.get("trans_id") or str(uuid.uuid4())
        if alert_id in self._alert_ids:
            return {"status": "deduped", "alert_id": alert_id, "deliveries": [], "delivery_mode": "deduped"}

        self._alert_ids.add(alert_id)
        severity = (discrepancy.get("severity") or "warning").lower()
        channels = self._resolve_channels(severity)
        locale = self._resolve_locale(discrepancy)
        deliveries = []
        delivery_mode = self._resolve_delivery_mode(severity, channels)

        if delivery_mode == "digest":
            self._store_delivery_log(alert_id, discrepancy, deliveries)
            return {"status": "queued", "alert_id": alert_id, "deliveries": deliveries, "delivery_mode": "digest"}

        for channel in channels:
            try:
                if channel == "slack":
                    send_slack_alert(discrepancy, locale=locale)
                elif channel == "sms":
                    send_sms_alert(discrepancy, locale=locale)
                elif channel == "email":
                    send_email_alert(discrepancy, locale=locale)
                deliveries.append({"channel": channel, "status": "sent"})
            except Exception as exc:  # noqa: BLE001
                logger.exception("Alert delivery failed", extra={"channel": channel, "alert_id": alert_id})
                deliveries.append({"channel": channel, "status": "failed", "error": str(exc)})

        self._store_delivery_log(alert_id, discrepancy, deliveries)
        return {"status": "queued", "alert_id": alert_id, "deliveries": deliveries, "delivery_mode": delivery_mode}

    def _resolve_channels(self, severity: str) -> List[str]:
        configured = self.tenant_settings.get("alert_channels") or ["slack"]
        if severity == "critical":
            return [channel for channel in configured if channel in {"slack", "sms", "email"}]
        if severity == "warning":
            return [channel for channel in configured if channel == "slack"]
        return []

    def _resolve_delivery_mode(self, severity: str, channels: List[str]) -> str:
        if severity == "info":
            return "digest"
        if channels:
            return "realtime"
        return "digest"

    def _resolve_locale(self, discrepancy: Dict[str, Any]) -> str:
        tenant_id = str(discrepancy.get("tenant_id", "default"))
        user_id = discrepancy.get("user_id")
        if hasattr(self.tenant_settings, "resolve_locale"):
            return self.tenant_settings.resolve_locale(tenant_id, user_id, fallback_locale="en")

        if isinstance(self.tenant_settings, dict):
            tenant_settings = self.tenant_settings.get(tenant_id) or self.tenant_settings.get("default") or {}
            if user_id and isinstance(tenant_settings.get("user_locale_overrides"), dict):
                override = tenant_settings["user_locale_overrides"].get(user_id) or tenant_settings["user_locale_overrides"].get(str(user_id))
                if override:
                    return str(override)

            preferred_locale = tenant_settings.get("preferred_locale") or tenant_settings.get("default_locale")
            if preferred_locale:
                return str(preferred_locale)

            default_settings = self.tenant_settings.get("default") or {}
            if default_settings.get("preferred_locale"):
                return str(default_settings["preferred_locale"])

        return "en"

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
