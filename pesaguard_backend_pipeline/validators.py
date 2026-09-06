"""
Validation & Normalization Helpers for payment provider callbacks.

Supports M-Pesa Daraja webhooks and Airtel Money callbacks, normalizing payloads
for the reconciliation engine across multiple mobile-money providers.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("pesaguard.daraja_validator")

# Flat C2B Callback standard required keys
REQUIRED_C2B_FIELDS = [
    "TransactionType",
    "TransID",
    "TransTime",
    "TransAmount",
    "BusinessShortCode",
    "MSISDN",
]

REQUIRED_AIRTEL_FIELDS = [
    "transactionId",
    "amount",
    "currency",
    "status",
]

# Provider transaction-id aliases, most specific first. Airtel callbacks and M-Pesa
# Daraja callbacks use different key names for the same logical identifier, so both
# the idempotency ledger and the reconciliation engine must resolve them identically.
# Keeping this list here (instead of duplicating it per call site) is what guarantees
# a stable dedupe key across providers.
TRANS_ID_ALIASES = (
    "TransID",
    "trans_id",
    "transactionId",
    "TransactionId",
    "id",
)

# Logical Airtel field -> accepted provider aliases (see docs/AIRTEL_MONEY_INTEGRATION.md).
AIRTEL_FIELD_ALIASES: Dict[str, Tuple[str, ...]] = {
    "transactionId": ("transactionId", "TransactionId", "id"),
    "amount": ("amount", "transactionAmount"),
    "currency": ("currency", "transactionCurrency"),
    "status": ("status", "transactionStatus"),
}


def resolve_trans_id(payload: Any) -> str:
    """Resolve the canonical transaction id from a provider payload.

    Works for both M-Pesa Daraja (``TransID``) and Airtel Money
    (``transactionId``/``TransactionId``/``id``) shapes. Returns an empty string
    when no usable identifier is present so callers can decide how to fail.
    """
    if not isinstance(payload, dict):
        return ""

    for key in TRANS_ID_ALIASES:
        value = payload.get(key)
        if value is None:
            continue
        candidate = str(value).strip()
        if candidate:
            return candidate

    return ""


def _resolve_airtel_field(payload: Dict[str, Any], field: str) -> Any:
    """Return the first present value among a logical field's accepted aliases."""
    for alias in AIRTEL_FIELD_ALIASES.get(field, (field,)):
        if alias in payload and payload[alias] is not None:
            return payload[alias]
    return None


def validate_daraja_payload(payload: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate raw incoming Daraja webhook structure and required fields.

    Args:
        payload: Incoming JSON request body dictionary

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not isinstance(payload, dict):
        return False, "Payload must be a JSON object"

    # 1. Evaluate Nested STK Push Callback Structure
    if "Body" in payload and "stkCallback" in payload["Body"]:
        return _validate_stk_push_callback(payload["Body"]["stkCallback"])

    # 2. Evaluate Nested B2C Callback Structure
    if "Result" in payload:
        return _validate_b2c_callback(payload["Result"])

    # 3. Evaluate Flat C2B PayBill / Till Confirmation Structure
    missing = [f for f in REQUIRED_C2B_FIELDS if f not in payload or payload[f] is None]
    if missing:
        return False, f"Missing required C2B fields: {', '.join(missing)}"

    # Validate TransAmount numerics
    try:
        amt = float(payload["TransAmount"])
        if amt <= 0:
            return False, "TransAmount must be greater than 0"
    except (ValueError, TypeError):
        return False, "TransAmount must be a valid numeric value"

    # Validate TransID non-empty
    trans_id = str(payload.get("TransID", "")).strip()
    if not trans_id:
        return False, "TransID cannot be empty"

    # Validate MSISDN format (12-digit Kenyan phone 2547XXXXXXXX / 2541XXXXXXXX)
    msisdn = str(payload.get("MSISDN", "")).strip()
    if not re.match(r"^254[17]\d{8}$", msisdn):
        return False, f"MSISDN '{msisdn}' must be a valid 12-digit string starting with 254"

    return True, ""


def validate_airtel_payload(payload: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate Airtel Money callback structures used by the gateway SDKs.

    Enforces every field in ``REQUIRED_AIRTEL_FIELDS`` while accepting the
    provider aliases documented in docs/AIRTEL_MONEY_INTEGRATION.md.
    """
    if not isinstance(payload, dict):
        return False, "Payload must be a JSON object"

    missing = [
        field for field in REQUIRED_AIRTEL_FIELDS
        if _resolve_airtel_field(payload, field) in (None, "")
    ]
    if missing:
        return False, f"Airtel callback missing required fields: {', '.join(missing)}"

    trans_id = resolve_trans_id(payload)
    if not trans_id:
        return False, "Airtel callback missing transactionId"

    amount = _resolve_airtel_field(payload, "amount")
    try:
        amount_value = float(amount)
        if amount_value <= 0:
            return False, "amount must be greater than 0"
    except (TypeError, ValueError):
        return False, "amount must be a valid numeric value"

    status = str(_resolve_airtel_field(payload, "status") or "").strip()
    if not status:
        return False, "status is required"

    currency = str(_resolve_airtel_field(payload, "currency") or "").strip()
    if not currency:
        return False, "currency is required"
    if not re.match(r"^[A-Za-z]{3}$", currency):
        return False, f"currency '{currency}' must be a 3-letter ISO-4217 code"

    msisdn = str(payload.get("msisdn") or payload.get("phoneNumber") or payload.get("MSISDN") or "").strip()
    if not msisdn:
        msisdn = str(payload.get("senderMsisdn") or payload.get("customerMsisdn") or "").strip()

    if not msisdn and payload.get("customer"):
        customer = payload.get("customer")
        if isinstance(customer, dict):
            msisdn = str(customer.get("phone") or customer.get("msisdn") or "").strip()

    if msisdn and not re.match(r"^\+?\d{8,15}$", msisdn.replace(" ", "")):
        return False, f"msisdn '{msisdn}' must look like a valid mobile number"

    return True, ""


def extract_canonical_event(payload: Dict[str, Any], tenant_id: str = "default") -> Optional[Dict[str, Any]]:
    """Extract and normalize standard payment fields from diverse provider callback payloads.

    This is the single source of truth for provider normalization: webhook handlers must
    call this instead of building their own canonical dict, so that M-Pesa and Airtel
    events enter the reconciliation pipeline with an identical shape.
    """
    if validate_airtel_payload(payload)[0]:
        trans_id = resolve_trans_id(payload)
        amount = float(_resolve_airtel_field(payload, "amount") or 0)
        msisdn = str(payload.get("msisdn") or payload.get("phoneNumber") or payload.get("senderMsisdn") or payload.get("MSISDN") or "").strip()
        if not msisdn:
            msisdn = str(payload.get("customerMsisdn") or "").strip()
        trans_time = str(payload.get("transactionTime") or payload.get("timestamp") or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"))
        return {
            "tenant_id": tenant_id,
            "TransID": trans_id,
            "TransAmount": amount,
            "MSISDN": msisdn,
            "TransTime": trans_time,
            "BusinessShortCode": str(payload.get("merchantCode") or payload.get("provider") or "AIRTEL"),
            "TransactionType": str(payload.get("transactionType") or "AIRTEL_MONEY"),
            "Currency": str(_resolve_airtel_field(payload, "currency") or "").strip().upper(),
            "payment_channel": "MOBILE_MONEY",
            "provider": "AIRTEL_MONEY",
            "status": str(_resolve_airtel_field(payload, "status") or "success").strip(),
            "raw_payload": payload,
        }

    is_valid, _ = validate_daraja_payload(payload)
    if not is_valid:
        return None

    # Handle Nested STK Push
    if "Body" in payload and "stkCallback" in payload["Body"]:
        stk = payload["Body"]["stkCallback"]
        meta = {item["Name"]: item.get("Value") for item in stk.get("CallbackMetadata", {}).get("Item", []) if "Name" in item}
        
        return {
            "tenant_id": tenant_id,
            "TransID": str(meta.get("MpesaReceiptNumber", stk.get("CheckoutRequestID", "unknown"))).strip(),
            "TransAmount": float(meta.get("Amount", 0)),
            "MSISDN": str(meta.get("PhoneNumber", "")).strip(),
            "TransTime": str(meta.get("TransactionDate", datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"))),
            "BusinessShortCode": str(payload.get("BusinessShortCode", "")),
            "TransactionType": "STK_PUSH",
            "payment_channel": "MOBILE_MONEY",
            "provider": "MPESA",
            "raw_payload": payload,
        }

    # Handle Flat C2B Payload
    return {
        "tenant_id": tenant_id,
        "TransID": str(payload.get("TransID", "")).strip(),
        "TransAmount": float(payload["TransAmount"]),
        "MSISDN": str(payload.get("MSISDN", "")).strip(),
        "TransTime": str(payload.get("TransTime", "")).strip(),
        "BusinessShortCode": str(payload.get("BusinessShortCode", "")).strip(),
        "TransactionType": str(payload.get("TransactionType", "C2B")),
        "BillRefNumber": str(payload.get("BillRefNumber", "")).strip(),
        "payment_channel": "MOBILE_MONEY",
        "provider": "MPESA",
        "raw_payload": payload,
    }


def _validate_stk_push_callback(stk: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate nested STK Push callback envelope."""
    result_code = stk.get("ResultCode")
    if result_code is None:
        return False, "STK Push callback missing ResultCode"

    if int(result_code) != 0:
        return False, f"STK Push cancelled or failed with ResultCode={result_code}: {stk.get('ResultDesc')}"

    meta_items = stk.get("CallbackMetadata", {}).get("Item", [])
    if not meta_items:
        return False, "STK Push callback missing CallbackMetadata items"

    return True, ""


def _validate_b2c_callback(result: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate nested B2C result envelope."""
    result_code = result.get("ResultCode")
    if result_code is None:
        return False, "B2C callback missing ResultCode"

    if int(result_code) != 0:
        return False, f"B2C payment failed with ResultCode={result_code}: {result.get('ResultDesc')}"

    return True, ""
