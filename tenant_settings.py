"""Tenant-level settings and admin configuration helpers."""

import json
import os
from typing import Any, Dict, Optional


class TenantSettingsStore:
    """Very small in-file settings store for pilot tenants."""

    def __init__(self, path: Optional[str] = None):
        self.path = path or os.getenv("TENANT_SETTINGS_FILE", "tenant_settings.json")
        self._data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if not os.path.exists(self.path):
            return {"default": {"alert_channels": ["slack"], "thresholds": {"warning": 1000, "critical": 5000}}}
        with open(self.path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(self._data, handle, indent=2)

    def get(self, tenant_id: str) -> Dict[str, Any]:
        return self._data.get(tenant_id, self._data.get("default", {}))

    def update(self, tenant_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._data[tenant_id] = {**self.get(tenant_id), **payload}
        self.save()
        return self._data[tenant_id]
