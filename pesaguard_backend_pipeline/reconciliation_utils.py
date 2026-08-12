from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Sequence


def parse_daraja_time(value: Any) -> Optional[datetime]:
    if not value:
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
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _coerce_amount(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        coerced = float(value)
        return None if math.isnan(coerced) else coerced
    except (TypeError, ValueError):
        return None


def extract_amount(payload: Dict[str, Any]) -> Optional[float]:
    return _coerce_amount(
        payload.get("TransAmount")
        or payload.get("amount")
        or payload.get("Amount")
        or payload.get("amount_paid")
    )


def extract_reference(payload: Dict[str, Any]) -> str:
    return str(
        payload.get("TransID")
        or payload.get("trans_id")
        or payload.get("internal_ref")
        or payload.get("reference")
        or ""
    ).strip()


def normalize_daraja_event(event: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "trans_id": extract_reference(event),
        "amount": extract_amount(event),
        "phone_number": str(event.get("MSISDN") or event.get("phone_number") or event.get("msisdn") or "").strip(),
        "timestamp": parse_daraja_time(event.get("TransTime") or event.get("timestamp") or event.get("created_at")),
        "raw": event,
    }


def _normalize_internal_record(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "internal_ref": str(record.get("internal_ref") or record.get("reference") or "").strip(),
        "amount": _coerce_amount(record.get("amount") or record.get("Amount") or record.get("TransAmount")),
        "phone_number": str(record.get("phone_number") or record.get("MSISDN") or record.get("msisdn") or "").strip(),
        "timestamp": parse_daraja_time(record.get("timestamp") or record.get("synced_at") or record.get("created_at") or record.get("TransTime")),
        "raw": record,
    }


def exact_match(normalized_event: Dict[str, Any], normalized_record: Dict[str, Any], tolerance_percent: float = 0.0) -> bool:
    event_amount = normalized_event.get("amount")
    record_amount = normalized_record.get("amount")
    if event_amount is None or record_amount is None:
        return False

    phone = str(normalized_event.get("phone_number") or "").strip()
    record_phone = str(normalized_record.get("phone_number") or "").strip()
    if not phone or phone != record_phone:
        return False

    allowed_delta = max(0.01, abs(float(event_amount)) * (float(tolerance_percent) / 100.0)) if float(tolerance_percent) > 0 else 0.0
    return abs(float(record_amount) - float(event_amount)) <= allowed_delta


def find_exact_match(
    normalized_event: Dict[str, Any],
    internal_records: Sequence[Dict[str, Any]],
    tolerance_percent: float = 0.0,
) -> Optional[Dict[str, Any]]:
    event_time = normalized_event.get("timestamp")
    best_match: Optional[Dict[str, Any]] = None

    for record in internal_records:
        normalized_record = _normalize_internal_record(record)
        if not exact_match(normalized_event, normalized_record, tolerance_percent=tolerance_percent):
            continue

        latency = 0
        if event_time is not None and normalized_record.get("timestamp") is not None:
            latency = int(abs((event_time - normalized_record["timestamp"]).total_seconds()))

        amount_diff = abs(float(normalized_record["amount"]) - float(normalized_event["amount"]))
        match_type = "exact" if amount_diff == 0 else "fuzzy_exact"
        candidate = {
            "match_type": match_type,
            "internal_ref": normalized_record.get("internal_ref"),
            "record": record,
            "latency_seconds": latency,
            "amount_diff": amount_diff,
        }

        if best_match is None:
            best_match = candidate
            continue

        if (candidate["latency_seconds"], candidate["amount_diff"]) < (
            best_match["latency_seconds"],
            best_match["amount_diff"],
        ):
            best_match = candidate

    return best_match


def time_window_match(
    normalized_event: Dict[str, Any],
    internal_records: Sequence[Dict[str, Any]],
    window_minutes: int = 15,
    tolerance_percent: float = 0.5,
    allow_partial: bool = True,
) -> Optional[Dict[str, Any]]:
    amount = normalized_event.get("amount")
    if amount is None or amount <= 0:
        return None

    event_time = normalized_event.get("timestamp")
    phone = str(normalized_event.get("phone_number") or "").strip()
    allowed_delta = max(0.01, abs(float(amount)) * (float(tolerance_percent) / 100.0))

    candidates = []
    for record in internal_records:
        normalized_record = _normalize_internal_record(record)
        record_amount = normalized_record.get("amount")
        if record_amount is None:
            continue

        latency = 0
        record_time = normalized_record.get("timestamp")
        if event_time is not None and record_time is not None:
            latency = int(abs((event_time - record_time).total_seconds()))
            if latency > max(0, int(window_minutes)) * 60:
                continue

        amt_diff = abs(float(record_amount) - float(amount))
        if amt_diff > allowed_delta:
            continue

        record_phone = str(normalized_record.get("phone_number") or "").strip()
        phone_matches = bool(phone) and phone == record_phone

        if phone_matches and amt_diff == 0:
            match_type = "exact"
        elif phone_matches:
            match_type = "fuzzy_exact"
        elif allow_partial:
            match_type = "partial_fuzzy" if amt_diff <= allowed_delta else "partial"
        else:
            continue

        candidates.append(
            {
                "match_type": match_type,
                "internal_ref": normalized_record.get("internal_ref"),
                "record": record,
                "latency_seconds": latency,
                "amount_diff": amt_diff,
            }
        )

    if not candidates:
        return None

    priority = {"exact": 0, "fuzzy_exact": 1, "partial_fuzzy": 2, "partial": 3}
    candidates.sort(
        key=lambda item: (
            priority.get(item["match_type"], 99),
            item["latency_seconds"],
            item["amount_diff"],
        )
    )
    return candidates[0]
