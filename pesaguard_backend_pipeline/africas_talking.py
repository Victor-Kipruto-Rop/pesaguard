"""Africa's Talking SMS helper for critical alerts."""

import os
from typing import Any, Dict, Optional

import requests


class AfricasTalkingClient:
    """Minimal SMS client for critical operational alerts."""

    def __init__(self, username: Optional[str] = None, api_key: Optional[str] = None):
        self.username = username or os.getenv("AFRICAS_TALKING_USERNAME", "")
        self.api_key = api_key or os.getenv("AFRICAS_TALKING_API_KEY", "")

    def send_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        if not self.username or not self.api_key:
            return {"status": "skipped", "reason": "not_configured"}

        response = requests.post(
            "https://api.africastalking.com/version1/messaging",
            headers={"apiKey": self.api_key, "Content-Type": "application/x-www-form-urlencoded"},
            data={"username": self.username, "to": to_phone, "message": message},
            timeout=10,
        )
        response.raise_for_status()
        return {"status": "sent", "response": response.text}
