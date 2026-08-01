import os
import sys
import json
import pytest

PACKAGE_DIR = os.path.dirname(os.path.dirname(__file__))
ROOT = os.path.dirname(PACKAGE_DIR)

if PACKAGE_DIR not in sys.path:
    sys.path.insert(0, PACKAGE_DIR)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Disable API auth for tests by default (unless explicitly enabled)
if not os.getenv("PESAGUARD_API_AUTH_REQUIRED"):
    os.environ["PESAGUARD_API_AUTH_REQUIRED"] = "0"

# Configure test authentication users if not already set
if not os.getenv("PESAGUARD_AUTH_USERS_JSON"):
    test_users = [
        {
            "username": "testuser",
            "tenant_id": "test-tenant",
            "roles": ["operator"],
            "salt_hex": "5593d5134da0e11444610cc0f3b23e62",
            "password_hash_hex": "6771168160abccd69654f6a9cf8697409e4cb4c7c0075cdeccbc4bb9b821349d",
        },
        {
            "username": "admin",
            "tenant_id": "test-tenant",
            "roles": ["admin"],
            "salt_hex": "5593d5134da0e11444610cc0f3b23e62",
            "password_hash_hex": "6771168160abccd69654f6a9cf8697409e4cb4c7c0075cdeccbc4bb9b821349d",
        },
    ]
    os.environ["PESAGUARD_AUTH_USERS_JSON"] = json.dumps(test_users)


@pytest.fixture
def admin_token():
    """Generate admin JWT token."""
    from pesaguard_backend_pipeline.auth_rbac import AuthRBAC
    return AuthRBAC.generate_token(
        user_id="user_admin",
        username="admin",
        tenant_id="test-tenant",
        roles=["admin"],
    )


@pytest.fixture
def operator_token():
    """Generate operator JWT token."""
    from pesaguard_backend_pipeline.auth_rbac import AuthRBAC
    return AuthRBAC.generate_token(
        user_id="user_operator",
        username="operator1",
        tenant_id="test-tenant",
        roles=["operator"],
    )
