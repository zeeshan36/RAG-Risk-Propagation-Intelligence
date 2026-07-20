"""Tests for streaming consumer adapters."""
import pytest

from data_ingestion.batch.simple_repository import SimpleRepository
from data_ingestion.streaming.consumer import (
    HttpEventConsumer,
    KafkaEventConsumer,
    build_consumer,
    default_handler,
)
from events.propagation.engine import PropagationEngine


def test_http_event_consumer_idempotency():
    consumer = HttpEventConsumer()
    assert consumer.is_duplicate("key1") is False
    assert consumer.is_duplicate("key1") is True
    consumer.close()
    assert "key1" not in consumer._seen_keys


def test_build_consumer_http_fallback():
    from config.loader import Settings

    settings = Settings()
    consumer = build_consumer(settings)
    assert isinstance(consumer, HttpEventConsumer)


def test_kafka_consumer_requires_dependency():
    try:
        import kafka  # noqa: F401
    except ImportError:
        with pytest.raises(ImportError):
            KafkaEventConsumer(bootstrap_servers=["localhost:9092"], topic="t", group_id="g")
