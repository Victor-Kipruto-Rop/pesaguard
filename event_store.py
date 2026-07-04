"""A lightweight durable event store for idempotency and replay."""

import os
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Transaction


class EventStore:
    """Persist processed transactions so duplicate callbacks can be ignored safely."""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")
        self.engine = create_engine(self.database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def already_processed(self, trans_id: str) -> bool:
        with self.Session() as session:
            return session.query(Transaction).filter(Transaction.trans_id == trans_id).first() is not None

    def mark_processed(self, payload: dict) -> None:
        with self.Session() as session:
            existing = session.query(Transaction).filter(Transaction.trans_id == payload.get("TransID")).first()
            if existing:
                return
            record = Transaction(
                trans_id=str(payload.get("TransID", "")),
                trans_amount=float(payload.get("TransAmount", 0)),
                msisdn=str(payload.get("MSISDN", "")),
                business_short_code=str(payload.get("BusinessShortCode", "")),
                trans_time=str(payload.get("TransTime", "")),
                raw_payload=payload,
                created_at=datetime.now(timezone.utc),
            )
            session.add(record)
            session.commit()
