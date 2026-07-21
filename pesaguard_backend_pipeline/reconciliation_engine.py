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

from event_store import ProcessResult

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

    event_time = _parse_event_time(event.get("TransTime"))
    if event_time:
        latency = (datetime.now(timezone.utc) - event_time).total_seconds()
        if latency > 3600:
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
    amount = _coerce_amount(event.get("TransAmount"))
    if amount is None or amount <= 0:
        return None

    phone = str(event.get("MSISDN", ""))
    event_time = _parse_event_time(event.get("TransTime"))
    allowed_delta = max(0.01, abs(amount) * (float(tolerance_percent) / 100.0))

    candidates = []
    for record in internal_records:
        record_time = _parse_record_time(record.get("timestamp"))
        if record_time is None or event_time is None:
            continue

        latency = int(abs((event_time - record_time).total_seconds()))
        if latency > window_minutes * 60:
            continue

        try:
            record_amount = float(record.get("amount", 0))
        except Exception:
            continue

        amt_diff = abs(record_amount - amount)
        if amt_diff > allowed_delta:
            continue

        phone_matches = str(record.get("phone_number", "")) == phone

        if phone_matches and amt_diff == 0:
            match_type = "exact"
        elif phone_matches and amt_diff <= allowed_delta:
            match_type = "fuzzy_exact"
        elif not phone_matches and allow_partial:
            match_type = "partial_fuzzy" if amt_diff <= allowed_delta else "partial"
        else:
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


def reconcile_with_idempotency(
    event: Dict[str, Any],
    internal_records: Sequence[Dict[str, Any]],
    event_store,
    discrepancy_dao,
    session,
    tenant_id: str = None,
    tenant_settings: Optional[Dict[str, Any]] = None,
    window_minutes: int = 15,
    source_ip: Optional[str] = None,
    signature_verified: bool = False,
) -> Dict[str, Any]:
    """Atomically evaluate and record reconciliation within a SINGLE transaction.

    Both the idempotency ledger write (ProcessedTransaction + Transaction) and the
    reconciliation outcome write (Discrepancy, when applicable) happen on the same
    `session` and commit together exactly once. If either fails, both roll back —
    there is no window where one is persisted and the other is silently lost.

    Returns a dict with at minimum: trans_id, status, severity, anomalies.
    status == "duplicate_ignored" means no reconciliation write happened because
    this trans_id was already processed (either seen before this call, or caught
    by the unique constraint during this call).
    """
    trans_id = str(event.get("TransID", "unknown"))

    # Cheap pre-check outside the transaction — pure optimization to skip evaluation
    # work for callbacks we already know about. NOT the safety guarantee; that's the
    # flush + unique constraint inside mark_processed_in_session below.
    if event_store.already_processed(trans_id):
        logger.info("Idempotency: duplicate trans_id=%s detected before evaluation, skipping", trans_id)
        return {
            "trans_id": trans_id,
            "status": "duplicate_ignored",
            "severity": "info",
            "anomalies": ["duplicate_transaction_id"],
        }

    seen_trans_ids: Set[str] = set()
    evaluation = evaluate_transaction(
        event, internal_records, seen_trans_ids, window_minutes=window_minutes, tenant_settings=tenant_settings,
    )
    evaluation["tenant_id"] = tenant_id
    evaluation["event"] = event

    try:
        # Step 1: attempt the idempotency ledger write on THIS session, not committed yet.
        result = event_store.mark_processed_in_session(
            session,
            event,
            tenant_id=tenant_id,
            source_ip=source_ip,
            signature_verified=signature_verified,
        )

        if result == ProcessResult.DUPLICATE:
            # A concurrent callback for the same trans_id won the race. Roll back
            # anything staged in this session and return a clean duplicate result —
            # crucially, we do this BEFORE writing any Discrepancy record, so we never
            # end up with a discrepancy for a transaction whose ledger write lost the race.
            session.rollback()
            logger.info("Duplicate trans_id=%s caught during idempotency write, skipping reconciliation write", trans_id)
            return {
                "trans_id": trans_id,
                "status": "duplicate_ignored",
                "severity": "info",
                "anomalies": ["duplicate_transaction_id"],
            }

        if result == ProcessResult.ERROR:
            session.rollback()
            raise RuntimeError(f"mark_processed_in_session failed validation for trans_id={trans_id}")

        # Step 2: only now write the reconciliation outcome — same session, same
        # not-yet-committed transaction as the ledger write above.
        if evaluation.get("status") in {"needs_review", "missing_payment"} or evaluation.get("anomalies"):
            if discrepancy_dao:
                disc_id = f"{trans_id}-{evaluation.get('status', 'unknown')}"
                discrepancy_dao.save_discrepancy(
                    session=session,
                    id=disc_id,
                    trans_id=trans_id,
                    tenant_id=tenant_id,
                    anomaly_type=evaluation.get("status", "unknown"),
                    severity=evaluation.get("severity", "warning"),
                    details=evaluation,
                )

        # Step 3: single explicit commit. Ledger write + discrepancy write succeed together.
        session.commit()
        evaluation["duplicate"] = False
        return evaluation

    except Exception:
        logger.exception("Error during atomic reconciliation for trans_id=%s — rolling back both writes", trans_id)
        session.rollback()
        raise

