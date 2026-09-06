"""Bank payment service for transaction ingestion, reconciliation, and ledger tracking."""

from __future__ import annotations

import csv
import io
import logging
import os
import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pesaguard_backend_pipeline.models import Base, OrganizationAccount

try:
    import openpyxl
except Exception:  # pragma: no cover - optional dependency
    openpyxl = None

logger = logging.getLogger("pesaguard.bank_service")


def _normalize_enum_label(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().replace("-", "_").replace(" ", "_").upper()


class PaymentAccount:
    """Representation of a financial account attached to an organization.

    Models the hierarchy requested by the product team:
      Organization -> M-Pesa Till/Paybill | Airtel Money Account | Bank Account | Other Payment Accounts
    """

    VALID_CHANNELS = {"MOBILE_MONEY", "BANK", "CARD", "PAYMENT_GATEWAY", "OTHER"}

    def __init__(
        self,
        account_id: str,
        organization_id: str,
        payment_channel: str,
        provider: str,
        account_name: Optional[str] = None,
        account_number: Optional[str] = None,
        bank_name: Optional[str] = None,
        currency: str = "KES",
        branch: Optional[str] = None,
        account_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.account_id = str(account_id)
        self.organization_id = str(organization_id or "default")
        self.payment_channel = _normalize_enum_label(payment_channel or "OTHER")
        if self.payment_channel not in self.VALID_CHANNELS:
            self.payment_channel = "OTHER"
        self.provider = _normalize_enum_label(provider or "UNKNOWN")
        if self.provider in {"M_PESA", "MPESA", "SAFARICOM"}:
            self.provider = "MPESA"
        if self.provider in {"AIRTEL", "AIRTEL_MONEY", "AIRTELMONEY"}:
            self.provider = "AIRTEL_MONEY"
        self.account_name = str(account_name or self.provider)
        self.account_number = str(account_number or "")
        self.bank_name = str(bank_name or "")
        self.currency = str(currency or "KES").upper()
        self.branch = str(branch or "")
        self.account_type = str(account_type or "")
        self.metadata = dict(metadata or {})

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "PaymentAccount":
        return cls(
            account_id=payload.get("account_id") or payload.get("accountId") or payload.get("id") or f"acct-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
            organization_id=payload.get("organization_id") or payload.get("tenant_id") or payload.get("organizationId") or "default",
            payment_channel=payload.get("payment_channel") or payload.get("paymentChannel") or "OTHER",
            provider=payload.get("provider") or payload.get("provider_name") or payload.get("providerName") or payload.get("bank_name") or "UNKNOWN",
            account_name=payload.get("account_name") or payload.get("accountName"),
            account_number=payload.get("account_number") or payload.get("accountNumber"),
            bank_name=payload.get("bank_name") or payload.get("bankName"),
            currency=payload.get("currency") or "KES",
            branch=payload.get("branch"),
            account_type=payload.get("account_type") or payload.get("accountType"),
            metadata=payload.get("metadata") or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id,
            "organization_id": self.organization_id,
            "payment_channel": self.payment_channel,
            "provider": self.provider,
            "account_name": self.account_name,
            "account_number": self.account_number,
            "bank_name": self.bank_name,
            "currency": self.currency,
            "branch": self.branch,
            "account_type": self.account_type,
            "metadata": deepcopy(self.metadata),
        }


class BankService:
    """Manage bank account state, statement ingestion, and reconciliation workflows."""

    def __init__(self, tenant_id: str = "default"):
        self.tenant_id = tenant_id or "default"
        self._accounts: Dict[str, Dict[str, Any]] = {}
        self._payment_accounts: Dict[str, Dict[str, Any]] = {}
        self._organization_accounts: Dict[str, List[str]] = {}
        self._transactions: List[Dict[str, Any]] = []
        self._seen_references: set[str] = set()
        self._database_url = os.getenv("DATABASE_URL", "sqlite:///pesaguard_bank_service.db")
        self._engine = create_engine(
            self._database_url,
            connect_args={"check_same_thread": False} if self._database_url.startswith("sqlite") else {},
        )
        Base.metadata.create_all(self._engine)
        self._SessionLocal = sessionmaker(bind=self._engine, expire_on_commit=False)
        self._sync_payment_accounts_from_db()

    def _sync_payment_accounts_from_db(self) -> None:
        with self._SessionLocal() as session:
            rows = session.query(OrganizationAccount).all()
        for row in rows:
            account = {
                "account_id": row.account_id,
                "organization_id": row.organization_id,
                "payment_channel": row.payment_channel,
                "provider": row.provider,
                "account_name": row.account_name,
                "account_number": row.account_number,
                "bank_name": row.bank_name,
                "currency": row.currency,
                "branch": row.branch,
                "account_type": row.account_type,
                "metadata": dict(row.account_metadata or {}),
            }
            self._payment_accounts[row.account_id] = account
            self._organization_accounts.setdefault(row.organization_id, [])
            if row.account_id not in self._organization_accounts[row.organization_id]:
                self._organization_accounts[row.organization_id].append(row.account_id)

    def _persist_payment_account(self, record: Dict[str, Any]) -> Dict[str, Any]:
        with self._SessionLocal() as session:
            row = session.query(OrganizationAccount).filter_by(
                organization_id=str(record["organization_id"]),
                account_id=str(record["account_id"]),
            ).one_or_none()
            if row is None:
                row = OrganizationAccount(
                    id=str(record["account_id"]),
                    organization_id=str(record["organization_id"]),
                    account_id=str(record["account_id"]),
                    payment_channel=str(record["payment_channel"]),
                    provider=str(record["provider"]),
                    account_name=record.get("account_name"),
                    account_number=record.get("account_number"),
                    bank_name=record.get("bank_name"),
                    currency=str(record.get("currency") or "KES"),
                    branch=record.get("branch"),
                    account_type=record.get("account_type"),
                    account_metadata=dict(record.get("metadata") or {}),
                    is_active=True,
                )
                session.add(row)
            else:
                row.payment_channel = str(record["payment_channel"])
                row.provider = str(record["provider"])
                row.account_name = record.get("account_name")
                row.account_number = record.get("account_number")
                row.bank_name = record.get("bank_name")
                row.currency = str(record.get("currency") or "KES")
                row.branch = record.get("branch")
                row.account_type = record.get("account_type")
                row.account_metadata = dict(record.get("metadata") or {})
                row.is_active = True
            session.commit()
        return deepcopy(record)

    def create_account(
        self,
        account_id: str,
        account_number: str,
        bank_name: str,
        opening_balance: float = 0.0,
        currency: str = "KES",
        **extra: Any,
    ) -> Dict[str, Any]:
        account = {
            "account_id": str(account_id),
            "account_number": str(account_number),
            "bank_name": str(bank_name),
            "currency": str(currency or "KES").upper(),
            "opening_balance": float(opening_balance),
            "available_balance": float(opening_balance),
            "ledger_balance": float(opening_balance),
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": dict(extra),
        }
        self._accounts[str(account_id)] = account
        return deepcopy(account)

    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        account = self._accounts.get(str(account_id))
        return deepcopy(account) if account else None

    def register_payment_account(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Register an organization payment account across all payment channels.

        Supported by the hierarchy requested by the business:
        - MOBILE_MONEY: MPESA, AIRTEL_MONEY
        - BANK: KCB, EQUITY, CO_OP, ABSA, etc.
        - CARD / GATEWAY / OTHER
        """
        account = PaymentAccount.from_payload(payload)
        record = account.to_dict()
        self._payment_accounts[account.account_id] = record
        org_accounts = self._organization_accounts.setdefault(account.organization_id, [])
        if account.account_id not in org_accounts:
            org_accounts.append(account.account_id)
        self._persist_payment_account(record)
        return deepcopy(record)

    def get_payment_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        account = self._payment_accounts.get(str(account_id))
        if account is not None:
            return deepcopy(account)
        with self._SessionLocal() as session:
            row = session.query(OrganizationAccount).filter_by(account_id=str(account_id)).one_or_none()
        if row is None:
            return None
        account = {
            "account_id": row.account_id,
            "organization_id": row.organization_id,
            "payment_channel": row.payment_channel,
            "provider": row.provider,
            "account_name": row.account_name,
            "account_number": row.account_number,
            "bank_name": row.bank_name,
            "currency": row.currency,
            "branch": row.branch,
            "account_type": row.account_type,
            "metadata": dict(row.account_metadata or {}),
        }
        self._payment_accounts[row.account_id] = account
        return deepcopy(account)

    def list_payment_accounts(self, organization_id: Optional[str] = None, payment_channel: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self._payment_accounts:
            self._sync_payment_accounts_from_db()
        accounts = list(self._payment_accounts.values())
        if organization_id is not None:
            accounts = [acct for acct in accounts if acct.get("organization_id") == str(organization_id)]
        if payment_channel is not None:
            accounts = [acct for acct in accounts if acct.get("payment_channel") == str(payment_channel).upper()]
        return deepcopy(accounts)

    def create_mobile_money_account(
        self,
        organization_id: str,
        provider: str,
        account_id: Optional[str] = None,
        account_name: Optional[str] = None,
        account_number: Optional[str] = None,
        currency: str = "KES",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.register_payment_account({
            "account_id": account_id,
            "organization_id": organization_id,
            "payment_channel": "MOBILE_MONEY",
            "provider": provider,
            "account_name": account_name or provider,
            "account_number": account_number,
            "currency": currency,
            "metadata": metadata or {},
        })

    def create_bank_account(
        self,
        organization_id: str,
        bank_name: str,
        account_number: str,
        currency: str = "KES",
        account_id: Optional[str] = None,
        branch: Optional[str] = None,
        account_type: Optional[str] = None,
        account_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.register_payment_account({
            "account_id": account_id,
            "organization_id": organization_id,
            "payment_channel": "BANK",
            "provider": bank_name,
            "account_name": account_name or bank_name,
            "account_number": account_number,
            "bank_name": bank_name,
            "currency": currency,
            "branch": branch,
            "account_type": account_type,
            "metadata": metadata or {},
        })

    def get_account_balance(self, account_id: str) -> Dict[str, Any]:
        account = self._accounts.get(str(account_id))
        if account is None:
            raise KeyError(f"Unknown bank account: {account_id}")
        return {
            "account_id": account["account_id"],
            "account_number": account["account_number"],
            "bank_name": account["bank_name"],
            "currency": account["currency"],
            "opening_balance": account["opening_balance"],
            "available_balance": account["available_balance"],
            "ledger_balance": account["ledger_balance"],
        }

    def _ensure_account(self, account_id: str) -> Dict[str, Any]:
        if account_id not in self._accounts:
            self.create_account(account_id=account_id, account_number=account_id, bank_name="BANK", opening_balance=0.0)
        return self._accounts[str(account_id)]

    def extract_reference(self, narration: str, fallback: Optional[str] = None) -> Optional[str]:
        candidates: List[str] = []
        if fallback:
            candidates.append(str(fallback))
        for pattern in (
            r"(?:INV|INV-?|PAY|REF|SETTLE|SETTLE-?|TXN|BILL|LOAN)[-_ ]?[A-Z0-9-]+",
            r"[A-Z]{2,}-\d{3,}",
            r"\b[A-Z0-9]{6,}\b",
        ):
            match = re.search(pattern, str(narration or ""), flags=re.IGNORECASE)
            if match:
                candidates.append(match.group(0).upper())
        for value in candidates:
            normalized = value.strip(" -_")
            if normalized and len(normalized) >= 4:
                return normalized
        return None

    def normalize_transaction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize bank transaction shapes into the internal ledger model."""
        if not isinstance(payload, dict):
            raise ValueError("Bank transaction payload must be a dict")

        amount = float(payload.get("amount") or 0.0)
        reference = str(payload.get("reference") or self.extract_reference(payload.get("narration") or "", payload.get("payment_reference")) or "BANK-UNKNOWN")
        narration = str(payload.get("narration") or payload.get("description") or "").strip()
        status = str(payload.get("status") or "POSTED").upper()
        currency = str(payload.get("currency") or payload.get("Currency") or "KES").upper()
        direction = "debit" if amount < 0 else "credit"

        bank_name = str(payload.get("bankName") or payload.get("bank_name") or "")
        normalized = {
            "tenant_id": self.tenant_id,
            "account_id": str(payload.get("accountId") or payload.get("account_id") or ""),
            "reference": reference,
            "amount": abs(amount),
            "net_amount": amount,
            "currency": currency,
            "direction": direction,
            "status": status,
            "narration": narration,
            "transaction_type": str(payload.get("transactionType") or payload.get("type") or ("DEBIT" if amount < 0 else "CREDIT")).upper(),
            "timestamp": str(payload.get("timestamp") or payload.get("posted_at") or datetime.now(timezone.utc).isoformat()),
            "bank_name": bank_name,
            "account_number": str(payload.get("accountNumber") or payload.get("account_number") or ""),
            "payment_channel": "BANK",
            "provider": bank_name.upper() if bank_name else "BANK",
            "raw_payload": deepcopy(payload),
        }
        return normalized

    def ingest_transaction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest a single bank transaction and update account balances."""
        normalized = self.normalize_transaction(payload)
        reference = normalized.get("reference")
        normalized["duplicate"] = reference in self._seen_references
        self._transactions.append(normalized)

        if reference:
            self._seen_references.add(reference)

        account_id = normalized["account_id"] or "default-account"
        account = self._ensure_account(account_id)

        normalized["failed"] = normalized["status"] == "FAILED"

        if normalized["direction"] == "credit":
            account["available_balance"] += normalized["amount"]
            account["ledger_balance"] += normalized["amount"]
        else:
            account["available_balance"] -= normalized["amount"]
            account["ledger_balance"] -= normalized["amount"]

        return deepcopy(normalized)

    def ingest_statement(self, rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bulk ingest bank statement rows."""
        ingested: List[Dict[str, Any]] = []
        for row in rows:
            ingested.append(self.ingest_transaction(row))
        return ingested

    def ingest_csv(
        self,
        csv_text: str,
        account_id: Optional[str] = None,
        bank_name: Optional[str] = None,
        delimiter: str = ",",
    ) -> List[Dict[str, Any]]:
        """Import bank statement data from CSV text."""
        rows = list(csv.DictReader(io.StringIO(csv_text), delimiter=delimiter))
        enriched = []
        for row in rows:
            if account_id:
                row.setdefault("accountId", account_id)
            if bank_name:
                row.setdefault("bankName", bank_name)
            enriched.append(row)
        return self.ingest_statement(enriched)

    def ingest_excel(
        self,
        workbook_bytes: bytes | str,
        account_id: Optional[str] = None,
        bank_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Import a spreadsheet-based bank statement if openpyxl is available."""
        if openpyxl is None:
            raise RuntimeError("openpyxl is required for Excel ingestion")

        if isinstance(workbook_bytes, str):
            workbook_bytes = workbook_bytes.encode("utf-8")

        workbook = openpyxl.load_workbook(io.BytesIO(workbook_bytes), read_only=True, data_only=True)
        sheet = workbook.active
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            return []
        headers = [str(header or "").strip().lower() for header in rows[0]]
        data_rows = []
        for row in rows[1:]:
            record = dict(zip(headers, row))
            if not any(value not in (None, "") for value in record.values()):
                continue
            if account_id:
                record.setdefault("accountid", account_id)
            if bank_name:
                record.setdefault("bankname", bank_name)
            data_rows.append(record)
        return self.ingest_statement(data_rows)

    def ingest_manual_upload(self, csv_text: str, file_name: str = "statement.csv", account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Handle manually uploaded bank statement files."""
        return self.ingest_csv(csv_text, account_id=account_id, bank_name="MANUAL_UPLOAD")

    def ingest_pdf_statement(
        self,
        pdf_text: str,
        account_id: Optional[str] = None,
        bank_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Support PDF text extraction where the source is a text-based PDF export or OCR result."""
        lines = [line.strip() for line in str(pdf_text).splitlines() if line.strip()]
        extracted: List[Dict[str, Any]] = []
        current: Dict[str, Any] = {}
        for line in lines:
            if line.lower().startswith("date:"):
                current["timestamp"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("description:"):
                current["narration"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("amount:"):
                current["amount"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("reference:"):
                current["reference"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("status:"):
                current["status"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("account:"):
                current["accountId"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("balance:"):
                current["balance"] = line.split(":", 1)[1].strip()
            if current and "amount" in current and "narration" in current:
                if account_id:
                    current.setdefault("accountId", account_id)
                if bank_name:
                    current.setdefault("bankName", bank_name)
                if not current.get("reference"):
                    current["reference"] = self.extract_reference(current.get("narration") or "", current.get("amount")) or "PDF-UNKNOWN"
                if not current.get("status"):
                    current["status"] = "POSTED"
                extracted.append(current)
                current = {}

        if not extracted:
            fallback_reference = self.extract_reference(pdf_text, "PDF-STATEMENT") or "PDF-UNKNOWN"
            extracted = [{
                "accountId": account_id or "default-account",
                "reference": fallback_reference,
                "amount": re.search(r"-?\d+(?:\.\d+)?", pdf_text or "") and float(re.search(r"-?\d+(?:\.\d+)?", pdf_text or "").group(0)) or 0.0,
                "narration": pdf_text[:180],
                "status": "POSTED",
                "bankName": bank_name or "BANK",
            }]

        return self.ingest_statement(extracted)

    def ingest_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Accept provider/webhook-created transactions and normalize them into the bank ledger."""
        return self.ingest_transaction(payload)

    def ingest_sftp_statement(
        self,
        host: str,
        remote_path: str,
        username: str,
        password: str,
        client_factory: Optional[Callable[..., Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch a statement over SFTP and import it as CSV."""
        factory = client_factory or (lambda *args, **kwargs: None)
        client = factory(host=host, username=username, password=password, remote_path=remote_path)
        if client is None:
            return []
        if hasattr(client, "open"):
            handle = client.open(remote_path)
            raw = handle.read() if hasattr(handle, "read") else b""
        elif hasattr(client, "read"):
            raw = client.read()
        else:
            raw = b""
        content = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw or "")
        return self.ingest_csv(content)

    def schedule_statement_retrieval(self, schedule: Dict[str, Any]) -> Dict[str, Any]:
        """Register a scheduled extraction configuration for a bank statement source."""
        scheduled = {
            "id": f"sched-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            **schedule,
        }
        self._scheduled = getattr(self, "_scheduled", [])
        self._scheduled.append(scheduled)
        return deepcopy(scheduled)

    def run_scheduled_statement_retrieval(
        self,
        schedule: Dict[str, Any],
        fetcher: Optional[Callable[[], str]] = None,
    ) -> List[Dict[str, Any]]:
        """Run a scheduled statement import using a custom fetcher or a scheduled config feed."""
        if fetcher is None:
            fetcher = lambda: ""
        content = fetcher()
        return self.ingest_csv(content)

    def detect_fee(self, normalized: Dict[str, Any]) -> bool:
        return (
            normalized.get("direction") == "debit"
            and any(token in str(normalized.get("narration", "")).lower() for token in ("fee", "maintenance", "service charge", "bank fee"))
        )

    def detect_charge(self, normalized: Dict[str, Any]) -> bool:
        return (
            normalized.get("direction") == "debit"
            and any(token in str(normalized.get("narration", "")).lower() for token in ("charge", "commission", "txn fee", "processing fee"))
        )

    def detect_reversal(self, normalized: Dict[str, Any]) -> bool:
        return any(token in str(normalized.get("narration", "")).lower() for token in ("reversal", "reversed", "return credit")) or str(normalized.get("status", "")).upper() == "REVERSED"

    def detect_failed(self, normalized: Dict[str, Any]) -> bool:
        return str(normalized.get("status", "")).upper() == "FAILED"

    def detect_duplicate(self, normalized: Dict[str, Any]) -> bool:
        reference = normalized.get("reference")
        if not reference:
            return False
        if reference in self._seen_references:
            return True
        count = sum(1 for item in self._transactions if item.get("reference") == reference)
        return count > 1

    def reconcile_settlements(
        self,
        bank_records: Iterable[Dict[str, Any]],
        ledger_records: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Match bank settlement rows to the internal ledger using reference and amount."""
        bank_list = list(bank_records)
        ledger_list = list(ledger_records)

        matched = []
        unmatched_bank = []
        unmatched_ledger = []

        for bank in bank_list:
            ref = str(bank.get("reference") or "").strip()
            amount = float(bank.get("amount") or 0.0)
            found = False
            for ledger in ledger_list:
                if str(ledger.get("reference") or "").strip() == ref and float(ledger.get("amount") or 0.0) == amount:
                    matched.append({"bank": bank, "ledger": ledger})
                    found = True
                    break
            if not found:
                unmatched_bank.append(bank)

        for ledger in ledger_list:
            ref = str(ledger.get("reference") or "").strip()
            amount = float(ledger.get("amount") or 0.0)
            if not any(str(item["ledger"].get("reference") or "").strip() == ref and float(item["ledger"].get("amount") or 0.0) == amount for item in matched):
                unmatched_ledger.append(ledger)

        status = "reconciled" if not unmatched_bank and not unmatched_ledger else "needs_review"
        return {
            "status": status,
            "matched_count": len(matched),
            "unmatched_bank": len(unmatched_bank),
            "unmatched_ledger": len(unmatched_ledger),
            "matches": matched,
            "unmatched_bank_rows": unmatched_bank,
            "unmatched_ledger_rows": unmatched_ledger,
        }

    def reconcile_bank_statement(self, statement_rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyse bank statement rows for fees, reversals, losses, and duplicates."""
        normalized_rows = [self.normalize_transaction(row) for row in statement_rows]
        summary = {
            "total_rows": len(normalized_rows),
            "fees": 0,
            "charges": 0,
            "reversals": 0,
            "failed": 0,
            "duplicates": 0,
            "matched": 0,
        }
        for row in normalized_rows:
            if self.detect_fee(row):
                summary["fees"] += 1
            if self.detect_charge(row):
                summary["charges"] += 1
            if self.detect_reversal(row):
                summary["reversals"] += 1
            if self.detect_failed(row):
                summary["failed"] += 1
            if self.detect_duplicate(row):
                summary["duplicates"] += 1
        summary["matched"] = summary["total_rows"] - summary["failed"]
        return summary
