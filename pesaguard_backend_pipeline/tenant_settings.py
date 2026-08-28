"""Minimal tenant settings compatibility layer for tests and runtime imports."""

from __future__ import annotations

import json
import os
import tempfile
from typing import Any, Dict, Optional

from pesaguard_backend_pipeline.localization_utils import normalise_locale


class TenantSettingsStore:
    """Load and merge tenant configuration from a JSON file or in-memory overrides."""

    def __init__(self, path: Optional[str] = None):
        default_path = os.path.join(os.path.dirname(__file__), "tenant_settings.json")
        self.path = path or os.getenv("TENANT_SETTINGS_FILE", default_path)
        self._data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
                if isinstance(data, dict):
                    return data
        except Exception:
            return {}
        return {}

    def get(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        tenant_id = tenant_id or "default"
        data = self._data.get(tenant_id) if isinstance(self._data, dict) else {}
        if isinstance(data, dict):
            return data
        return {}

    def get_residency_context(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        return {"tenant_id": tenant_id or "default", "compliant": True}

    def resolve_locale(self, tenant_id: Optional[str] = None, user_id: Optional[str] = None, fallback_locale: str = "en") -> str:
        """Resolve a tenant/user locale with support for the older API used by tests and callers."""
        tenant_settings = self.get(tenant_id or "default")
        if not isinstance(tenant_settings, dict):
            return fallback_locale

        user_overrides = tenant_settings.get("user_locale_overrides") or {}
        if user_id and isinstance(user_overrides, dict):
            override = user_overrides.get(str(user_id)) or user_overrides.get(user_id)
            if override:
                return normalise_locale(str(override))

        if user_id and tenant_settings.get("user_locales"):
            override = tenant_settings.get("user_locales", {}).get(str(user_id)) or tenant_settings.get("user_locales", {}).get(user_id)
            if override:
                return normalise_locale(str(override))

        locale = tenant_settings.get("preferred_locale") or tenant_settings.get("locale")
        if locale:
            return normalise_locale(str(locale))

        return str(fallback_locale)

    def update(self, tenant_id: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        tenant_id = tenant_id or "default"
        payload = payload or {}
        current = self.get(tenant_id)
        updated = dict(current)

        if "preferred_locale" in payload:
            updated["preferred_locale"] = normalise_locale(str(payload["preferred_locale"]))
        if "locale" in payload:
            updated["locale"] = normalise_locale(str(payload["locale"]))
        if "user_locale_overrides" in payload and isinstance(payload["user_locale_overrides"], dict):
            updated["user_locale_overrides"] = {
                str(key): normalise_locale(str(value)) if value is not None else value
                for key, value in payload["user_locale_overrides"].items()
            }

        for key, value in payload.items():
            if key not in {"preferred_locale", "locale", "user_locale_overrides"}:
                if isinstance(value, dict) and isinstance(updated.get(key), dict):
                    merged = dict(updated.get(key, {}))
                    merged.update(value)
                    updated[key] = merged
                else:
                    updated[key] = value

        self._data[tenant_id] = updated
        self._persist()
        return updated

    def _persist(self) -> None:
        """Persist settings atomically so account preferences survive restarts."""
        directory = os.path.dirname(os.path.abspath(self.path))
        try:
            os.makedirs(directory, exist_ok=True)
            fd, temp_path = tempfile.mkstemp(prefix=".tenant_settings_", suffix=".json", dir=directory)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self._data, handle, indent=2, sort_keys=True)
                handle.write("\n")
            os.replace(temp_path, self.path)
        except OSError:
            # Keep the in-memory update available for the current process. A
            # read-only deployment should not make account pages unavailable.
            try:
                if "temp_path" in locals() and os.path.exists(temp_path):
                    os.unlink(temp_path)
            except OSError:
                pass


__all__ = ["TenantSettingsStore", "normalise_locale"]
