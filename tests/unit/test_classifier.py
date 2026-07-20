"""Tests for event classification."""
import pytest

from common.exceptions import EventProcessingError
from events.classification.classifier import classify_event
from models.events import CyberIncident, ExportControl, PortClosure


def test_classify_port_closure():
    raw = {"id": "E1", "type": "PortClosure", "port_id": "P1", "severity": "high"}
    event = classify_event(raw)
    assert isinstance(event, PortClosure)
    assert event.port_id == "P1"


def test_classify_cyber_incident():
    raw = {"id": "E2", "type": "CyberIncident", "provider_id": "PRV1"}
    event = classify_event(raw)
    assert isinstance(event, CyberIncident)


def test_classify_invalid_without_llm():
    raw = {"id": "E3", "type": "UnknownType"}
    with pytest.raises(EventProcessingError):
        classify_event(raw)
