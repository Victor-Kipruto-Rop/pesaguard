import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("pesaguard.alerting.consumer")


class AlertingConsumer:
    """Processes discrepancy events from a topic or in-process list and routes them to the alerting service."""

    def __init__(self, alert_service: Any, tenant_settings_provider: Optional[Callable[[str], Dict[str, Any]]] = None):
        self.alert_service = alert_service
        self.tenant_settings_provider = tenant_settings_provider or (lambda _tenant_id: {})

    def process_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for message in messages:
            tenant_id = str(message.get("tenant_id") or "default")
            self._apply_tenant_context(message, tenant_id)
            result = self.alert_service.handle_discrepancy(message)
            results.append(result)
        return results

    def _apply_tenant_context(self, message: Dict[str, Any], tenant_id: str) -> None:
        settings = self.tenant_settings_provider(tenant_id) or {}
        if "alert_channels" in settings and "alert_channels" not in message:
            message["alert_channels"] = settings["alert_channels"]
        message.setdefault("tenant_id", tenant_id)
        message.setdefault("locale", settings.get("preferred_locale", "en"))
        logger.info("Processing discrepancy for alerting", extra={"tenant_id": tenant_id, "trans_id": message.get("trans_id")})
