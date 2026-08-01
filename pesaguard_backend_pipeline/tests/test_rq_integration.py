import os
import time
import tempfile
import pathlib
import sys

# Ensure repo root is on sys.path for imports in test env
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import redis
from rq import Queue, Connection, SimpleWorker
from pesaguard_backend_pipeline.scripts.test_tasks import write_marker


def test_rq_worker_writes_marker(tmp_path):
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        r = redis.from_url(redis_url)
        r.ping()
    except Exception:
        import pytest

        pytest.skip("Redis not available; skipping RQ integration test")

    marker = tmp_path / "marker.txt"
    # Enqueue job
    with Connection(r):
        q = Queue(name=os.getenv("RQ_QUEUE_NAME", "transaction_events"), connection=r)
        job = q.enqueue(
            "pesaguard_backend_pipeline.scripts.test_tasks.write_marker",
            str(marker),
            "done",
        )

        # Process queue synchronously in-process
        worker = SimpleWorker([q], connection=r)
        worker.work(burst=True)

    # verify marker file exists
    assert marker.exists()
    assert marker.read_text() == "done"
