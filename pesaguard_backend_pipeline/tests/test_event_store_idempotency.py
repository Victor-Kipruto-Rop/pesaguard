import threading
import tempfile
import os
import time
import sys
import pathlib

# Ensure repo root is on sys.path for imports in test env
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pesaguard_backend_pipeline.event_store import EventStore, ProcessResult


def _make_payload(trans_id: str):
    return {"TransID": trans_id, "TransAmount": "100", "MSISDN": "254700000000", "BusinessShortCode": "12345", "TransTime": "20220101120000"}


def test_mark_processed_concurrent(tmp_path):
    db_file = tmp_path / "es_test.db"
    db_url = f"sqlite:///{db_file}"

    es = EventStore(database_url=db_url)

    results = []
    lock = threading.Lock()
    barrier = threading.Barrier(2)

    def worker():
        barrier.wait()
        res = es.mark_processed(_make_payload("T12345"), tenant_id="test-tenant")
        with lock:
            results.append(res)

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # We expect one STORED and one DUPLICATE (order may vary)
    statuses = {r for r in results}
    assert ProcessResult.STORED in statuses
    assert ProcessResult.DUPLICATE in statuses


if __name__ == "__main__":
    test_mark_processed_concurrent(tempfile.gettempdir())
