from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from typing import Any, Optional



def _payload_to_bytes(payload: Any) -> bytes:
    if payload is None:
        return b""
    if isinstance(payload, bytes):
        return payload
    if isinstance(payload, str):
        return payload.encode("utf-8")
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")



def compute_hmac(payload: Any, shared_secret: str, encoding: str = "hex") -> str:
    """Compute HMAC-SHA256 over payload using shared secret."""
    digest = hmac.new(shared_secret.encode("utf-8"), _payload_to_bytes(payload), hashlib.sha256).digest()
    normalized_encoding = str(encoding or "hex").strip().lower()

    if normalized_encoding == "base64":
        return base64.b64encode(digest).decode("utf-8")
    return digest.hex()



def validate_signature(payload: Any, signature: Optional[str], shared_secret: str) -> bool:
    """Validate provided signature against both hex and base64 HMAC-SHA256 encodings."""
    if not signature or not shared_secret:
        return False

    provided = str(signature).strip()
    expected_hex = compute_hmac(payload, shared_secret, encoding="hex")
    expected_b64 = compute_hmac(payload, shared_secret, encoding="base64")

    return hmac.compare_digest(provided, expected_hex) or hmac.compare_digest(provided, expected_b64)



def validate_daraja_callback(payload: Any, signature: Optional[str], shared_secret: Optional[str] = None) -> bool:
    """Validate Daraja callback payload integrity using shared-secret HMAC verification."""
    secret = shared_secret if shared_secret is not None else os.getenv("DARAJA_SHARED_SECRET", "")
    return validate_signature(payload, signature, secret)
