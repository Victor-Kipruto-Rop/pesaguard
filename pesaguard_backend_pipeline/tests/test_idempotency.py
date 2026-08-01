from idempotency import derive_idempotency_key


def test_transid_based_key_is_deterministic():
    payload_a = {"TransID": "abc123", "TransAmount": "10"}
    payload_b = {"TransID": "ABC123", "TransAmount": "99"}

    assert derive_idempotency_key(payload_a) == derive_idempotency_key(payload_b)


def test_hash_based_key_changes_with_material_fields():
    base = {"MSISDN": "254700000001", "TransAmount": "10", "TransTime": "20240601120000"}
    changed = {"MSISDN": "254700000001", "TransAmount": "11", "TransTime": "20240601120000"}

    assert derive_idempotency_key(base) != derive_idempotency_key(changed)


def test_hash_based_key_is_stable_across_time_formats():
    payload_a = {"msisdn": "254700000001", "amount": 10, "timestamp": "2024-06-01T12:00:00Z"}
    payload_b = {"MSISDN": "254700000001", "TransAmount": "10.00", "TransTime": "20240601120000"}

    assert derive_idempotency_key(payload_a) == derive_idempotency_key(payload_b)
