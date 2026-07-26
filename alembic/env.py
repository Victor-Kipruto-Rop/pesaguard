"""Alembic environment configuration for PesaGuard database migrations."""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Ensure application modules can be resolved for autogenerate support
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from models import Base  # type: ignore
except ImportError:
    try:
        from pesaguard_backend_pipeline.models import Base  # type: ignore
    except ImportError as exc:
        raise ImportError(f"Could not import Base metadata for Alembic autogenerate: {exc}")

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL and not an Engine, though an
    Engine is acceptable here as well. By skipping engine creation
    we don't even need a DB connection to generate SQL scripts.
    """
    url = config.get_main_option("sqlalchemy.url") or os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError("Database URL not specified for offline migrations.")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection
    with the context.
    """
    ini_section = config.get_section(config.config_ini_section) or {}
    
    # Fallback to environment variable DATABASE_URL if alembic.ini lacks sqlalchemy.url
    database_url = os.environ.get("DATABASE_URL")
    if database_url and "sqlalchemy.url" not in ini_section:
        ini_section["sqlalchemy.url"] = database_url

    connectable = engine_from_config(
        ini_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Detect column type changes during autogenerate
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
