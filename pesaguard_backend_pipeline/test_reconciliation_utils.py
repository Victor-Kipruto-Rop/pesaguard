import base64
import hashlib
import hmac

from reconciliation_utils import (
    exact_match,
    find_exact_match,
    normalize_daraja_event,
    parse_daraja_time,
    time_window_match,
)
from shared.daraja.validator import compute_hmac, validate_daraja_callback, validate_signature


def test_normalize_daraja_event_flattens_stk_callback():
    event = {
        "Body": {
            "stkCallback": {
                "CheckoutRequestID": "ws_CO_001",
                "CallbackMetadata": {
                    "Item": [
                        {"Name": "Amount", "Value": 100.0},
                        {"Name": "MpesaReceiptNumber", "Value": "RCP123"},
                        {"Name": "PhoneNumber", "Value": "254700000000"},
                        {"Name": "TransactionDate", "Value": "20240601120000"},
                        {"Name": "AccountReference", "Value": "INV-10"},
                    ]
                },
            }
        }
    }

    normalized = normalize_daraja_event(event)

    assert normalized["TransID"] == "RCP123"
    assert normalized["TransAmount"] == 100.0
    assert normalized["MSISDN"] == "254700000000"
    assert normalized["BillRefNumber"] == "INV-10"
    assert normalized["TransTime"] == "20240601120000"


def test_parse_daraja_time_supports_daraja_and_iso():
    assert parse_daraja_time("20240601120000").isoformat() == "2024-06-01T12:00:00+00:00"
    assert parse_daraja_time("2024-06-01T12:00:00Z").isoformat() == "2024-06-01T12:00:00+00:00"


def test_exact_and_find_exact_match():
    event = {"TransAmount": "100", "MSISDN": "254700000000", "BillRefNumber": "INV-1"}
    records = [
        {"amount": 99.0, "phone_number": "254700000000", "reference": "INV-1"},
        {"amount": 100.0, "phone_number": "254700000000", "reference": "INV-1"},
    ]

    assert exact_match(event, records[1]) is True
    assert find_exact_match(event, records) == records[1]


def test_time_window_match_returns_record_within_window():
    event = {"TransTime": "20240601120000"}
    records = [
        {"timestamp": "2024-06-01T11:40:00Z"},
        {"timestamp": "2024-06-01T12:10:00Z"},
    ]

    assert time_window_match(event, records, window_minutes=15) == records[1]


def test_validate_signature_accepts_hex_signature():
    payload = b'{"TransID":"T1","TransAmount":100}'
    secret = "top-secret"
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    assert compute_hmac(payload, secret) == expected
    assert validate_signature(payload, expected, secret) is True


def test_validate_signature_accepts_base64_and_prefixed_hex_headers():
    payload = b'{"TransID":"T2","TransAmount":200}'
    secret = "top-secret"
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).digest()

    assert validate_signature(payload, base64.b64encode(digest).decode("utf-8"), secret) is True
    assert validate_daraja_callback(payload, {"X-Daraja-Signature": f"sha256={digest.hex()}"}, secret) is True
