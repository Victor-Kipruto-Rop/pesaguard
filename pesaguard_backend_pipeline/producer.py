"""
Thin wrapper around the Kafka producer so the webhook receiver
doesn't need to know about serialization details.
"""
import json
import logging
import os
from functools import lru_cache

logger = logging.getLogger("pesaguard.producer")

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
PRODUCER_SEND_TIMEOUT_SECONDS = int(os.getenv("PESAGUARD_PRODUCER_SEND_TIMEOUT_SECONDS", "10"))


@lru_cache(maxsize=1)
def get_producer():
    try:
        from kafka import KafkaProducer
    except ImportError as exc:
        raise ImportError(
            "Kafka producer is unavailable. Install kafka-python or configure the environment "
            "for message publication."
        ) from exc

    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        retries=5,
        acks="all",
    )


def publish_transaction_event(topic: str, payload: dict) -> None:
    """Publish a transaction event, raising if it genuinely failed to send.

    FIXED: previously called producer.flush() and returned, with no check on
    the Future that send() returns. flush() waits for all pending sends to
    finish (success OR failure) but does NOT raise for an individual message
    that failed after exhausting retries — that failure only lives on its
    Future object. Callers (e.g. app.py's webhook handler) wrap this call in
    a try/except specifically to log "failed to publish, queued for manual
    replay" — but that except block could never fire for an actual Kafka
    delivery failure, only for errors during send() itself. A message could
    genuinely never reach Kafka while the caller logged "published
    successfully."

    Now: explicitly calls future.get(timeout=...) on the Future returned by
    send(), which DOES raise (a KafkaError or subclass) if the send
    ultimately failed — so a real delivery failure now actually propagates
    to the caller instead of being silently absorbed by flush().
    """
    producer = get_producer()

    trans_id = payload.get("TransID")
    # FIXED: an empty-but-not-None key (from a missing TransID) hashes to a
    # single, consistent Kafka partition under the default partitioner —
    # every malformed/missing-TransID event would pile onto the same
    # partition instead of distributing. Use None (round-robin) when there's
    # no real key to partition on.
    key = str(trans_id).encode("utf-8") if trans_id else None

    future = producer.send(topic, key=key, value=payload)
    producer.flush(timeout=PRODUCER_SEND_TIMEOUT_SECONDS)

    try:
        # This is what actually surfaces a delivery failure — raises on
        # timeout or on a genuine send error (e.g. all retries exhausted).
        future.get(timeout=PRODUCER_SEND_TIMEOUT_SECONDS)
    except Exception:
        logger.exception(
            "Kafka publish failed for trans_id=%s topic=%s — this event did "
            "NOT reach Kafka despite flush() completing without raising.",
            trans_id, topic,
        )
        raise
