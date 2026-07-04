"""
Anomaly detection rules applied to each incoming M-Pesa transaction event.

Keep these as small, independent, named checks so it's easy to see
which rule fired and to tune thresholds per pilot customer.
"""
from typing import Any, Dict, List, Set

# Tune these per-customer based on real transaction patterns
LARGE_AMOUNT_THRESHOLD_KES = 150_000
CALLBACK_DELAY_THRESHOLD_MINUTES = 10


def check_for_anomalies(event: Dict[str, Any], seen_trans_ids: Set[str]) -> List[str]:
    """
    Runs all anomaly checks against a single transaction event.
    Returns a list of human-readable anomaly descriptions (empty if clean).
    """
    anomalies = []

    if _is_duplicate(event, seen_trans_ids):
        anomalies.append("duplicate_transaction_id")

    if _is_unusually_large(event):
        anomalies.append(f"amount_exceeds_threshold_{LARGE_AMOUNT_THRESHOLD_KES}_KES")

    if _has_invalid_amount(event):
        anomalies.append("invalid_or_zero_amount")

    # TODO once internal_sync connector is wired up:
    # - missing_internal_record (M-Pesa says paid, no matching order)
    # - amount_mismatch (M-Pesa amount != internal order amount)
    # - till_number_mismatch

    return anomalies


def _is_duplicate(event: Dict[str, Any], seen_trans_ids: Set[str]) -> bool:
    return event.get("TransID") in seen_trans_ids


def _is_unusually_large(event: Dict[str, Any]) -> bool:
    try:
        return float(event.get("TransAmount", 0)) > LARGE_AMOUNT_THRESHOLD_KES
    except (TypeError, ValueError):
        return False


def _has_invalid_amount(event: Dict[str, Any]) -> bool:
    try:
        return float(event.get("TransAmount", 0)) <= 0
    except (TypeError, ValueError):
        return True
