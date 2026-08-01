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
"""Daraja HMAC signature validator helpers.

Provides:
- compute_hmac(payload, secret, algo="sha256") -> bytes
- validate_signature(header_signature, payload, secret, *, algo="sha256", signature_encoding="hex") -> bool
- validate_daraja_callback(headers, body_bytes, secret, *, header_name="X-MPESA-SIGNATURE", signature_encoding="hex") -> bool

No external dependencies (stdlib only).
"""
from __future__ import annotations
import hmac
import hashlib
import base64
from typing import Optional, Dict


def compute_hmac(payload: bytes, secret: str, algo: str = "sha256") -> bytes:
    """Compute HMAC digest for payload using secret and hashlib algo."""
    if not isinstance(payload, (bytes, bytearray)):
        raise TypeError("payload must be bytes")
    digmod = getattr(hashlib, algo)
    return hmac.new(secret.encode("utf-8"), payload, digmod).digest()


def validate_signature(header_signature: str, payload: bytes, secret: str, *, algo: str = "sha256", signature_encoding: str = "hex") -> bool:
    """Validate header_signature against computed HMAC.

    - signature_encoding: "hex" or "base64"
    """
    if not header_signature:
        return False
    expected = compute_hmac(payload, secret, algo=algo)
    if signature_encoding == "hex":
        expected_repr = expected.hex()
        header_clean = header_signature.lower().strip()
        # Accept common prefixes like "sha256=" and strip them
        if header_clean.startswith("sha256="):
            header_clean = header_clean.split("=", 1)[1]
        try:
            return hmac.compare_digest(header_clean, expected_repr)
        except Exception:
            return False
    elif signature_encoding == "base64":
        expected_b64 = base64.b64encode(expected).decode("ascii")
        header_clean = header_signature.strip()
        return hmac.compare_digest(header_clean, expected_b64)
    else:
        raise ValueError("signature_encoding must be 'hex' or 'base64'")


def validate_daraja_callback(headers: Dict[str, str], body_bytes: bytes, secret: str, *, header_name: str = "X-MPESA-SIGNATURE", signature_encoding: str = "hex") -> bool:
    """Convenience wrapper to validate an incoming HTTP callback.

    - headers: mapping-like object with header names (case-sensitive or lowercased)
    - body_bytes: raw request body bytes
    - secret: shared secret used to generate HMAC
    - header_name: header that contains signature (common: "X-Daraja-Signature" or "X-MPESA-SIGNATURE")
    """
    # Try the canonical name then lowercase variant
    header_value = headers.get(header_name) or headers.get(header_name.lower()) or ""
    return validate_signature(header_value, body_bytes, secret, algo="sha256", signature_encoding=signature_encoding)
