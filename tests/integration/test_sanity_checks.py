"""Sanity checks for impact and analysis responses."""
from data_ingestion.batch.simple_repository import SimpleRepository
from events.propagation.engine import PropagationEngine
from models.domain import Customer, Facility, Order, Port, Product, Route, Shipment
from models.events import PortClosure


def _build_repo_with_event():
    repo = SimpleRepository()
    repo.load_many([
        Port(id="P1", name="Port A", region_id="R1"),
        Facility(id="F1", type="warehouse", name="WH1", region_id="R1"),
        Customer(id="C1", name="Customer A", region_id="R1", criticality_score=0.5),
        Product(id="PR1", name="Product A", sku="SKU1"),
        Route(id="R1", origin_node_id="P1", destination_node_id="F1", mode="sea", avg_lead_time_days=5, capacity=100),
        Order(id="O1", customer_id="C1", product_id="PR1", quantity=10),
        Shipment(id="SH1", order_id="O1", route_ids=["R1"], carrier_id="CAR1"),
    ])
    event = PortClosure(id="EV1", port_id="P1")
    repo.upsert(event)
    return repo, event


def test_disruptive_event_has_impacted_entities():
    repo, event = _build_repo_with_event()
    engine = PropagationEngine(repo=repo)
    impact = engine.propagate(event)
    assert len(impact.impacted_entities) > 0
    assert "SH1" in impact.impacted_shipment_ids


def test_event_outside_scope_has_no_impact():
    repo, _ = _build_repo_with_event()
    event = PortClosure(id="EV2", port_id="P_UNKNOWN")
    engine = PropagationEngine(repo=repo)
    impact = engine.propagate(event)
    assert len(impact.impacted_entities) == 0
