import os
from datetime import datetime, timezone, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pesaguard_backend_pipeline.models import Base, Discrepancy


def main() -> None:
    engine = create_engine(os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5433/pesaguard_staging"))
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as session:
        session.query(Discrepancy).delete()
        session.add_all([
            Discrepancy(
                id="stg-1",
                trans_id="STG-001",
                tenant_id="staging-tenant",
                anomaly_type="duplicate",
                severity="warning",
                status="needs_review",
                resolved=False,
                detected_at=datetime.now(timezone.utc) - timedelta(minutes=10),
            ),
            Discrepancy(
                id="stg-2",
                trans_id="STG-002",
                tenant_id="staging-tenant",
                anomaly_type="missing_payment",
                severity="critical",
                status="needs_review",
                resolved=False,
                detected_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            ),
        ])
        session.commit()
    print("Seeded staging disputes")


if __name__ == "__main__":
    main()
