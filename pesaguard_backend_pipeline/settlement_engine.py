"""Settlement Engine: acts on reconciliation outcomes to drive settlements.

Provides helpers to reconcile bank statement rows against internal ledger rows
and optionally trigger outbound bank transfers for unmatched ledger items.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional
import logging
import time

from pesaguard_backend_pipeline.bank_service import BankService
from pesaguard_backend_pipeline.models import SettlementAttempt
from pesaguard_backend_pipeline import notifier
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

logger = logging.getLogger("pesaguard.settlement_engine")


def SessionLocal(read_only: bool | None = None):
    """Resolve ``app_2.SessionLocal`` lazily, at call time.

    This is a deliberate lazy proxy, not a stylistic choice. Importing ``app_2``
    eagerly at module scope creates the cycle::

        app_1 -> app -> settlement_engine -> app_2 -> app

    which raises ``ImportError: cannot import name 'app' from partially
    initialized module`` for any interpreter that imports these modules in that
    order. It also inverts the dependency direction (a domain engine should not
    import the Flask web layer at load time).

    Keeping the name bound at module scope preserves the existing test contract
    (tests monkeypatch ``settlement_engine.SessionLocal``), while deferring the
    web-layer import until a settlement actually runs.
    """
    from pesaguard_backend_pipeline.app_2 import SessionLocal as _app2_session_local

    return _app2_session_local(read_only=read_only)


class SettlementEngine:
    """Lightweight settlement orchestration helpers.

    The engine focuses on two responsibilities:
    - Reconcile a set of bank statement rows to internal ledger rows.
    - Optionally trigger outbound bank payouts for unmatched ledger items
      (e.g. supplier disbursements) using a provided payment client.
    """

    def __init__(self, tenant_id: str = "default"):
        self.tenant_id = tenant_id or "default"

    def reconcile_bank_and_ledger(
        self,
        bank_rows: Iterable[Dict[str, Any]],
        ledger_rows: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Run reconciliation using BankService utilities and return the result."""
        service = BankService(tenant_id=self.tenant_id)
        result = service.reconcile_settlements(bank_rows, ledger_rows)
        logger.info("Reconciliation summary: %s", {k: result.get(k) for k in ("status", "matched_count")})
        return result

    def settle_unmatched_ledger(
        self,
        unmatched_ledger: Iterable[Dict[str, Any]],
        bank_client: Optional[Any] = None,
        dry_run: bool = False,
        max_retries: int = 2,
        backoff_base_seconds: float = 1.0,
    ) -> Dict[str, Any]:
        """Attempt to settle unmatched ledger items by issuing outbound transfers.

        Args:
            unmatched_ledger: Iterable of ledger rows deemed unpaid.
            bank_client: Optional client exposing `request_payment(...)`.
            dry_run: when True, do not actually call the client.

        Returns:
            Summary dict with attempted settlements and responses or errors.
        """
        results: List[Dict[str, Any]] = []

        session = SessionLocal(read_only=False)

        for item in list(unmatched_ledger):
            ref = str(item.get("reference") or item.get("internal_ref") or "").strip()
            amount = float(item.get("amount") or 0.0)
            account_number = str(item.get("account_number") or item.get("account") or item.get("payer_account") or "")
            bank_name = str(item.get("bank_name") or item.get("bank") or "")
            narration = str(item.get("narration") or item.get("description") or f"Settlement for {ref}")

            entry = {"reference": ref, "amount": amount, "account_number": account_number, "bank_name": bank_name}
            if dry_run or bank_client is None:
                entry.update({"status": "dry_run" if dry_run else "not_attempted"})
                results.append(entry)
                continue

            attempt = 0
            last_exc = None
            while attempt <= max_retries:
                attempt += 1
                sa = SettlementAttempt(
                    id=f"settle_{ref}_{int(datetime.now(timezone.utc).timestamp()*1000)}_{attempt}",
                    tenant_id=self.tenant_id,
                    reference=ref,
                    amount=amount,
                    account_number=account_number,
                    bank_name=bank_name,
                    status="pending",
                    attempt_number=attempt,
                    created_at=datetime.now(timezone.utc),
                )
                try:
                    session.add(sa)
                    session.flush()
                except SQLAlchemyError:
                    session.rollback()
                    logger.exception("Failed to persist settlement attempt metadata for ref=%s", ref)

                try:
                    resp = bank_client.request_payment(
                        amount=amount,
                        currency=str(item.get("currency") or "KES").upper(),
                        reference=ref or f"SETTLE-{id(item)}",
                        account_number=account_number,
                        bank_name=bank_name,
                        narration=narration,
                    )

                    entry.update({"status": "requested", "response": resp, "attempt": attempt})

                    # mark attempt success
                    try:
                        sa.status = "success"
                        sa.response = resp if isinstance(resp, dict) else {"result": str(resp)}
                        sa.last_attempt_at = datetime.now(timezone.utc)
                        session.add(sa)
                        session.commit()
                    except SQLAlchemyError:
                        session.rollback()
                        logger.exception("Failed to update settlement attempt as success for ref=%s", ref)

                    break

                except Exception as exc:
                    last_exc = exc
                    logger.exception("Settlement request failed for ref=%s attempt=%d: %s", ref, attempt, exc)
                    try:
                        sa.status = "failed"
                        sa.error_message = str(exc)
                        sa.last_attempt_at = datetime.now(timezone.utc)
                        session.add(sa)
                        session.commit()
                    except SQLAlchemyError:
                        session.rollback()
                        logger.exception("Failed to persist failed settlement attempt for ref=%s", ref)

                    if attempt <= max_retries:
                        backoff = backoff_base_seconds * (2 ** (attempt - 1))
                        time.sleep(backoff)
                        continue
                    else:
                        entry.update({"status": "error", "error": str(last_exc), "attempt": attempt})
                        # send an alert for persistent failure
                        try:
                            alert_payload = {
                                "trans_id": ref,
                                "tenant_id": self.tenant_id,
                                "severity": "critical",
                                "anomalies": ["settlement_failure"],
                                "amount": amount,
                                "status": "failed",
                                "details": {"account": account_number, "bank": bank_name, "attempts": attempt},
                            }
                            notifier.send_routed_alert(alert_payload)
                        except Exception:
                            logger.exception("Failed to send settlement failure alert for ref=%s", ref)

            results.append(entry)

        try:
            session.close()
        except Exception:
            pass

        return {"attempted": len(results), "results": results}
