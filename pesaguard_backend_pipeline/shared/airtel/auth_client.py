"""
Airtel Money API Authentication Client for PesaGuard.

Manages Airtel OAuth-style token generation, secure thread-safe caching,
and authorized API request dispatching with multi-tenant credential isolation.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("pesaguard.airtel_auth")


class AirtelAuthClient:
    """Fetch, cache, and refresh Airtel Money access tokens securely and robustly."""

    def __init__(
        self,
        tenant_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        cache: Optional[Any] = None,
        session: Optional[requests.Session | Any] = None,
    ):
        self.tenant_id = tenant_id or "default"
        self.credentials = credentials or {}
        self.cache = cache
        self._token_cache_key = f"pesaguard:airtel:token:{self.tenant_id}"
        self._last_token: Optional[str] = None
        self._lock = threading.Lock()

        if session is not None:
            self.session = session
        else:
            self.session = requests.Session()
            retries = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[502, 503, 504],
                raise_on_status=False,
            )
            adapter = HTTPAdapter(max_retries=retries)
            self.session.mount("https://", adapter)

    def get_access_token(self) -> str:
        """Retrieve a valid access token from cache or fetch a new one with thread safety."""
        cached = self._read_cache()
        if cached:
            return cached

        with self._lock:
            cached = self._read_cache()
            if cached:
                return cached

            payload = self._call_fetcher()
            token = payload.get("access_token", "") if isinstance(payload, dict) else str(payload)
            if not token:
                logger.error("Airtel authentication payload missing 'access_token' for tenant=%s", self.tenant_id)
                raise RuntimeError("Airtel authentication response missing 'access_token'")

            self._write_cache(token, ttl=3300)
            logger.info("Successfully acquired and cached Airtel access token for tenant=%s", self.tenant_id)
            return token

    def _call_fetcher(self) -> Any:
        """Invoke the token fetcher method handling different signature variants."""
        for call in (
            lambda: self._fetch_access_token(self, self),
            lambda: self._fetch_access_token(self),
            lambda: self._fetch_access_token(),
        ):
            try:
                return call()
            except TypeError:
                continue
        raise RuntimeError("Airtel auth fetcher could not be successfully invoked due to signature mismatch.")

    def _read_cache(self) -> Optional[str]:
        """Read token from external cache backend or in-memory fallback."""
        if self.cache is None:
            return self._last_token
        try:
            value = self.cache.get(self._token_cache_key)
            if not value:
                return None
            if isinstance(value, dict):
                if "value" in value:
                    return str(value.get("value"))
                if "token" in value:
                    return str(value.get("token"))
                return None
            return str(value)
        except Exception as exc:
            logger.warning("Failed to read token from cache for tenant=%s: %s", self.tenant_id, exc)
            return self._last_token

    def _write_cache(self, token: str, ttl: int) -> None:
        """Write token to cache backend or in-memory fallback with TTL."""
        self._last_token = token
        if self.cache is None:
            return
        try:
            if hasattr(self.cache, "setex"):
                self.cache.setex(self._token_cache_key, ttl, token)
                return

            if hasattr(self.cache, "set"):
                try:
                    self.cache.set(self._token_cache_key, token, ttl)
                except TypeError:
                    self.cache.set(self._token_cache_key, {"value": token}, ttl)
                return
        except Exception as exc:
            logger.error("Failed to write token to cache for tenant=%s: %s", self.tenant_id, exc)

    def _fetch_access_token(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Call Airtel Money OAuth endpoint to generate a new access token."""
        base_url = self.credentials.get("base_url", "https://sandbox.example.com").rstrip("/")
        auth_url = f"{base_url}/auth/oauth2/token"
        api_key = self.credentials.get("api_key", "")
        api_secret = self.credentials.get("api_secret", "")

        if not api_key or not api_secret:
            raise ValueError(f"Missing Airtel API key or secret for tenant={self.tenant_id}")

        response = self.session.post(
            auth_url,
            auth=(api_key, api_secret),
            timeout=10,
            headers={"Accept": "application/json"},
        )

        if response.status_code == 401:
            logger.warning("Airtel auth returned 401 for tenant=%s. Retrying once...", self.tenant_id)
            time.sleep(0.5)
            retry_response = self.session.post(
                auth_url,
                auth=(api_key, api_secret),
                timeout=10,
                headers={"Accept": "application/json"},
            )
            if retry_response.status_code == 200:
                return retry_response.json()
            raise RuntimeError(
                f"Airtel authentication failed after retry with status {retry_response.status_code}: {retry_response.text}"
            )

        if response.status_code != 200:
            raise RuntimeError(f"Airtel authentication failed with status {response.status_code}: {response.text}")

        return response.json()

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        """Execute an authenticated HTTP request against Airtel APIs, handling token expiration."""
        token = self.get_access_token()
        headers = kwargs.pop("headers", {})
        headers.setdefault("Authorization", f"Bearer {token}")

        response = self.session.request(method=method, url=url, headers=headers, **kwargs)

        if response.status_code == 401:
            logger.warning("Airtel API request returned 401 for tenant=%s. Forcing token refresh and retrying...", self.tenant_id)
            with self._lock:
                if self.cache is not None:
                    try:
                        self.cache.delete(self._token_cache_key)
                    except Exception:
                        pass
                self._last_token = None

                refreshed_payload = self._fetch_access_token()
                refreshed_token = refreshed_payload.get("access_token", "") if isinstance(refreshed_payload, dict) else str(refreshed_payload)

                if refreshed_token:
                    self._write_cache(refreshed_token, ttl=3300)
                    headers["Authorization"] = f"Bearer {refreshed_token}"
                    response = self.session.request(method=method, url=url, headers=headers, **kwargs)

        return response
