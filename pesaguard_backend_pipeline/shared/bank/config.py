"""Multi-tenant bank transfer configuration loader for PesaGuard."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger("pesaguard.bank_config")


class BankConfig:
    """Load tenant-specific bank API credentials and routing settings."""

    def __init__(self, tenant_id: Optional[str] = None):
        self.tenant_id = (tenant_id or os.getenv("TENANT_ID", "default")).strip().lower()
        env_prefix = self.tenant_id.upper().replace("-", "_")

        api_key = (
            os.getenv(f"{env_prefix}_BANK_API_KEY")
            or os.getenv("BANK_API_KEY", "")
        )
        api_secret = (
            os.getenv(f"{env_prefix}_BANK_API_SECRET")
            or os.getenv("BANK_API_SECRET", "")
        )
        base_url = (
            os.getenv(f"{env_prefix}_BANK_BASE_URL")
            or os.getenv("BANK_BASE_URL", "https://api.bank.example")
        ).rstrip("/")
        partner_code = (
            os.getenv(f"{env_prefix}_BANK_PARTNER_CODE")
            or os.getenv("BANK_PARTNER_CODE", "")
        )

        self._credentials: Dict[str, Any] = {
            "tenant_id": self.tenant_id,
            "api_key": api_key.strip(),
            "api_secret": api_secret.strip(),
            "base_url": base_url,
            "partner_code": partner_code.strip(),
        }

        if not self._credentials["api_key"] or not self._credentials["api_secret"]:
            logger.warning(
                "Bank credentials incomplete for tenant=%s. API calls may fail until credentials are configured.",
                self.tenant_id,
            )

    def get_credentials(self) -> Dict[str, Any]:
        return dict(self._credentials)

    @property
    def is_configured(self) -> bool:
        return bool(self._credentials.get("api_key") and self._credentials.get("api_secret"))
