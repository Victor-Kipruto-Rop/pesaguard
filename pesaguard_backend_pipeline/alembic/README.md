Alembic migration scripts for PesaGuard.

This directory contains Alembic environment configuration. Use the `alembic` CLI
from the project root to create and apply migrations. Ensure `DATABASE_URL` is
set in the environment or in `alembic.ini` before running migrations.

Example:

    export DATABASE_URL=postgresql://user:pass@localhost:5432/pesaguard
    alembic -c pesaguard_backend_pipeline/alembic.ini revision --autogenerate -m "create tables"
    alembic -c pesaguard_backend_pipeline/alembic.ini upgrade head
