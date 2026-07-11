import os
import time
from typing import Any, Dict, Optional

import requests


class DarajaAuthClient:
    """Fetch and cache Daraja access tokens with refresh-on-expiry support."""

    def __init__(self, tenant_id: str, credentials: Optional[Dict[str, Any]] = None, cache=None, session=None):
        self.tenant_id = tenant_id
        self.credentials = credentials or {}
        self.cache = cache
        self.session = session or requests
        self._token_cache_key = f"daraja:token:{tenant_id}"
        self._last_token: Optional[str] = None

    def get_access_token(self) -> str:
        cached = self._read_cache()
        if cached:
            return cached

        payload = self._call_fetcher()
        token = payload.get("access_token", "") if isinstance(payload, dict) else str(payload)
        self._write_cache(token, ttl=3300)
        return token

    def _call_fetcher(self) -> Any:
        for call in (
            lambda: self._fetch_access_token(self, self),
            lambda: self._fetch_access_token(self),
            lambda: self._fetch_access_token(),
        ):
            try:
                return call()
            except TypeError:
                continue
        raise RuntimeError("Daraja auth fetcher could not be invoked")

    def _read_cache(self) -> Optional[str]:
        if self.cache is None:
            return self._last_token
        value = self.cache.get(self._token_cache_key)
        if not value:
            return None
        return value.get("value")

    def _write_cache(self, token: str, ttl: int) -> None:
        if self.cache is None:
            self._last_token = token
            return
        self.cache.set(self._token_cache_key, token, ttl)

    def _fetch_access_token(self, client: "DarajaAuthClient" = None) -> Any:
        response = self.session.post(
            f"{self.credentials.get('base_url', 'https://sandbox.safaricom.co.ke')}/oauth/v1/generate?grant_type=client_credentials",
            auth=(self.credentials.get("consumer_key", ""), self.credentials.get("consumer_secret", "")),
            timeout=10,
        )
        if response.status_code == 401:
            retry_response = self.session.post(
                f"{self.credentials.get('base_url', 'https://sandbox.safaricom.co.ke')}/oauth/v1/generate?grant_type=client_credentials",
                auth=(self.credentials.get("consumer_key", ""), self.credentials.get("consumer_secret", "")),
                timeout=10,
            )
            if retry_response.status_code == 200:
                return retry_response.json()
            raise RuntimeError("Daraja auth failed")
        return response.json()

    def request(self, method: str, url: str, **kwargs: Any) -> Any:
        token = self.get_access_token()
        headers = kwargs.pop("headers", {})
        headers.setdefault("Authorization", f"Bearer {token}")
        response = self.session.request(method=method, url=url, headers=headers, **kwargs)
        if response.status_code == 401:
            refreshed_payload = self._fetch_access_token(self)
            refreshed_token = refreshed_payload.get("access_token", "") if isinstance(refreshed_payload, dict) else str(refreshed_payload)
            self._write_cache(refreshed_token, ttl=3300)
            headers["Authorization"] = f"Bearer {self.get_access_token()}"
            response = self.session.request(method=method, url=url, headers=headers, **kwargs)
        return response
