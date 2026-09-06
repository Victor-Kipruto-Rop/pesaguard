from pesaguard_backend_pipeline.bank_service import BankService


def test_bank_service_normalizes_transaction_and_extracts_reference():
    service = BankService(tenant_id="tenant-bank")

    normalized = service.normalize_transaction({
        "accountNumber": "1234567890",
        "reference": "INV-1007",
        "narration": "Invoice INV-1007 settlement for supplier",
        "amount": "5000",
        "currency": "KES",
        "transactionType": "CREDIT",
        "status": "POSTED",
        "timestamp": "2026-09-06T10:00:00Z",
    })

    assert normalized["reference"] == "INV-1007"
    assert normalized["amount"] == 5000.0
    assert normalized["direction"] == "credit"
    assert normalized["currency"] == "KES"


def test_bank_service_detects_fee_charge_reversal_failed_and_duplicate():
    service = BankService(tenant_id="tenant-bank")

    fee_txn = service.normalize_transaction({
        "reference": "FEE-1",
        "amount": "-50",
        "narration": "Account maintenance fee",
        "status": "POSTED",
    })
    charge_txn = service.normalize_transaction({
        "reference": "CHG-2",
        "amount": "-180",
        "narration": "Service charge",
        "status": "POSTED",
    })
    reversal_txn = service.normalize_transaction({
        "reference": "REV-3",
        "amount": "-250",
        "narration": "Reversal of deposit",
        "status": "REVERSED",
    })
    failed_txn = service.normalize_transaction({
        "reference": "FAIL-4",
        "amount": "300",
        "narration": "Transfer failed",
        "status": "FAILED",
    })

    service.ingest_transaction({
        "accountId": "acct-100",
        "reference": "INV-1007",
        "amount": "5000",
        "narration": "Invoice settlement",
        "status": "POSTED",
    })
    duplicate_txn = service.normalize_transaction({
        "accountId": "acct-100",
        "reference": "INV-1007",
        "amount": "5000",
        "narration": "Duplicate invoice settlement",
        "status": "POSTED",
    })

    assert service.detect_fee(fee_txn) is True
    assert service.detect_charge(charge_txn) is True
    assert service.detect_reversal(reversal_txn) is True
    assert service.detect_failed(failed_txn) is True
    assert service.detect_duplicate(duplicate_txn) is True


def test_bank_service_reconciles_settlements_and_tracks_balances():
    service = BankService(tenant_id="tenant-bank")

    account = service.create_account(
        account_id="acct-100",
        account_number="1234567890",
        bank_name="KCB",
        opening_balance=10000.0,
        currency="KES",
    )

    service.ingest_transaction({
        "accountId": "acct-100",
        "reference": "SETTLE-200",
        "amount": "2500",
        "currency": "KES",
        "status": "POSTED",
        "narration": "Settlement for invoice INV-200",
    })
    service.ingest_transaction({
        "accountId": "acct-100",
        "reference": "SETTLE-201",
        "amount": "-100",
        "currency": "KES",
        "status": "POSTED",
        "narration": "Bank fee",
    })

    account_state = service.get_account_balance("acct-100")
    assert account_state["available_balance"] == 12400.0

    result = service.reconcile_settlements(
        [
            {"reference": "SETTLE-200", "amount": 2500, "status": "POSTED"},
            {"reference": "SETTLE-201", "amount": -100, "status": "POSTED"},
        ],
        [
            {"reference": "SETTLE-200", "amount": 2500},
            {"reference": "SETTLE-201", "amount": -100},
        ],
    )

    assert result["matched_count"] == 2
    assert result["status"] == "reconciled"


def test_bank_service_tracks_organization_payment_accounts_by_channel_and_provider():
    service = BankService(tenant_id="tenant-org")

    mpesa_account = service.create_mobile_money_account(
        organization_id="org-1",
        provider="M-Pesa",
        account_id="mpesa-1",
        account_name="Sales MPesa",
        account_number="254712345678",
        currency="KES",
    )
    airtel_account = service.create_mobile_money_account(
        organization_id="org-1",
        provider="Airtel Money",
        account_id="airtel-1",
        account_name="Sales Airtel",
        account_number="256700000001",
        currency="UGX",
    )
    bank_account = service.create_bank_account(
        organization_id="org-1",
        bank_name="KCB",
        account_number="1234567890",
        branch="Nairobi CBD",
        account_type="CURRENT",
        account_id="bank-1",
        currency="KES",
    )

    assert mpesa_account["payment_channel"] == "MOBILE_MONEY"
    assert mpesa_account["provider"] == "MPESA"
    assert airtel_account["provider"] == "AIRTEL_MONEY"
    assert bank_account["payment_channel"] == "BANK"
    assert bank_account["provider"] == "KCB"

    registered = service.list_payment_accounts(organization_id="org-1")
    assert {item["account_id"] for item in registered} == {"mpesa-1", "airtel-1", "bank-1"}
    assert service.get_payment_account("bank-1")["branch"] == "Nairobi CBD"


def test_bank_service_persists_organization_payment_accounts_to_sqlalchemy(monkeypatch, tmp_path):
    db_path = tmp_path / "pesaguard_org_accounts.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    service = BankService(tenant_id="tenant-org")
    service.create_mobile_money_account(
        organization_id="org-persist",
        provider="M-Pesa",
        account_id="mpesa-persist",
        account_name="Persist MPesa",
        account_number="254700123456",
        currency="KES",
    )

    reloaded = BankService(tenant_id="tenant-org")
    accounts = reloaded.list_payment_accounts(organization_id="org-persist")

    assert {item["account_id"] for item in accounts} == {"mpesa-persist"}
    assert accounts[0]["provider"] == "MPESA"


def test_bank_service_supports_csv_manual_upload_and_webhook_ingestion():
    service = BankService(tenant_id="tenant-bank")

    csv_rows = service.ingest_csv(
        "date,reference,accountId,amount,narration,status\n2026-09-06,CSV-100,acct-csv,2500,Payroll deposit,POSTED\n",
        account_id="acct-csv",
        bank_name="KCB",
    )
    assert len(csv_rows) == 1
    assert csv_rows[0]["reference"] == "CSV-100"

    webhook_row = service.ingest_webhook({
        "accountId": "acct-webhook",
        "reference": "WEB-200",
        "amount": "-120",
        "narration": "Webhook bank fee",
        "status": "POSTED",
    })
    assert webhook_row["reference"] == "WEB-200"
    assert webhook_row["direction"] == "debit"

    manual_rows = service.ingest_manual_upload(
        "date,reference,amount,narration,status\n2026-09-06,MAN-300,4300,Manual settlement upload,POSTED\n",
        file_name="manual.csv",
    )
    assert len(manual_rows) == 1
    assert manual_rows[0]["reference"] == "MAN-300"


def test_bank_service_supports_excel_pdf_sftp_and_scheduled_retrieval():
    service = BankService(tenant_id="tenant-bank")

    openpyxl = __import__("pytest").importorskip("openpyxl")
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["date", "reference", "accountId", "amount", "narration", "status"])
    sheet.append(["2026-09-06", "XL-500", "acct-excel", "3200", "Excel settlement", "POSTED"])
    buffer = __import__("io").BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    excel_rows = service.ingest_excel(buffer.getvalue(), account_id="acct-excel", bank_name="KCB")
    assert len(excel_rows) == 1
    assert excel_rows[0]["reference"] == "XL-500"

    pdf_rows = service.ingest_pdf_statement(
        "Date: 2026-09-06\nDescription: PDF settlement\nAmount: 1550.00\n",
        account_id="acct-pdf",
        bank_name="Co-operative Bank",
    )
    assert len(pdf_rows) == 1
    assert pdf_rows[0]["amount"] == 1550.0

    class FakeSFTPClient:
        def __init__(self):
            self.data = "date,reference,accountId,amount,narration,status\n2026-09-06,SFTP-11,acct-sftp,890.50,Remote sync deposit,POSTED\n"

        def open(self, path):
            return self

        def read(self):
            return self.data.encode("utf-8")

    rows = service.ingest_sftp_statement(
        host="ftp.bank.local",
        remote_path="/incoming/statement.csv",
        username="ops",
        password="secret",
        client_factory=lambda *args, **kwargs: FakeSFTPClient(),
    )
    assert len(rows) == 1
    assert rows[0]["reference"] == "SFTP-11"

    schedule = service.schedule_statement_retrieval({
        "source_type": "csv",
        "schedule": "0 1 * * *",
        "provider": "bank",
        "remote_path": "/incoming/nightly.csv",
    })
    fetched = service.run_scheduled_statement_retrieval(
        schedule,
        fetcher=lambda: "date,reference,amount,narration,status\n2026-09-06,SCHED-88,400,scheduled import,POSTED\n",
    )
    assert fetched[0]["reference"] == "SCHED-88"
