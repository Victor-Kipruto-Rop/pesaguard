import os
from typing import Any, Dict, Optional


class DarajaConfig:
    """Load per-tenant Daraja credentials from the environment."""

    def __init__(self, tenant_id: Optional[str] = None):
        self.tenant_id = tenant_id or os.getenv("TENANT_ID", "default")
        self.credentials = {
            "consumer_key": os.getenv(f"{self.tenant_id.upper()}_DARJA_CONSUMER_KEY") or os.getenv("DARJA_CONSUMER_KEY", ""),
            "consumer_secret": os.getenv(f"{self.tenant_id.upper()}_DARJA_CONSUMER_SECRET") or os.getenv("DARJA_CONSUMER_SECRET", ""),
            "base_url": os.getenv("DARJA_BASE_URL", "https://sandbox.safaricom.co.ke"),
        }

    def get_credentials(self) -> Dict[str, Any]:
        return dict(self.credentials)
