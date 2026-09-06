import os

import jwt
from sqlalchemy import create_engine

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_auth_rbac_tokens_v2.db")

if os.environ["DATABASE_URL"].startswith("sqlite:///./test_auth_rbac_tokens_v2.db"):
    try:
        os.remove("test_auth_rbac_tokens_v2.db")
    except FileNotFoundError:
        pass

from pesaguard_backend_pipeline.auth_rbac import (
    ALGORITHM,
    JWT_AUDIENCE,
    JWT_ISSUER,
    SECRET_KEY,
    AuthRBAC,
    _RevocationBase,
    IdentityAccessService,
)
from pesaguard_backend_pipeline.models import Base, UserAccount

_test_engine = create_engine(os.environ["DATABASE_URL"])
Base.metadata.create_all(_test_engine)
_RevocationBase.metadata.create_all(_test_engine)


def test_access_and_refresh_tokens_are_distinguished():
    user_id = "user-123"
    username = "alice"
    tenant_id = "tenant-a"
    roles = ["admin"]

    access_token = AuthRBAC.generate_token(user_id, username, tenant_id, roles)
    refresh_token = AuthRBAC.generate_refresh_token(user_id, username, tenant_id, roles)

    assert AuthRBAC.verify_token(access_token) is not None
    assert AuthRBAC.verify_refresh_token(refresh_token) is not None
    assert AuthRBAC.verify_token(refresh_token) is None
    assert AuthRBAC.verify_refresh_token(access_token) is None


def test_refresh_tokens_rotate_and_reuse_revokes_family():
    refresh_token = AuthRBAC.generate_refresh_token(
        "user-456",
        "bob",
        "tenant-b",
        ["operator"],
        device_id="device-1",
    )

    rotated = AuthRBAC.rotate_refresh_token(refresh_token, device_id="device-1")
    assert rotated is not None
    _, replacement_token = rotated
    assert AuthRBAC.verify_refresh_token(refresh_token) is None
    assert AuthRBAC.verify_refresh_token(replacement_token) is not None

    assert AuthRBAC.rotate_refresh_token(refresh_token, device_id="device-1") is None
    assert AuthRBAC.verify_refresh_token(replacement_token) is None


def test_tokens_with_wrong_issuer_or_audience_are_rejected():
    access_token = AuthRBAC.generate_token("user-789", "carol", "tenant-c", ["read-only"])
    payload = jwt.decode(access_token, options={"verify_signature": False})

    payload["iss"] = "other-service"
    wrong_issuer_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    assert AuthRBAC.verify_token(wrong_issuer_token) is None

    payload["iss"] = JWT_ISSUER
    payload["aud"] = "other-api"
    wrong_audience_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    assert AuthRBAC.verify_token(wrong_audience_token) is None

    assert JWT_AUDIENCE != "other-api"


def test_tokens_missing_required_claims_are_rejected():
    access_token = AuthRBAC.generate_token("user-999", "dana", "tenant-d", ["read-only"])
    payload = jwt.decode(access_token, options={"verify_signature": False})

    payload_without_jti = dict(payload)
    del payload_without_jti["jti"]
    assert AuthRBAC.verify_token(jwt.encode(payload_without_jti, SECRET_KEY, algorithm=ALGORITHM)) is None

    payload_without_exp = dict(payload)
    del payload_without_exp["exp"]
    assert AuthRBAC.verify_token(jwt.encode(payload_without_exp, SECRET_KEY, algorithm=ALGORITHM)) is None


def test_tenant_access_requires_explicit_global_permission():
    tenant_admin = IdentityAccessService.create_principal("u1", "alice", "tenant-a", ["admin"])
    platform_admin = IdentityAccessService.create_principal("u2", "root", "tenant-a", ["platform-admin"])

    assert AuthRBAC.check_tenant_access(tenant_admin, "tenant-b") is False
    assert AuthRBAC.check_tenant_access(platform_admin, "tenant-b") is True


def test_token_issuance_normalizes_roles_and_rejects_unknown_roles():
    token = AuthRBAC.generate_token("u3", "bob", "tenant-a", [" Admin ", "admin"])
    payload = jwt.decode(token, options={"verify_signature": False})
    assert payload["roles"] == ["admin"]
    assert payload["permissions"] == sorted(payload["permissions"])

    try:
        AuthRBAC.generate_token("u4", "eve", "tenant-a", ["admn"])
    except ValueError:
        pass
    else:
        raise AssertionError("Unknown roles must not receive tokens")


def test_disabled_or_stale_persisted_accounts_cannot_use_access_tokens():
    session = __import__("sqlalchemy.orm", fromlist=["sessionmaker"]).sessionmaker(bind=_test_engine)()
    account = UserAccount(
        id="persisted-user",
        tenant_id="tenant-a",
        username="persisted",
        roles=["operator"],
        permissions=[],
        status="active",
        authorization_version=1,
    )
    account = session.merge(account)
    session.commit()
    token = AuthRBAC.generate_token("persisted-user", "persisted", "tenant-a", ["operator"])

    account.status = "disabled"
    session.commit()
    assert AuthRBAC.verify_token(token) is None

    account.status = "active"
    account.authorization_version = 2
    session.commit()
    assert AuthRBAC.verify_token(token) is None
    session.close()
