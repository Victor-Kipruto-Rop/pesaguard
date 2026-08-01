"""Tenant settings persistence and locale resolution helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional

from localization_utils import normalise_locale


class TenantSettingsStore:
    """Simple JSON-backed tenant settings store."""

    def __init__(self, settings_file: Optional[str] = None):
        default_file = Path(__file__).with_name("tenant_settings.json")
        self.settings_file = Path(
            settings_file
            or os.getenv("TENANT_SETTINGS_FILE")
            or default_file
        )
        self._lock = Lock()
        self._settings: Dict[str, Dict[str, Any]] = self._load()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if not self.settings_file.exists():
            return {}
        try:
            with self.settings_file.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def _persist(self) -> None:
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        with self.settings_file.open("w", encoding="utf-8") as handle:
            json.dump(self._settings, handle, indent=2, sort_keys=True)

    def get(self, tenant_id: str) -> Dict[str, Any]:
        with self._lock:
            default_cfg = dict(self._settings.get("default") or {})
            tenant_cfg = dict(self._settings.get(tenant_id) or {})
            merged = {**default_cfg, **tenant_cfg}
            merged.setdefault("preferred_locale", "en")
            merged["preferred_locale"] = normalise_locale(merged.get("preferred_locale"))
            return merged

    def update(self, tenant_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            tenant_cfg = dict(self._settings.get(tenant_id) or self.get(tenant_id))
            tenant_cfg.update(updates or {})
            if "preferred_locale" in tenant_cfg:
                tenant_cfg["preferred_locale"] = normalise_locale(tenant_cfg.get("preferred_locale"))
            self._settings[tenant_id] = tenant_cfg
            self._persist()
            return dict(tenant_cfg)

    def get_residency_context(self, tenant_id: str) -> Dict[str, Any]:
        settings = self.get(tenant_id)
        return {
            "tenant_id": tenant_id,
            "deployment_region": settings.get("deployment_region"),
            "backup_region": settings.get("backup_region"),
            "log_region": settings.get("log_region"),
            "cross_border_transfer_allowed": bool(settings.get("cross_border_transfer_allowed", False)),
        }

    def resolve_locale(self, tenant_id: str, user_id: Optional[str] = None) -> str:
        settings = self.get(tenant_id)
        if user_id:
            overrides = settings.get("user_locale_overrides")
            if isinstance(overrides, dict):
                override = overrides.get(str(user_id)) or overrides.get(user_id)
                if override:
                    return normalise_locale(override)
        return normalise_locale(settings.get("preferred_locale"))
