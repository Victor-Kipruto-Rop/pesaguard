"""Africa's Talking SMS helper for critical alerts (Robust & Production-Ready)."""

import os
import logging
import time
import re
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger("pesaguard.sms")


class AfricasTalkingClient:
    """Robust SMS client for critical operational alerts with retries and normalization."""

    def __init__(
        self,
        username: Optional[str] = None,
        api_key: Optional[str] = None,
        environment: Optional[str] = None,
        max_retries: int = 3,
        timeout_seconds: int = 10,
    ):
        self.username = username or os.getenv("AFRICAS_TALKING_USERNAME", "")
        self.api_key = api_key or os.getenv("AFRICAS_TALKING_API_KEY", "")
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds

        env = environment or os.getenv("AT_ENVIRONMENT", "production").lower()
        if env == "sandbox":
            self.base_url = "https://api.sandbox.africastalking.com/version1/messaging"
        else:
            self.base_url = "https://api.africastalking.com/version1/messaging"

    def _normalize_phone_number(self, phone: str) -> str:
        """
        Normalizes phone numbers to E.164 format (specifically handling Kenyan numbers
        defaulting to +254 if starting with 0 or 7).
        """
        if phone is None:
            return ""
        if not isinstance(phone, str):
            phone = str(phone)

        cleaned = re.sub(r"\s+", "", phone)
        if cleaned.startswith("+"):
            return cleaned
        if cleaned.startswith("0") and len(cleaned) == 10:
            return "+254" + cleaned[1:]
        if cleaned.startswith("7") and len(cleaned) == 9:
            return "+254" + cleaned
        return cleaned

    def send_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        """
        Send an SMS notification with exponential backoff retries, structured response parsing,
        and automatic phone number normalization.
        """
        if not self.username or not self.api_key:
            logger.warning("Africa's Talking SMS skipped: credentials not configured.")
            return {"status": "skipped", "reason": "not_configured"}

        if not to_phone or not message:
            logger.error("Africa's Talking SMS failed: missing recipient phone number or message body.")
            return {"status": "failed", "reason": "invalid_parameters"}

        normalized_phone = self._normalize_phone_number(to_phone)
        payload = {
            "username": self.username,
            "to": normalized_phone,
            "message": message,
        }
        headers = {
            "apiKey": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    data=payload,
                    timeout=self.timeout_seconds,
                )
                
                # Retry on gateway or server errors (5xx)
                if response.status_code >= 500:
                    logger.warning(
                        "Africa's Talking server error (HTTP %s) on attempt %s/%s for %s. Retrying...",
                        response.status_code, attempt, self.max_retries, normalized_phone
                    )
                    last_error = f"HTTP {response.status_code}"
                else:
                    response.raise_for_status()
                    
                    try:
                        data = response.json()
                    except ValueError:
                        data = {"raw_response": response.text}

                    logger.info("Africa's Talking SMS successfully sent to %s on attempt %s", normalized_phone, attempt)
                    return {"status": "sent", "attempts": attempt, "response": data}

            except requests.exceptions.Timeout:
                logger.warning("Africa's Talking SMS timed out on attempt %s/%s for %s", attempt, self.max_retries, normalized_phone)
                last_error = "timeout"
            except requests.exceptions.RequestException as e:
                logger.error("Africa's Talking SMS request failed on attempt %s/%s: %s", attempt, self.max_retries, str(e))
                last_error = str(e)

            if attempt < self.max_retries:
                wait_time = 2 ** (attempt - 1)  # Exponential backoff: 1s, 2s, 4s...
                time.sleep(wait_time)

        logger.error("Africa's Talking SMS failed permanently after %s attempts for %s", self.max_retries, normalized_phone)
        return {"status": "failed", "attempts": self.max_retries, "reason": last_error}
