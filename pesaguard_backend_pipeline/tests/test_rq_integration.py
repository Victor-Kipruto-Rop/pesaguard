import os
import pathlib
import sys
from unittest.mock import MagicMock

# Ensure repo root is on sys.path for imports in test env
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import redis
from rq import Queue, SimpleWorker

from pesaguard_backend_pipeline.scripts import rq_worker
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
    q = Queue(name=os.getenv("RQ_QUEUE_NAME", "transaction_events"), connection=r)
    q.enqueue(
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


def test_rq_worker_main_uses_environment_defaults(monkeypatch):
    fake_redis = MagicMock()
    fake_redis.from_url.return_value = object()

    fake_queue = MagicMock()
    fake_worker = MagicMock()
    fake_worker.work.return_value = None

    monkeypatch.setattr(rq_worker.redis, "from_url", fake_redis.from_url)
    monkeypatch.setattr(rq_worker, "Queue", lambda name, connection=None: fake_queue)
    monkeypatch.setattr(rq_worker, "Worker", lambda queues, connection=None: fake_worker)

    rq_worker.main()

    fake_redis.from_url.assert_called_once_with(rq_worker.REDIS_URL)
    fake_queue.name = rq_worker.RQ_QUEUE_NAME
    fake_worker.work.assert_called_once_with()
