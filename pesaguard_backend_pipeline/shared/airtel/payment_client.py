"""Outbound Airtel Money payment helpers for sending disbursements and transfers."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("pesaguard.airtel_payment")


class AirtelPaymentClient:
    """Create and fire Airtel Money outbound payment requests using the tenant credentials.

    Airtel Money's merchant API is OAuth2 protected, so every disbursement is sent
    through :class:`AirtelAuthClient`, which attaches the ``Bearer`` token and
    transparently refreshes + retries once on a 401. Sending a payout without a
    token would be rejected by the provider, so missing credentials fail fast here
    rather than producing an unauthenticated money-movement request.
    """

    def __init__(
        self,
        tenant_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        session: Optional[Any] = None,
        auth_client: Optional[Any] = None,
        cache: Optional[Any] = None,
    ):
        self.tenant_id = tenant_id or "default"
        self.credentials = credentials or {}
        self.session = session
        self.cache = cache
        self._auth_client = auth_client

    @property
    def auth_client(self) -> Any:
        """Lazily build the shared OAuth client for this tenant's credentials."""
        if self._auth_client is None:
            from pesaguard_backend_pipeline.shared.airtel.auth_client import AirtelAuthClient

            self._auth_client = AirtelAuthClient(
                tenant_id=self.tenant_id,
                credentials=self.credentials,
                cache=self.cache,
                session=self.session,
            )
            # Reuse the auth client's (retry-configured) session for outbound calls
            # so connection pooling and backoff apply to payments too.
            self.session = self._auth_client.session
        return self._auth_client

    def build_disbursement_payload(
        self,
        amount: float,
        currency: str,
        reference: str,
        msisdn: str,
        description: str = "",
        **extra: Any,
    ) -> Dict[str, Any]:
        """Create a normalized Airtel Money disbursement request payload."""
        normalized_msisdn = str(msisdn or "").replace("+", "").replace(" ", "")
        payload = {
            "amount": float(amount),
            "currency": str(currency or "UGX").upper(),
            "reference": str(reference or ""),
            "msisdn": normalized_msisdn,
            "description": str(description or "PesaGuard payment"),
        }
        payload.update(extra)
        return payload

    def request_payment(
        self,
        amount: float,
        currency: str,
        reference: str,
        msisdn: str,
        description: str = "",
        **extra: Any,
    ) -> Dict[str, Any]:
        """Submit an authenticated payment request to Airtel Money.

        Raises:
            ValueError: if tenant API credentials are absent — the provider cannot
                authorize the call, so no request is sent.
            RuntimeError: if Airtel rejects the disbursement.
        """
        if not self.credentials.get("api_key") or not self.credentials.get("api_secret"):
            # An injected auth_client may carry its own credentials, so only fail
            # fast when we would otherwise have to build an unauthenticated request.
            if self._auth_client is None:
                raise ValueError(
                    f"Missing Airtel API key or secret for tenant={self.tenant_id}; "
                    "refusing to send an unauthenticated payment request"
                )

        payload = self.build_disbursement_payload(
            amount=amount,
            currency=currency,
            reference=reference,
            msisdn=msisdn,
            description=description,
            **extra,
        )

        base_url = str(self.credentials.get("base_url", "https://sandbox.example.com")).rstrip("/")
        url = f"{base_url}/merchant/v1/payments"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Country": str(self.credentials.get("country", "")).upper() or "UG",
            "X-Currency": str(currency or "UGX").upper(),
        }

        auth = self.auth_client
        response = auth.request(
            "POST",
            url,
            json=payload,
            headers=headers,
            timeout=15,
        )

        if response.status_code not in (200, 201, 202):
            raise RuntimeError(f"Airtel payment request failed [{response.status_code}]: {response.text}")

        body = response.json() if hasattr(response, "json") else {}
        logger.info("Airtel payment request accepted for tenant=%s reference=%s", self.tenant_id, reference)
        return body

