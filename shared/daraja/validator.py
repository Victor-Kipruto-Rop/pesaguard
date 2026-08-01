"""HMAC signature validation helpers for Daraja webhook requests."""

from __future__ import annotations

import base64
import hashlib
import hmac
from typing import Any, Dict


def compute_hmac(payload: bytes, secret: str) -> str:
    """Compute a hex encoded HMAC-SHA256 digest for a request payload."""
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def _normalize_signature(signature: str) -> str:
    value = (signature or "").strip()
    for prefix in ("sha256=", "hmac-sha256=", "sha256:"):
        if value.lower().startswith(prefix):
            return value[len(prefix):].strip()
    return value


def validate_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Validate a Daraja webhook signature in hex or base64 encoding."""
    normalized = _normalize_signature(signature)
    if not normalized or not secret:
        return False

    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).digest()
    expected_hex = digest.hex()
    if hmac.compare_digest(normalized.lower(), expected_hex.lower()):
        return True

    expected_b64 = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(normalized, expected_b64)


def validate_daraja_callback(payload: bytes, headers: Dict[str, Any], secret: str) -> bool:
    """Validate callback signature from common Daraja signature headers."""
    if not headers:
        return False

    candidate_headers = (
        "X-Daraja-Signature",
        "X-Daraja-HMAC-Signature",
        "X-Signature",
        "X-Hub-Signature-256",
    )
    signature = next((headers.get(name) for name in candidate_headers if headers.get(name)), None)
    if signature is None:
        return False
    return validate_signature(payload, str(signature), secret)
