"""
One-shot script to create tables for the MVP.
Swap for Alembic once the schema starts changing often.
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "models"))

from sqlalchemy import create_engine
from models import Base  # noqa: E402

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")


def main():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    print(f"Tables created at {DATABASE_URL}")


if __name__ == "__main__":
    main()
