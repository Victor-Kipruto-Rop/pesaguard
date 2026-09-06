"""
Multi-Tenant Airtel Money Configuration Loader for PesaGuard.

Loads Airtel API credentials and base URL from tenant-specific environment variables.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger("pesaguard.airtel_config")


class AirtelConfig:
    """Load per-tenant Airtel Money credentials from environment variables securely."""

    def __init__(self, tenant_id: Optional[str] = None):
        self.tenant_id = (tenant_id or os.getenv("TENANT_ID", "default")).strip().lower()
        env_prefix = self.tenant_id.upper().replace("-", "_")

        api_key = (
            os.getenv(f"{env_prefix}_AIRTEL_API_KEY")
            or os.getenv("AIRTEL_API_KEY", "")
        )
        api_secret = (
            os.getenv(f"{env_prefix}_AIRTEL_API_SECRET")
            or os.getenv("AIRTEL_API_SECRET", "")
        )
        base_url = (
            os.getenv(f"{env_prefix}_AIRTEL_BASE_URL")
            or os.getenv("AIRTEL_BASE_URL", "https://sandbox.example.com")
        ).rstrip("/")

        self._credentials: Dict[str, Any] = {
            "tenant_id": self.tenant_id,
            "api_key": api_key.strip(),
            "api_secret": api_secret.strip(),
            "base_url": base_url,
        }

        if not self._credentials["api_key"] or not self._credentials["api_secret"]:
            logger.warning(
                "Airtel credentials incomplete for tenant=%s. API calls may fail until credentials are configured.",
                self.tenant_id,
            )

    def get_credentials(self) -> Dict[str, Any]:
        """Return a copy of the loaded credential dictionary."""
        return dict(self._credentials)

    @property
    def is_configured(self) -> bool:
        """Verify whether essential API keys are present."""
        return bool(self._credentials.get("api_key") and self._credentials.get("api_secret"))
