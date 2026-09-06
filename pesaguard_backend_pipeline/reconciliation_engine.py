"""
Reconciliation Engine for matching M-Pesa Daraja callbacks to internal ledger records.

Turns raw webhook events into auditable reconciliation outcomes so operational teams
can distinguish between exact matches, partial matches, missing payments, and duplicate callbacks.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Set

from pesaguard_backend_pipeline.event_store import ProcessResult
from pesaguard_backend_pipeline.validators import resolve_trans_id

logger = logging.getLogger("pesaguard.reconciliation_engine")


def _normalize_enum_value(value: Any) -> str:
    """Normalize provider names and channel labels into the canonical enum style."""
    if value is None:
        return ""
    cleaned = str(value).strip().replace("-", "_").replace(" ", "_")
    return cleaned.upper()


def resolve_payment_context(event: Dict[str, Any]) -> Dict[str, str]:
    """Resolve the payment channel and concrete provider from a webhook payload or event dict.

    This uses the hierarchical model:
      PAYMENT_CHANNEL -> MOBILE_MONEY | BANK | CARD | PAYMENT_GATEWAY | OTHER
      provider -> MPESA | AIRTEL_MONEY | KCB | EQUITY | ...
    """
    if not isinstance(event, dict):
        return {"payment_channel": "OTHER", "provider": "UNKNOWN"}

    payment_channel = _normalize_enum_value(event.get("payment_channel") or event.get("paymentChannel") or "")
    provider_hint = _normalize_enum_value(event.get("provider") or event.get("payment_provider") or event.get("paymentProvider") or "")

    if payment_channel in {"MOBILE_MONEY", "BANK", "CARD", "PAYMENT_GATEWAY", "OTHER"}:
        base_provider = provider_hint or "UNKNOWN"
        if payment_channel == "MOBILE_MONEY":
            if base_provider in {"MPESA", "DARAJA", "SAFARICOM"}:
                return {"payment_channel": "MOBILE_MONEY", "provider": "MPESA"}
            if base_provider in {"AIRTEL", "AIRTEL_MONEY", "AIRTELMONEY"}:
                return {"payment_channel": "MOBILE_MONEY", "provider": "AIRTEL_MONEY"}
            return {"payment_channel": "MOBILE_MONEY", "provider": base_provider or "UNKNOWN"}
        if payment_channel == "BANK":
            bank_name = _normalize_enum_value(event.get("bankName") or event.get("bank_name") or event.get("bank") or "")
            return {"payment_channel": "BANK", "provider": bank_name or base_provider or "BANK"}
        return {"payment_channel": payment_channel, "provider": base_provider or "UNKNOWN"}

    bank_name = _normalize_enum_value(event.get("bankName") or event.get("bank_name") or event.get("bank") or "")
    if bank_name or event.get("accountNumber") or event.get("account_number") or event.get("sort_code") or event.get("iban"):
        return {"payment_channel": "BANK", "provider": bank_name or "BANK"}

    provider_hint = provider_hint.lower()
    if provider_hint in {"mpesa", "daraja", "safaricom", "m_pesa", "m_pesa_mobile_money"}:
        return {"payment_channel": "MOBILE_MONEY", "provider": "MPESA"}
    if provider_hint in {"airtel", "airtel_money", "airtelmoney"}:
        return {"payment_channel": "MOBILE_MONEY", "provider": "AIRTEL_MONEY"}
    if provider_hint in {"bank", "bank_transfer", "bank-transfer", "banking"}:
        return {"payment_channel": "BANK", "provider": bank_name or "BANK"}
    if event.get("transactionType") == "AIRTEL_MONEY" or event.get("transactionType") == "airtel_money":
        return {"payment_channel": "MOBILE_MONEY", "provider": "AIRTEL_MONEY"}
    if event.get("transactionId") or event.get("TransactionId"):
        return {"payment_channel": "MOBILE_MONEY", "provider": "AIRTEL_MONEY"}
    if event.get("TransID") or event.get("TransactionType") in {"STK_PUSH", "C2B", "B2C"}:
        return {"payment_channel": "MOBILE_MONEY", "provider": "MPESA"}
    if event.get("card_number") or event.get("cardNumber") or event.get("card_brand") or event.get("cardBrand"):
        return {"payment_channel": "CARD", "provider": "CARD"}
    if event.get("gateway") or event.get("merchant") or event.get("checkout_id"):
        return {"payment_channel": "PAYMENT_GATEWAY", "provider": "PAYMENT_GATEWAY"}
    return {"payment_channel": "OTHER", "provider": "UNKNOWN"}


def resolve_provider(event: Dict[str, Any]) -> str:
    """Resolve the concrete payment provider from a webhook payload or event dict."""
    return resolve_payment_context(event).get("provider", "UNKNOWN")


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
    payment_context = resolve_payment_context(event)
    provider = payment_context["provider"]
    payment_channel = payment_context["payment_channel"]
    trans_id = resolve_trans_id(event) or "unknown"
    duplicate = trans_id in seen_trans_ids

    anomalies: List[str] = []
    if duplicate:
        anomalies.append("duplicate_transaction_id")

    event_time = _parse_event_time(event.get("TransTime") or event.get("transactionTime") or event.get("timestamp"))
    if event_time:
        latency = (datetime.now(timezone.utc) - event_time).total_seconds()
        if latency > 3600:
            anomalies.append("late_arriving_event")

    amount = _coerce_amount(event.get("TransAmount") or event.get("amount"))
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
            "payment_channel": payment_channel,
            "provider": provider,
            "status": "missing_payment",
            "severity": "critical",
            "duplicate": duplicate,
            "anomalies": anomalies,
            "risk_score": 0.98,
            "match": {"match_type": "none", "reason": "no_internal_records", "confidence": 0.0},
        }

    best_match = _find_best_match(
        event,
        internal_records,
        window_minutes=window_minutes,
        tolerance_percent=tolerance_percent,
        allow_partial=allow_partial,
    )

    if best_match is None:
        return {
            "trans_id": trans_id,
            "provider": provider,
            "status": "missing_payment",
            "severity": "critical",
            "duplicate": duplicate,
            "anomalies": anomalies,
            "risk_score": 0.95,
            "match": {"match_type": "none", "reason": "no_matching_record", "confidence": 0.0},
        }

    match_metrics = _score_match(best_match, anomalies, duplicate)
    best_match.update(match_metrics)

    if best_match["match_type"] in {"exact", "fuzzy_exact"}:
        return {
            "trans_id": trans_id,
            "payment_channel": payment_channel,
            "provider": provider,
            "status": "matched",
            "severity": "info",
            "duplicate": duplicate,
            "anomalies": anomalies,
            "risk_score": match_metrics["risk_score"],
            "match": best_match,
        }

    return {
        "trans_id": trans_id,
        "payment_channel": payment_channel,
        "provider": provider,
        "status": "needs_review",
        "severity": "warning",
        "duplicate": duplicate,
        "anomalies": anomalies,
        "risk_score": match_metrics["risk_score"],
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
    amount = _coerce_amount(event.get("TransAmount") or event.get("amount"))
    if amount is None or amount <= 0:
        return None

    phone = str(event.get("MSISDN") or event.get("phone_number") or "").strip()
    event_time = _parse_event_time(event.get("TransTime"))
    allowed_delta = max(0.01, abs(amount) * (float(tolerance_percent) / 100.0))

    candidates = []
    for record in internal_records:
        record_time = _parse_record_time(record.get("timestamp") or record.get("synced_at") or record.get("created_at"))
        
        latency = 0
        if record_time is not None and event_time is not None:
            latency = int(abs((event_time - record_time).total_seconds()))
            if latency > window_minutes * 60:
                continue

        record_amount = _coerce_amount(record.get("amount"))
        if record_amount is None:
            continue

        amt_diff = abs(record_amount - amount)
        if amt_diff > allowed_delta:
            continue

        record_phone = str(record.get("phone_number") or record.get("msisdn") or "").strip()
        phone_matches = record_phone == phone and len(phone) > 0

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
    candidates.sort(
        key=lambda item: (
            priority.get(item["match_type"], 99),
            item["latency_seconds"],
            item["amount_diff"],
        )
    )
    return candidates[0]


def _coerce_amount(value: Any) -> Optional[float]:
    """Safely cast raw values to float."""
    if value is None:
        return None
    try:
        val = float(value)
        return val if not math.isnan(val) else None
    except (TypeError, ValueError):
        return None


def _score_match(best_match: Dict[str, Any], anomalies: Sequence[str], duplicate: bool) -> Dict[str, Any]:
    """Assign a confidence score and risk score to an evaluated match."""
    match_type = best_match.get("match_type", "none")
    quality_scores = {
        "exact": 0.95,
        "fuzzy_exact": 0.78,
        "partial_fuzzy": 0.60,
        "partial": 0.45,
        "none": 0.0,
    }
    confidence = quality_scores.get(match_type, 0.0)

    if duplicate:
        confidence -= 0.08
    if "invalid_or_zero_amount" in anomalies:
        confidence -= 0.15
    if "duplicate_transaction_id" in anomalies:
        confidence -= 0.05

    amount_diff = float(best_match.get("amount_diff", 0.0) or 0.0)
    if amount_diff > 0:
        confidence -= min(0.15, amount_diff / 1000.0)

    confidence = max(0.0, min(1.0, confidence))

    risk_score = 1.0 - confidence
    if "duplicate_transaction_id" in anomalies:
        risk_score += 0.08
    if "invalid_or_zero_amount" in anomalies:
        risk_score += 0.12
    if match_type in {"partial", "partial_fuzzy"}:
        risk_score += 0.10

    risk_score = max(0.0, min(1.0, risk_score))
    return {"confidence": round(confidence, 3), "risk_score": round(risk_score, 3)}


import math


def _parse_event_time(value: Any) -> Optional[datetime]:
    """Parse M-Pesa 14-digit Daraja timestamp strings or ISO timestamps into UTC datetimes."""
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
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def _parse_record_time(value: Any) -> Optional[datetime]:
    return _parse_event_time(value)


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
    trans_id = resolve_trans_id(event)
    if not trans_id:
        # Without a provider transaction id there is no dedupe key, so the ledger write
        # below would fail validation. Surface it explicitly instead of silently
        # collapsing every such event onto a shared "unknown" key.
        logger.error("reconcile_with_idempotency() received an event with no resolvable transaction id")
        trans_id = "unknown"

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
