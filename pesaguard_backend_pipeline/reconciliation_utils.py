"""Reusable normalization and matching helpers for reconciliation flows."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Sequence


def parse_daraja_time(value: Any) -> Optional[datetime]:
    """Parse Daraja (YYYYMMDDHHMMSS) or ISO-8601 timestamps into UTC."""
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    text = str(value).strip()
    if len(text) == 14 and text.isdigit():
        try:
            return datetime.strptime(text, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        except ValueError:
            return None

    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _get_reference(event: Dict[str, Any]) -> str:
    for key in ("BillRefNumber", "reference", "AccountReference", "invoice_number"):
        val = event.get(key)
        if val not in (None, ""):
            return str(val).strip()
    return ""


def _get_amount(event: Dict[str, Any]) -> Optional[float]:
    for key in ("TransAmount", "amount", "Amount"):
        val = event.get(key)
        if val in (None, ""):
            continue
        try:
            return float(val)
        except (TypeError, ValueError):
            return None
    return None


def _get_timestamp(event: Dict[str, Any]) -> Optional[datetime]:
    for key in ("TransTime", "trans_time", "timestamp", "TransactionDate"):
        parsed = parse_daraja_time(event.get(key))
        if parsed is not None:
            return parsed
    return None


def normalize_daraja_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Extract canonical transaction keys from flat or nested callback payloads."""
    normalized: Dict[str, Any] = {}
    if not isinstance(event, dict):
        return normalized

    callback = (
        event.get("Body", {}).get("stkCallback", {})
        if isinstance(event.get("Body"), dict)
        else {}
    )
    metadata_items = callback.get("CallbackMetadata", {}).get("Item", []) if isinstance(callback, dict) else []
    metadata = {
        item.get("Name"): item.get("Value")
        for item in metadata_items
        if isinstance(item, dict) and item.get("Name")
    }

    trans_id = (
        event.get("TransID")
        or event.get("trans_id")
        or metadata.get("MpesaReceiptNumber")
        or callback.get("CheckoutRequestID")
    )
    if trans_id not in (None, ""):
        normalized["trans_id"] = str(trans_id).strip()
        normalized["TransID"] = str(trans_id).strip()

    amount = _get_amount(event)
    if amount is None:
        metadata_amount = metadata.get("Amount")
        if metadata_amount not in (None, ""):
            try:
                amount = float(metadata_amount)
            except (TypeError, ValueError):
                amount = None
    if amount is not None:
        normalized["amount"] = amount
        normalized["TransAmount"] = amount

    phone = event.get("MSISDN") or event.get("phone_number") or metadata.get("PhoneNumber")
    if phone not in (None, ""):
        normalized["phone_number"] = str(phone).strip()
        normalized["MSISDN"] = str(phone).strip()

    timestamp = _get_timestamp(event) or parse_daraja_time(metadata.get("TransactionDate"))
    if timestamp is not None:
        normalized["timestamp"] = timestamp.isoformat()
        normalized["TransTime"] = timestamp.strftime("%Y%m%d%H%M%S")

    reference = _get_reference(event)
    if not reference and metadata.get("AccountReference") not in (None, ""):
        reference = str(metadata.get("AccountReference")).strip()
    if reference:
        normalized["reference"] = reference
        normalized["BillRefNumber"] = reference

    return normalized


def exact_match(event: Dict[str, Any], record: Dict[str, Any]) -> bool:
    event_amount = _get_amount(event)
    record_amount = _get_amount(record)
    if event_amount is None or record_amount is None or event_amount != record_amount:
        return False

    event_ref = _get_reference(event)
    record_ref = _get_reference(record)
    if event_ref and record_ref and event_ref != record_ref:
        return False

    event_phone = str(event.get("MSISDN") or event.get("phone_number") or "").strip()
    record_phone = str(record.get("MSISDN") or record.get("phone_number") or record.get("msisdn") or "").strip()
    if event_phone and record_phone:
        return event_phone == record_phone
    return True


def find_exact_match(event: Dict[str, Any], records: Sequence[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for record in records:
        if exact_match(event, record):
            return record
    return None


def time_window_match(
    event: Dict[str, Any],
    records: Sequence[Dict[str, Any]],
    window_minutes: int = 15,
) -> Optional[Dict[str, Any]]:
    event_ts = _get_timestamp(event)
    if event_ts is None:
        return None

    max_delta = timedelta(minutes=max(window_minutes, 0))
    for record in records:
        record_ts = _get_timestamp(record)
        if record_ts is None:
            continue
        if abs(event_ts - record_ts) <= max_delta:
            return record
    return None
