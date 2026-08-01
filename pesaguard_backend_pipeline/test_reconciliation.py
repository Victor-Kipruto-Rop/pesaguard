from reconciliation_engine import evaluate_transaction
from reconciliation_utils import (
    exact_match,
    find_exact_match,
    normalize_daraja_event,
    parse_daraja_time,
    time_window_match,
)
from shared.daraja.validator import compute_hmac, validate_daraja_callback


def make_event(trans_id="T1", amount="100", phone="254700000000", trans_time="20240601120000"):
    return {
        "TransID": trans_id,
        "TransAmount": amount,
        "MSISDN": phone,
        "TransTime": trans_time,
        "BusinessShortCode": "12345",
    }


def make_internal_record(internal_ref="ORD-1", amount=100.0, phone="254700000000", timestamp="2024-06-01T12:00:00Z", status="pending"):
    return {
        "internal_ref": internal_ref,
        "amount": amount,
        "phone_number": phone,
        "timestamp": timestamp,
        "status": status,
    }


def test_exact_match_is_resolved():
    event = make_event(trans_id="T-100", amount="100", phone="254700000000", trans_time="20240601120000")
    internal_record = make_internal_record(timestamp="2024-06-01T12:00:00Z")

    result = evaluate_transaction(event, [internal_record], seen_trans_ids=set())

    assert result["status"] == "matched"
    assert result["severity"] == "info"
    assert result["match"]["match_type"] == "exact"


def test_partial_match_is_review_required():
    event = make_event(trans_id="T-200", amount="100", phone="254700000001", trans_time="20240601120000")
    internal_record = make_internal_record(internal_ref="ORD-2", phone="254700000000", timestamp="2024-06-01T12:00:00Z")

    result = evaluate_transaction(event, [internal_record], seen_trans_ids=set())

    assert result["status"] == "needs_review"
    assert result["severity"] == "warning"
    assert result["match"]["match_type"] in {"partial", "partial_fuzzy"}


def test_missing_payment_is_critical():
    event = make_event(trans_id="T-300", amount="100", phone="254700000002", trans_time="20240601130000")
    internal_record = make_internal_record(internal_ref="ORD-3", phone="254700000002", amount=100.0, timestamp="2024-06-01T11:00:00Z")

    result = evaluate_transaction(event, [internal_record], seen_trans_ids=set(), window_minutes=15)

    assert result["status"] == "missing_payment"
    assert result["severity"] == "critical"


def test_duplicate_transaction_is_flagged_without_double_alerting():
    event = make_event(trans_id="T-400", amount="100", phone="254700000003", trans_time="20240601120000")
    internal_record = make_internal_record(internal_ref="ORD-4", phone="254700000003", timestamp="2024-06-01T12:00:00Z")

    result = evaluate_transaction(event, [internal_record], seen_trans_ids={"T-400"})

    assert "duplicate_transaction_id" in result["anomalies"]
    assert result["duplicate"] is True


def test_normalize_daraja_event_parses_core_fields():
    normalized = normalize_daraja_event(make_event(trans_id="T-500", amount="250.50", phone="254711111111"))

    assert normalized["trans_id"] == "T-500"
    assert normalized["amount"] == 250.50
    assert normalized["phone_number"] == "254711111111"
    assert normalized["timestamp"] == parse_daraja_time("20240601120000")


def test_exact_match_and_find_exact_match():
    event = normalize_daraja_event(make_event(trans_id="T-600", amount="100", phone="254722222222"))
    record = make_internal_record(internal_ref="ORD-6", amount=100.0, phone="254722222222", timestamp="2024-06-01T12:00:00Z")

    assert exact_match(event, {"amount": 100.0, "phone_number": "254722222222"}, tolerance_percent=0.0)
    best = find_exact_match(event, [record], tolerance_percent=0.5)
    assert best is not None
    assert best["match_type"] == "exact"
    assert best["internal_ref"] == "ORD-6"


def test_time_window_match_filters_old_record():
    event = normalize_daraja_event(make_event(trans_id="T-700", amount="100", phone="254733333333", trans_time="20240601120000"))
    old_record = make_internal_record(
        internal_ref="ORD-7",
        amount=100.0,
        phone="254733333333",
        timestamp="2024-06-01T10:00:00Z",
    )

    assert time_window_match(event, [old_record], window_minutes=15, tolerance_percent=0.5) is None


def test_daraja_hmac_hex_signature_validation():
    payload = {"TransID": "T-800", "TransAmount": "150", "MSISDN": "254744444444"}
    secret = "phase1_shared_secret"
    signature = compute_hmac(payload, secret, encoding="hex")

    assert validate_daraja_callback(payload, signature, secret) is True
    assert validate_daraja_callback(payload, "invalid-signature", secret) is False
