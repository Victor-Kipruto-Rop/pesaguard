"""
Thin wrapper around the Kafka producer so the webhook receiver
doesn't need to know about serialization details.
"""
import json
import os
from functools import lru_cache

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


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
    producer = get_producer()
    key = str(payload.get("TransID", "")).encode("utf-8")
    producer.send(topic, key=key, value=payload)
    producer.flush(timeout=5)
