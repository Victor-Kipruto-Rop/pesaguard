from reconciliation_engine import evaluate_transaction
from reconciliation_scoring import score_match


def _event(**overrides):
    payload = {
        "TransID": "ABC123",
        "BillRefNumber": "INV-10",
        "TransAmount": "100",
        "MSISDN": "254700000001",
        "TransTime": "20240601120000",
    }
    payload.update(overrides)
    return payload


def _record(**overrides):
    rec = {
        "internal_ref": "INV-10",
        "amount": 100.0,
        "phone_number": "254700000001",
        "timestamp": "2024-06-01T12:00:00Z",
    }
    rec.update(overrides)
    return rec


def test_score_match_returns_score_and_reasons():
    score, reasons = score_match(_event(), _record())

    assert 0.0 <= score <= 1.0
    assert "components" in reasons
    assert "matched_features" in reasons
    assert reasons["components"]["phone_match"] == 1.0


def test_evaluate_transaction_includes_explainability_for_match():
    result = evaluate_transaction(_event(), [_record()], seen_trans_ids=set())

    assert result["status"] == "matched"
    assert "score" in result["match"]
    assert "reasons" in result["match"]


def test_evaluate_transaction_includes_explainability_for_review():
    result = evaluate_transaction(
        _event(MSISDN="254700000099"),
        [_record(phone_number="254700000001")],
        seen_trans_ids=set(),
    )

    assert result["status"] == "needs_review"
    assert "score" in result["match"]
    assert "reasons" in result["match"]
