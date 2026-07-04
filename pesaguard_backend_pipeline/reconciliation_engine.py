"""
Reconciliation engine for matching Daraja callbacks to internal ledger records.

This module turns raw webhook events into auditable reconciliation outcomes so
ops teams can distinguish between exact matches, partial matches, missing
payments, and duplicate callbacks.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Set

logger = logging.getLogger("pesaguard.reconciliation_engine")


def evaluate_transaction(
    event: Dict[str, Any],
    internal_records: Sequence[Dict[str, Any]],
    seen_trans_ids: Set[str],
    window_minutes: int = 15,
) -> Dict[str, Any]:
    """Evaluate one M-Pesa event against a set of internal records."""
    trans_id = str(event.get("TransID", "unknown"))
    duplicate = trans_id in seen_trans_ids

    anomalies: List[str] = []
    if duplicate:
        anomalies.append("duplicate_transaction_id")

    amount = _coerce_amount(event.get("TransAmount"))
    if amount is None or amount <= 0:
        anomalies.append("invalid_or_zero_amount")

    if not internal_records:
        return {
            "trans_id": trans_id,
            "status": "missing_payment",
            "severity": "critical",
            "duplicate": duplicate,
            "anomalies": anomalies,
            "match": {"match_type": "none", "reason": "no_internal_record"},
        }

    best_match = _find_best_match(event, internal_records, window_minutes=window_minutes)
    if best_match is None:
        return {
            "trans_id": trans_id,
            "status": "missing_payment",
            "severity": "critical",
            "duplicate": duplicate,
            "anomalies": anomalies,
            "match": {"match_type": "none", "reason": "no_matching_record"},
        }

    if best_match["match_type"] == "exact":
        return {
            "trans_id": trans_id,
            "status": "matched",
            "severity": "info",
            "duplicate": duplicate,
            "anomalies": anomalies,
            "match": best_match,
        }

    return {
        "trans_id": trans_id,
        "status": "needs_review",
        "severity": "warning",
        "duplicate": duplicate,
        "anomalies": anomalies,
        "match": best_match,
    }


def _find_best_match(
    event: Dict[str, Any],
    internal_records: Sequence[Dict[str, Any]],
    window_minutes: int = 15,
) -> Optional[Dict[str, Any]]:
    amount = _coerce_amount(event.get("TransAmount"))
    if amount is None or amount <= 0:
        return None

    phone = str(event.get("MSISDN", ""))
    event_time = _parse_event_time(event.get("TransTime"))

    candidates = []
    for record in internal_records:
        record_time = _parse_record_time(record.get("timestamp"))
        if record_time is None or event_time is None:
            continue

        if abs((event_time - record_time).total_seconds()) > window_minutes * 60:
            continue

        if abs(float(record.get("amount", 0)) - amount) > 0.01:
            continue

        if str(record.get("phone_number", "")) == phone:
            candidates.append({
                "match_type": "exact",
                "internal_ref": record.get("internal_ref"),
                "record": record,
                "latency_seconds": int(abs((event_time - record_time).total_seconds())),
            })
        else:
            candidates.append({
                "match_type": "partial",
                "internal_ref": record.get("internal_ref"),
                "record": record,
                "latency_seconds": int(abs((event_time - record_time).total_seconds())),
            })

    if not candidates:
        return None

    candidates.sort(key=lambda item: (item["match_type"] != "exact", item["latency_seconds"]))
    return candidates[0]


def _coerce_amount(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_event_time(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    text = str(value)
    if len(text) == 14 and text.isdigit():
        return datetime.strptime(text, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_record_time(value: Any) -> Optional[datetime]:
    return _parse_event_time(value)
