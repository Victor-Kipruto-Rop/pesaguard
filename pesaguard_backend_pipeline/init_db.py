"""
One-shot initialization script to construct database tables for PesaGuard.

Deployment / Usage:
  python3 init_db.py
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Add project root directory dynamically to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine
from pesaguard_backend_pipeline.models import Base  # noqa: E402

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")


def main():
    connect_args = {}
    if DATABASE_URL.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    elif DATABASE_URL.startswith("postgresql"):
        connect_args["connect_timeout"] = int(os.getenv("DB_CONNECT_TIMEOUT", "5"))

    logger.info("Initializing database schema on %s...", DATABASE_URL.split("@")[-1])

    try:
        engine = create_engine(DATABASE_URL, connect_args=connect_args)
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully.")
    except Exception as exc:
        logger.error("Failed to initialize database tables: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
