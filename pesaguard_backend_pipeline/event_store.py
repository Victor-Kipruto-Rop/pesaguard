"""A lightweight durable event store for idempotency and replay."""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Transaction


class EventStore:
    """Persist processed transactions so duplicate callbacks can be ignored safely."""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")
        self.engine = None
        self.Session = None
        self._initialized = False

    def _ensure_ready(self) -> None:
        if self._initialized:
            return

        self.engine = create_engine(self.database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._initialized = True

    def already_processed(self, trans_id: str) -> bool:
        try:
            self._ensure_ready()
            with self.Session() as session:
                return session.query(Transaction).filter(Transaction.trans_id == trans_id).first() is not None
        except Exception:
            return False

    def mark_processed(self, payload: dict) -> None:
        try:
            self._ensure_ready()
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
        except Exception:
            pass

    def write_dead_letter(self, payload: dict | None, reason: str, error_detail: str | None = None, tenant_id: str | None = None) -> None:
        """Persist a malformed or rejected webhook payload to the dead-letter table for later inspection.

        This is intentionally best-effort and must not raise in the webhook hot path.
        """
        try:
            from models import DeadLetter

            self._ensure_ready()
            with self.Session() as session:
                dl = DeadLetter(
                    id=f"dl_{uuid.uuid4().hex[:12]}",
                    tenant_id=tenant_id,
                    reason=reason,
                    payload=payload,
                    error_detail=str(error_detail) if error_detail else None,
                    attempts=0,
                    processed=False,
                    processed_at=None,
                )
                session.add(dl)
                session.commit()
        except Exception:
            # Never raise from the hot path; best-effort logging only
            return
