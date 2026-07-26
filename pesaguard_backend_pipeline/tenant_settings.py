"""Tenant-level settings and admin configuration helpers."""

import json
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional

from localization_utils import normalise_locale

logger = logging.getLogger("pesaguard.tenant_settings")

try:
    import fcntl  # POSIX only — this deployment targets Linux
    _HAS_FCNTL = True
except ImportError:  # pragma: no cover - non-POSIX environments
    _HAS_FCNTL = False


class TenantSettingsStore:
    """Small JSON-file-backed settings store for pilot tenants.

    NOTE: this is a file-based store used by multiple independent
    processes (webhook receiver, dashboard API, reconciliation job,
    background tasks — each constructs its own TenantSettingsStore
    instance). See the locking/reload logic in update() below for why that
    matters and what's done about it. For anything beyond a single pilot
    customer at low write volume, this should move to a real database
    table — the locking here reduces the risk of lost updates, but a
    JSON file is still a much weaker concurrency primitive than a DB row,
    and every write still means every process reads and rewrites the
    entire file rather than touching just the changed tenant.
    """

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

    def _save_locked(self) -> None:
        """Write self._data to disk atomically.

        FIXED: previously `open(self.path, "w")` truncated the file
        immediately on open, before json.dump() had written anything — a
        crash mid-write left tenant_settings.json empty or partially
        written, and every subsequent _load() anywhere in the codebase
        would raise on json.load(), breaking settings retrieval for EVERY
        tenant process-wide. Now writes to a temp file in the same
        directory first, then atomically renames it over the real path
        (os.replace is atomic on POSIX) — a crash mid-write leaves the
        original file untouched.
        """
        directory = os.path.dirname(os.path.abspath(self.path)) or "."
        fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".tenant_settings_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self._data, handle, indent=2)
            os.replace(tmp_path, self.path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def save(self) -> None:
        """Public save — kept for compatibility with existing callers that
        don't go through update(). Prefer update() when possible, since it
        also does the reload-before-merge that prevents lost updates across
        processes; a bare save() here still only protects against file
        corruption, not against another process's concurrent change.
        """
        self._save_locked()

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

    def list_tenant_ids(self, include_default: bool = False) -> List[str]:
        """Return all known tenant IDs.

        Added: nothing exposed this previously — a caller (background_tasks.py's
        generate_reports()) was reaching directly into the private `_data`
        attribute instead, which broke silently on any internal refactor.

        "default" is the fallback/template entry, not a real tenant, so it's
        excluded by default — pass include_default=True if you specifically
        need it (e.g. an admin tool inspecting the template itself).
        """
        keys = list(self._data.keys())
        if not include_default:
            keys = [k for k in keys if k != "default"]
        return keys

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
        """Update a tenant's settings.

        FIXED: this previously merged the new payload into self._data — an
        in-memory snapshot loaded once when THIS instance was constructed —
        then overwrote the entire file with that snapshot. Since multiple
        independent processes each hold their own TenantSettingsStore
        instance (webhook receiver, dashboard API, reconciliation job,
        background tasks all construct one), two processes updating
        DIFFERENT tenants around the same time would race: whichever one's
        save() ran last would overwrite the whole file with only its own
        view, silently discarding the other process's change — including,
        potentially, a compliance-relevant field like
        cross_border_transfer_allowed.

        Now: uses a file lock around a read-reload-merge-write cycle, so a
        concurrent writer's changes (already on disk) are picked up before
        this update is applied and saved, rather than blindly overwritten.
        This does not eliminate the JSON-file-as-datastore limitation
        entirely (see the class docstring) but it closes the specific lost-
        update race.
        """
        if not _HAS_FCNTL:
            # Best-effort on non-POSIX platforms — reload before merging,
            # which narrows the race window even without a real lock.
            return self._update_unlocked(tenant_id, payload)

        lock_path = f"{self.path}.lock"
        with open(lock_path, "w") as lock_handle:
            fcntl.flock(lock_handle, fcntl.LOCK_EX)
            try:
                return self._update_unlocked(tenant_id, payload)
            finally:
                fcntl.flock(lock_handle, fcntl.LOCK_UN)

    def _update_unlocked(self, tenant_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Reload from disk first — picks up any change another process
        # already committed since this instance was constructed or last
        # updated, so this update merges against current reality instead of
        # a potentially stale in-memory snapshot.
        try:
            self._data = self._load()
        except (json.JSONDecodeError, OSError):
            logger.exception(
                "Failed to reload tenant_settings before update for tenant=%s — "
                "proceeding with in-memory data, which may be stale.",
                tenant_id,
            )

        existing = self._data.get(tenant_id, {})
        merged = dict(existing)
        normalized_payload = self._normalize_payload(payload)
        for key, value in normalized_payload.items():
            if isinstance(value, dict) and isinstance(existing.get(key), dict):
                merged[key] = {**existing[key], **value}
            else:
                merged[key] = value
        self._data[tenant_id] = merged
        self._save_locked()
        return self.get(tenant_id)
