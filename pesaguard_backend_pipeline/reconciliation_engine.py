"""
Reconciliation Engine for matching M-Pesa Daraja callbacks to internal ledger records.

Turns raw webhook events into auditable reconciliation outcomes so operational teams
can distinguish between exact matches, partial matches, missing payments, and duplicate callbacks.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Set

from event_store import ProcessResult
from reconciliation_utils import normalize_daraja_event, time_window_match

logger = logging.getLogger("pesaguard.reconciliation_engine")


def evaluate_transaction(
    event: Dict[str, Any],
    internal_records: Sequence[Dict[str, Any]],
    seen_trans_ids: Set[str],
    window_minutes: int = 15,
    tenant_settings: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Evaluate one M-Pesa event against a set of internal records.

    Args:
        event: Daraja callback payload dict
        internal_records: List of internal order/payment dicts
        seen_trans_ids: Set of recently observed transaction IDs
        window_minutes: Default matching time window in minutes
        tenant_settings: Optional tenant-specific settings dict for custom rules

    Returns:
        Structured evaluation outcome dict
    """
    normalized_event = normalize_daraja_event(event)
    trans_id = str(normalized_event.get("trans_id") or "unknown").strip()
    duplicate = trans_id in seen_trans_ids

    anomalies: List[str] = []
    if duplicate:
        anomalies.append("duplicate_transaction_id")

    event_time = normalized_event.get("timestamp")
    if event_time:
        latency = (datetime.now(timezone.utc) - event_time).total_seconds()
        if latency > 3600:
            anomalies.append("late_arriving_event")

    amount = normalized_event.get("amount")
    if amount is None or amount <= 0:
        anomalies.append("invalid_or_zero_amount")

    # Resolve tenant config overrides
    reconciliation_cfg = (tenant_settings or {}).get("reconciliation", {}) if tenant_settings else {}
    tolerance_percent = float(reconciliation_cfg.get("tolerance_percent", 0.5))
    allow_partial = bool(reconciliation_cfg.get("allow_partial", True))
    
    if reconciliation_cfg.get("window_minutes") is not None:
        try:
            window_minutes = int(reconciliation_cfg["window_minutes"])
        except (TypeError, ValueError):
            pass

    if not internal_records:
        return {
            "trans_id": trans_id,
            "status": "missing_payment",
            "severity": "critical",
            "duplicate": duplicate,
            "anomalies": anomalies,
            "match": {"match_type": "none", "reason": "no_internal_records"},
        }

    best_match = _find_best_match(
        normalized_event,
        internal_records,
        window_minutes=window_minutes,
        tolerance_percent=tolerance_percent,
        allow_partial=allow_partial,
    )

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
    """Match callback event against candidate internal records."""
    normalized_event = event
    if "amount" not in event or "phone_number" not in event:
        normalized_event = normalize_daraja_event(event)

    return time_window_match(
        normalized_event,
        internal_records,
        window_minutes=window_minutes,
        tolerance_percent=tolerance_percent,
        allow_partial=allow_partial,
    )


def reconcile_with_idempotency(
    event: Dict[str, Any],
    internal_records: Sequence[Dict[str, Any]],
    event_store: Any,
    discrepancy_dao: Any,
    session: Any,
    tenant_id: Optional[str] = None,
    tenant_settings: Optional[Dict[str, Any]] = None,
    window_minutes: int = 15,
    source_ip: Optional[str] = None,
    signature_verified: bool = False,
) -> Dict[str, Any]:
    """Atomically evaluate and record reconciliation outcomes inside a single database transaction.

    Ensures that both the idempotency ledger write and the Discrepancy write commit
    together or roll back entirely.
    """
    trans_id = str(event.get("TransID") or event.get("trans_id") or "unknown").strip()

    # Pre-flight duplicate check optimization
    if event_store and event_store.already_processed(trans_id):
        logger.info("Idempotency: duplicate trans_id=%s detected prior to evaluation, skipping", trans_id)
        return {
            "trans_id": trans_id,
            "status": "duplicate_ignored",
            "severity": "info",
            "anomalies": ["duplicate_transaction_id"],
        }

    seen_trans_ids: Set[str] = set()
    evaluation = evaluate_transaction(
        event,
        internal_records,
        seen_trans_ids,
        window_minutes=window_minutes,
        tenant_settings=tenant_settings,
    )
    evaluation["tenant_id"] = tenant_id or "default"
    evaluation["event"] = event

    try:
        result = ProcessResult.STORED
        if event_store:
            result = event_store.mark_processed_in_session(
                session,
                event,
                tenant_id=tenant_id,
                source_ip=source_ip,
                signature_verified=signature_verified,
            )

        if result == ProcessResult.DUPLICATE:
            session.rollback()
            logger.info("Duplicate trans_id=%s caught during idempotency session flush, skipping", trans_id)
            return {
                "trans_id": trans_id,
                "status": "duplicate_ignored",
                "severity": "info",
                "anomalies": ["duplicate_transaction_id"],
            }

        if result == ProcessResult.ERROR:
            session.rollback()
            raise RuntimeError(f"mark_processed_in_session failed validation for trans_id={trans_id}")

        # Record discrepancy for non-matched or anomalous transactions
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

        session.commit()
        evaluation["duplicate"] = False
        return evaluation

    except Exception as exc:
        logger.exception("Error during atomic reconciliation for trans_id=%s — rolling back: %s", trans_id, exc)
        session.rollback()
        raise
