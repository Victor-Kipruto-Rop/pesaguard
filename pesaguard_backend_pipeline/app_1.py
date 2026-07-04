"""
Minimal read-only API for viewing reconciliation status.
For the MVP pilot, skip building a full frontend — this can be
consumed directly, or wired into Retool/Django admin.
"""
import os

from flask import Flask, jsonify
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "storage", "models"))
from models import Base, Transaction, Discrepancy  # noqa: E402

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")

app = Flask(__name__)
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


@app.route("/api/discrepancies", methods=["GET"])
def list_discrepancies():
    session = Session()
    try:
        rows = session.execute(
            select(Discrepancy).where(Discrepancy.resolved.is_(False)).order_by(Discrepancy.detected_at.desc())
        ).scalars().all()
        return jsonify([
            {
                "id": r.id,
                "trans_id": r.trans_id,
                "anomaly_type": r.anomaly_type,
                "details": r.details,
                "detected_at": r.detected_at.isoformat() if r.detected_at else None,
            }
            for r in rows
        ])
    finally:
        session.close()


@app.route("/api/stats/summary", methods=["GET"])
def summary():
    session = Session()
    try:
        total_transactions = session.query(Transaction).count()
        open_discrepancies = session.query(Discrepancy).filter_by(resolved=False).count()
        return jsonify({
            "total_transactions": total_transactions,
            "open_discrepancies": open_discrepancies,
            "reconciliation_rate": (
                round(1 - (open_discrepancies / total_transactions), 4)
                if total_transactions else None
            ),
        })
    finally:
        session.close()


if __name__ == "__main__":
    port = int(os.getenv("DASHBOARD_API_PORT", 5001))
    app.run(host="0.0.0.0", port=port)
