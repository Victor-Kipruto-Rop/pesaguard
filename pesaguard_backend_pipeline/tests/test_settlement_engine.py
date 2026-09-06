from pesaguard_backend_pipeline.settlement_engine import SettlementEngine


class DummyBankClient:
    def __init__(self):
        self.calls = []

    def request_payment(self, amount, currency, reference, account_number, bank_name, narration=None, **extra):
        self.calls.append({
            "amount": amount,
            "currency": currency,
            "reference": reference,
            "account_number": account_number,
            "bank_name": bank_name,
        })
        return {"status": "processed", "transactionId": f"BANK-{reference}"}


def test_reconcile_and_settle_unmatched(monkeypatch):
    engine = SettlementEngine(tenant_id="tenant-bank")

    # No bank rows, one ledger item
    bank_rows = []
    ledger_rows = [
        {"reference": "INV-200", "amount": 150.0, "account_number": "12345", "bank_name": "KCB", "currency": "KES"}
    ]

    result = engine.reconcile_bank_and_ledger(bank_rows, ledger_rows)
    assert result["status"] == "needs_review"
    assert result["unmatched_ledger"] == 1

    dummy = DummyBankClient()
    # monkeypatch DB session to avoid real DB access in unit test
    class FakeSession:
        def add(self, *args, **kwargs):
            pass

        def flush(self):
            pass

        def commit(self):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr('pesaguard_backend_pipeline.settlement_engine.SessionLocal', lambda read_only=False: FakeSession())

    settle_summary = engine.settle_unmatched_ledger(ledger_rows, bank_client=dummy, dry_run=False)
    assert settle_summary["attempted"] == 1
    assert len(dummy.calls) == 1
    assert dummy.calls[0]["reference"] == "INV-200"


def test_settle_dry_run():
    engine = SettlementEngine()
    ledger_rows = [{"reference": "INV-DRY", "amount": 20.0}]
    summary = engine.settle_unmatched_ledger(ledger_rows, bank_client=None, dry_run=True)
    assert summary["attempted"] == 1
    assert summary["results"][0]["status"] == "dry_run"


def test_settlement_retries_and_alert(monkeypatch):
    engine = SettlementEngine(tenant_id="t1")

    class FailingBankClient:
        def __init__(self):
            self.calls = 0

        def request_payment(self, *args, **kwargs):
            self.calls += 1
            raise RuntimeError("bank down")

    fake_client = FailingBankClient()

    # capture alert sends
    alerts = []

    def fake_alert(payload, locale=None, channels=None):
        alerts.append(payload)
        return {"status": "sent"}

    monkeypatch.setattr('pesaguard_backend_pipeline.settlement_engine.SessionLocal', lambda read_only=False: type('S', (), {'add': lambda *a, **k: None, 'flush': lambda *a, **k: None, 'commit': lambda *a, **k: None, 'rollback': lambda *a, **k: None, 'close': lambda *a, **k: None})())
    monkeypatch.setattr('pesaguard_backend_pipeline.settlement_engine.notifier.send_routed_alert', fake_alert)

    rows = [{"reference": "INV-FAIL", "amount": 10.0, "account_number": "111"}]
    summary = engine.settle_unmatched_ledger(rows, bank_client=fake_client, dry_run=False, max_retries=1, backoff_base_seconds=0.01)

    # two attempts (initial + 1 retry)
    assert fake_client.calls == 2
    assert summary["attempted"] == 1
    assert len(alerts) == 1
