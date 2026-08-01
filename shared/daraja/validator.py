from __future__ import annotations

import base64
import hashlib
import hmac
from typing import Optional


_HEX_CHARS = set("0123456789abcdefABCDEF")


def compute_hmac(secret: str, body: bytes) -> bytes:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()


def _strip_prefix(signature: str) -> str:
    value = (signature or "").strip()
    if "=" in value:
        prefix, remainder = value.split("=", 1)
        if prefix.lower().startswith("sha"):
            value = remainder
    return value.strip()


def _decode_hex(candidate: str) -> Optional[bytes]:
    if not candidate or len(candidate) % 2 != 0:
        return None
    if any(ch not in _HEX_CHARS for ch in candidate):
        return None
    try:
        return bytes.fromhex(candidate)
    except ValueError:
        return None


def _decode_base64(candidate: str) -> Optional[bytes]:
    try:
        padding = "=" * ((4 - len(candidate) % 4) % 4)
        return base64.b64decode(candidate + padding, validate=True)
    except Exception:
        return None


def validate_signature(secret: str, body: bytes, signature: str) -> bool:
    expected = compute_hmac(secret, body)
    normalized = _strip_prefix(signature)

    hex_bytes = _decode_hex(normalized)
    if hex_bytes is not None:
        return hmac.compare_digest(hex_bytes, expected)

    b64_bytes = _decode_base64(normalized)
    if b64_bytes is not None:
        return hmac.compare_digest(b64_bytes, expected)

    return False


def validate_daraja_callback(body: bytes, signature: str, consumer_secret: str) -> bool:
    return validate_signature(consumer_secret, body, signature)
