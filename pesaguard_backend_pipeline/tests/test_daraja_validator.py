import base64
import hashlib
import hmac

from shared.daraja.validator import validate_signature


SECRET = "secret-key"
BODY = b'{"TransID":"ABC123"}'


def _hex_sig():
    return hmac.new(SECRET.encode("utf-8"), BODY, hashlib.sha256).hexdigest()


def _b64_sig():
    digest = hmac.new(SECRET.encode("utf-8"), BODY, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def test_accepts_hex_signature_case_insensitive():
    assert validate_signature(SECRET, BODY, _hex_sig().upper())
    assert validate_signature(SECRET, BODY, _hex_sig().lower())


def test_accepts_prefixed_hex_signature():
    assert validate_signature(SECRET, BODY, f"sha256={_hex_sig()}")


def test_accepts_base64_signature():
    assert validate_signature(SECRET, BODY, _b64_sig())


def test_rejects_invalid_signature():
    assert not validate_signature(SECRET, BODY, "sha256=deadbeef")
