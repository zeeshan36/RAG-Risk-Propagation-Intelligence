"""Streaming event consumer adapters."""
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from common.logging import get_logger
from events.classification.classifier import classify_event
from events.propagation.engine import PropagationEngine

logger = get_logger("streaming.consumer")


class EventConsumer(ABC):
    """Abstract event consumer."""

    @abstractmethod
    def consume(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Start consuming events and dispatch them to handler."""

    @abstractmethod
    def close(self) -> None:
        """Stop and clean up the consumer."""


class HttpEventConsumer(EventConsumer):
    """HTTP-based fallback consumer.

    In minimal mode events are received directly via the `/events` HTTP endpoint.
    This consumer simply records that it is available and provides idempotency
    helpers.
    """

    def __init__(self) -> None:
        self._seen_keys: set = set()

    def is_duplicate(self, idempotency_key: str) -> bool:
        if idempotency_key in self._seen_keys:
            return True
        self._seen_keys.add(idempotency_key)
        return False

    def consume(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        logger.info("HTTP event consumer is passive; receive events via POST /events")

    def close(self) -> None:
        self._seen_keys.clear()


class KafkaEventConsumer(EventConsumer):
    """Kafka consumer for streaming events.

    Requires the optional `kafka-python-ng` dependency.
    """

    def __init__(
        self,
        bootstrap_servers: List[str],
        topic: str,
        group_id: str,
        propagation_engine: Optional[PropagationEngine] = None,
    ) -> None:
        try:
            from kafka import KafkaConsumer
        except ImportError as exc:
            raise ImportError(
                "KafkaEventConsumer requires kafka-python-ng to be installed "
                "(pip install rag-risk-propagation[kafka])."
            ) from exc
        self._consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: m.decode("utf-8"),
        )
        self._topic = topic
        self._propagation_engine = propagation_engine
        self._running = False

    def consume(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        import json

        self._running = True
        logger.info("Starting Kafka consumer", extra={"topic": self._topic})
        try:
            for message in self._consumer:
                if not self._running:
                    break
                try:
                    payload = json.loads(message.value)
                    handler(payload)
                except Exception:
                    logger.exception("Failed to process Kafka message")
        finally:
            self._consumer.close()

    def close(self) -> None:
        self._running = False
        self._consumer.close()


def build_consumer(
    settings,
    propagation_engine: Optional[PropagationEngine] = None,
) -> EventConsumer:
    """Factory that returns the appropriate consumer for the feature flags."""
    if settings.features.use_kafka_events:
        return KafkaEventConsumer(
            bootstrap_servers=["localhost:9092"],
            topic="supply-chain-events",
            group_id="rag-risk-propagation",
            propagation_engine=propagation_engine,
        )
    return HttpEventConsumer()


def default_handler(
    payload: Dict[str, Any],
    repo: Any,
    propagation_engine: PropagationEngine,
) -> Dict[str, Any]:
    """Default synchronous handler: classify, store, propagate."""
    event = classify_event(payload)
    repo.upsert(event)
    impact = propagation_engine.propagate(event)
    return {
        "event_id": event.id,
        "event_type": event.type,
        "impacted_entities": len(impact.impacted_entities),
    }
