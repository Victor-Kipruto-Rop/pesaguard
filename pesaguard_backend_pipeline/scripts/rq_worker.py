#!/usr/bin/env python3
"""Simple RQ worker for local CI/dev to process `transaction_events` queue.

Run locally:

    REDIS_URL=redis://localhost:6379/0 python3 -m pesaguard_backend_pipeline.scripts.rq_worker

"""
import os
import redis
from rq import Worker, Queue, Connection

RQ_QUEUE_NAME = os.getenv("RQ_QUEUE_NAME", "transaction_events")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def main():
    redis_conn = redis.from_url(REDIS_URL)
    with Connection(redis_conn):
        q = Queue(name=RQ_QUEUE_NAME, connection=redis_conn)
        worker = Worker([q], connection=redis_conn)
        worker.work()


if __name__ == "__main__":
    main()
