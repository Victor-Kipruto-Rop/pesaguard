"""Test bootstrap for repository-wide pytest execution.

This project intentionally fails closed when security credentials are not configured,
so the default test environment must provide minimal safe values before any modules
are imported during collection.
"""

import os

import pytest

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-0123456789abcdef")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_auth_rbac_tokens_v2.db")
os.environ.setdefault("PYTEST_TEST_DB_URL", "sqlite:///./test_auth_rbac_tokens_v2.db")
os.environ.setdefault("PESAGUARD_API_AUTH_REQUIRED", "0")
os.environ.setdefault("DARAJA_SHARED_SECRET", "test-daraja-shared-secret")
os.environ.setdefault("DARAJA_ALLOWED_IPS", "127.0.0.1,::1")
os.environ.setdefault("PESAGUARD_ALLOW_UNRESTRICTED_WEBHOOK_SOURCE", "1")


@pytest.fixture(scope="session", autouse=True)
def provision_auth_schema_for_tests():
	"""Provision migrated auth tables explicitly; production uses Alembic."""
	from sqlalchemy import create_engine
	from pesaguard_backend_pipeline.auth_rbac import _RevocationBase

	database_url = os.environ["DATABASE_URL"]
	engine = create_engine(
		database_url,
		connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
	)
	_RevocationBase.metadata.create_all(engine)
	engine.dispose()
