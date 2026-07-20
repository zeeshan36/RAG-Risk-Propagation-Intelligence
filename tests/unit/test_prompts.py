"""Tests for Jinja2 prompt templates."""
from rag_pipeline.prompts.loader import (
    render_impact_analysis,
    render_mitigation_plan,
    render_vulnerability_review,
)


def test_render_impact_analysis():
    context = {
        "event": {
            "id": "EV1",
            "type": "PortClosure",
            "severity": "high",
            "expected_duration_hours": 48,
        },
        "impacted_entities": [{"entity_type": "Shipment", "entity_id": "SH1"}],
        "context_docs": [{"text": "Port closure playbook"}],
    }
    text = render_impact_analysis(context)
    assert "EV1" in text
    assert "PortClosure" in text
    assert "SH1" in text


def test_render_mitigation_plan():
    context = {
        "event": {"id": "EV1", "type": "PortClosure", "severity": "high"},
        "impacted_entities": [{"entity_type": "Shipment", "entity_id": "SH1"}],
    }
    text = render_mitigation_plan(context)
    assert "mitigation" in text.lower() or "recommend" in text.lower()


def test_render_vulnerability_review():
    context = {
        "question": "What are the bottlenecks?",
        "graph_nodes": [{"type": "Route", "id": "R1", "name": "Route 1"}],
    }
    text = render_vulnerability_review(context)
    assert "bottlenecks" in text.lower()
