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
    tenant_settings: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Evaluate one M-Pesa event against a set of internal records.

    tenant_settings: optional dict from TenantSettingsStore to allow per-customer
    reconciliation tuning (tolerance_percent, allow_partial, window_minutes override).
    """
    trans_id = str(event.get("TransID", "unknown"))
    duplicate = trans_id in seen_trans_ids

    anomalies: List[str] = []
    if duplicate:
        anomalies.append("duplicate_transaction_id")

    # Streaming alignment / late arrival detection
    event_time = _parse_event_time(event.get("TransTime"))
    if event_time:
        latency = (datetime.now(timezone.utc) - event_time).total_seconds()
        if latency > 3600:  # 1 hour
            anomalies.append("late_arriving_event")

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

    # Extract reconciliation-specific tuning from tenant settings
    reconciliation_cfg = (tenant_settings or {}).get("reconciliation", {}) if tenant_settings is not None else {}
    tolerance_percent = float(reconciliation_cfg.get("tolerance_percent", 0.5))
    allow_partial = bool(reconciliation_cfg.get("allow_partial", True))
    if reconciliation_cfg.get("window_minutes") is not None:
        try:
            window_minutes = int(reconciliation_cfg.get("window_minutes"))
        except Exception:
            pass

    best_match = _find_best_match(event, internal_records, window_minutes=window_minutes, tolerance_percent=tolerance_percent, allow_partial=allow_partial)
    if best_match is None:
        return {
            "trans_id": trans_id,
            "status": "missing_payment",
            "severity": "critical",
            "duplicate": duplicate,
            "anomalies": anomalies,
            "match": {"match_type": "none", "reason": "no_matching_record"},
        }

    if best_match["match_type"] in {"exact", "fuzzy_exact"}:
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
    tolerance_percent: float = 0.5,
    allow_partial: bool = True,
) -> Optional[Dict[str, Any]]:
    """Find the best matching internal record using configurable tolerance/window.

    tolerance_percent: allowed percentage difference in amount (e.g., 0.5 for 0.5%).
    allow_partial: whether to consider records that match on amount/time but different phone_number.
    """
    amount = _coerce_amount(event.get("TransAmount"))
    if amount is None or amount <= 0:
        return None

    phone = str(event.get("MSISDN", ""))
    event_time = _parse_event_time(event.get("TransTime"))

    # compute allowed delta as either a minimum of 1 cent or configured percent
    allowed_delta = max(0.01, abs(amount) * (float(tolerance_percent) / 100.0))

    candidates = []
    for record in internal_records:
        record_time = _parse_record_time(record.get("timestamp"))
        if record_time is None or event_time is None:
            continue

        latency = int(abs((event_time - record_time).total_seconds()))
        if latency > window_minutes * 60:
            continue

        record_amount = None
        try:
            record_amount = float(record.get("amount", 0))
        except Exception:
            continue

        amt_diff = abs(record_amount - amount)
        if amt_diff > allowed_delta:
            # amount mismatch beyond tolerance
            continue

        phone_matches = str(record.get("phone_number", "")) == phone

        # Determine match type with fuzzy categories
        if phone_matches and amt_diff == 0:
            match_type = "exact"
        elif phone_matches and amt_diff <= allowed_delta:
            match_type = "fuzzy_exact"
        elif not phone_matches and allow_partial:
            # partial match on amount/time but different phone
            match_type = "partial_fuzzy" if amt_diff <= allowed_delta else "partial"
        else:
            # phone mismatch and partials not allowed
            continue

        candidates.append({
            "match_type": match_type,
            "internal_ref": record.get("internal_ref"),
            "record": record,
            "latency_seconds": latency,
            "amount_diff": amt_diff,
        })

    if not candidates:
        return None

    # ranking preference: exact -> fuzzy_exact -> partial_fuzzy -> partial; then lower latency
    priority = {"exact": 0, "fuzzy_exact": 1, "partial_fuzzy": 2, "partial": 3}
    candidates.sort(key=lambda item: (priority.get(item["match_type"], 99), item["latency_seconds"], item.get("amount_diff", 0)))
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
