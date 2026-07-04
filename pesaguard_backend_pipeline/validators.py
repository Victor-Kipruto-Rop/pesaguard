"""
Validation helpers for M-Pesa Daraja callback payloads.
"""
from typing import Any, Dict, Tuple

REQUIRED_FIELDS = [
    "TransactionType",
    "TransID",
    "TransTime",
    "TransAmount",
    "BusinessShortCode",
    "MSISDN",
]


def validate_daraja_payload(payload: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validates that a Daraja callback payload has the required fields
    and sane types. Returns (is_valid, error_message).
    """
    if not isinstance(payload, dict):
        return False, "Payload must be a JSON object"

    missing = [f for f in REQUIRED_FIELDS if f not in payload]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"

    try:
        float(payload["TransAmount"])
    except (ValueError, TypeError):
        return False, "TransAmount must be numeric"

    if not str(payload["TransID"]).strip():
        return False, "TransID cannot be empty"

    # TODO: add IP allowlist check against Safaricom's published IP ranges
    # TODO: add shared-secret / signature check if your Daraja setup supports it

    return True, ""
