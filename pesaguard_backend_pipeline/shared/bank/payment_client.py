"""Outbound bank transfer helpers for sending settlement requests."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("pesaguard.bank_payment")


class BankPaymentClient:
    """Create and fire bank transfer requests using the tenant credentials."""

    def __init__(self, tenant_id: str, credentials: Optional[Dict[str, Any]] = None, session: Optional[Any] = None):
        self.tenant_id = tenant_id or "default"
        self.credentials = credentials or {}
        self.session = session

    def build_transfer_payload(
        self,
        amount: float,
        currency: str,
        reference: str,
        account_number: str,
        bank_name: str,
        narration: str = "",
        **extra: Any,
    ) -> Dict[str, Any]:
        payload = {
            "amount": float(amount),
            "currency": str(currency or "KES").upper(),
            "reference": str(reference or ""),
            "account_number": str(account_number or ""),
            "bank_name": str(bank_name or ""),
            "narration": str(narration or "PesaGuard bank transfer"),
        }
        if self.credentials.get("partner_code"):
            payload["partner_code"] = str(self.credentials["partner_code"])
        payload.update(extra)
        return payload

    def request_payment(
        self,
        amount: float,
        currency: str,
        reference: str,
        account_number: str,
        bank_name: str,
        narration: str = "",
        **extra: Any,
    ) -> Dict[str, Any]:
        if self.session is None:
            import requests
            self.session = requests.Session()

        payload = self.build_transfer_payload(
            amount=amount,
            currency=currency,
            reference=reference,
            account_number=account_number,
            bank_name=bank_name,
            narration=narration,
            **extra,
        )

        base_url = str(self.credentials.get("base_url", "https://api.bank.example")).rstrip("/")
        url = f"{base_url}/api/v1/transfers"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-API-Key": str(self.credentials.get("api_key", "")),
            "X-API-Secret": str(self.credentials.get("api_secret", "")),
        }

        response = self.session.request(
            method="POST",
            url=url,
            json=payload,
            headers=headers,
            timeout=15,
        )

        if response.status_code not in (200, 201, 202):
            raise RuntimeError(f"Bank payment request failed [{response.status_code}]: {response.text}")

        body = response.json() if hasattr(response, "json") else {}
        logger.info("Bank payment request accepted for tenant=%s reference=%s", self.tenant_id, reference)
        return body
