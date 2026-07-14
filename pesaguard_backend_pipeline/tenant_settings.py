"""Tenant-level settings and admin configuration helpers."""

import json
import os
from typing import Any, Dict, Optional

from localization_utils import normalise_locale


class TenantSettingsStore:
    """Very small in-file settings store for pilot tenants."""

    def __init__(self, path: Optional[str] = None):
        self.path = path or os.getenv("TENANT_SETTINGS_FILE", "tenant_settings.json")
        self._data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if not os.path.exists(self.path):
            return {
                "default": {
                    "alert_channels": ["slack"],
                    "thresholds": {"warning": 1000, "critical": 5000},
                    "preferred_locale": "en",
                    "deployment_region": "ke-1",
                    "backup_region": "ke-1",
                    "log_region": "ke-1",
                    "cross_border_transfer_allowed": False,
                }
            }
        with open(self.path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(self._data, handle, indent=2)

    def _normalize_setting_value(self, key: str, value: Any) -> Any:
        if key in {"preferred_locale", "default_locale"} and isinstance(value, str):
            return normalise_locale(value)
        if key == "user_locale_overrides" and isinstance(value, dict):
            return {
                user_id: (normalise_locale(str(locale)) if isinstance(locale, str) else locale)
                for user_id, locale in value.items()
            }
        if isinstance(value, dict):
            return {nested_key: self._normalize_setting_value(nested_key, nested_value) for nested_key, nested_value in value.items()}
        return value

    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {key: self._normalize_setting_value(key, value) for key, value in payload.items()}

    def get(self, tenant_id: str) -> Dict[str, Any]:
        default_settings = self._data.get("default", {})
        tenant_settings = self._data.get(tenant_id, {})
        merged = {**default_settings, **tenant_settings}
        if isinstance(merged.get("preferred_locale"), str):
            merged["preferred_locale"] = normalise_locale(merged["preferred_locale"])
        if isinstance(merged.get("default_locale"), str):
            merged["default_locale"] = normalise_locale(merged["default_locale"])
        return merged

    def resolve_locale(self, tenant_id: str, user_id: Optional[str] = None, fallback_locale: str = "en") -> str:
        tenant_settings = self.get(tenant_id)
        if user_id:
            user_overrides = tenant_settings.get("user_locale_overrides") or {}
            if isinstance(user_overrides, dict):
                override = user_overrides.get(user_id) or user_overrides.get(str(user_id))
                if override:
                    return normalise_locale(str(override))

        preferred_locale = tenant_settings.get("preferred_locale") or tenant_settings.get("default_locale")
        return normalise_locale(str(preferred_locale or fallback_locale))

    def get_residency_context(self, tenant_id: str) -> Dict[str, Any]:
        tenant_settings = self.get(tenant_id)
        deployment_region = tenant_settings.get("deployment_region") or tenant_settings.get("region") or "ke-1"
        return {
            "deployment_region": deployment_region,
            "backup_region": tenant_settings.get("backup_region") or deployment_region,
            "log_region": tenant_settings.get("log_region") or deployment_region,
            "cross_border_transfer_allowed": bool(tenant_settings.get("cross_border_transfer_allowed", False)),
            "data_residency_note": tenant_settings.get("data_residency_note") or f"Primary data, backups, and logs should stay in {deployment_region}.",
        }

    def update(self, tenant_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        existing = self._data.get(tenant_id, {})
        merged = dict(existing)
        normalized_payload = self._normalize_payload(payload)
        for key, value in normalized_payload.items():
            if isinstance(value, dict) and isinstance(existing.get(key), dict):
                merged[key] = {**existing[key], **value}
            else:
                merged[key] = value
        self._data[tenant_id] = merged
        self.save()
        return self.get(tenant_id)
