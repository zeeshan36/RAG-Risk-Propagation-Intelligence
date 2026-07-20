"""Tests for rule-based propagation."""
from data_ingestion.batch.simple_repository import SimpleRepository
from events.propagation.engine import PropagationEngine
from models.domain import Customer, Facility, Order, Port, Product, Route, Shipment
from models.events import PortClosure, CyberIncident, ExportControl


def _make_minimal_network():
    repo = SimpleRepository()
    repo.load_many([
        Port(id="P1", name="Port A", region_id="R1"),
        Facility(id="F1", type="warehouse", name="WH1", region_id="R1"),
        Customer(id="C1", name="Customer A", region_id="R1", criticality_score=0.5),
        Product(id="PR1", name="Product A", sku="SKU1", bom_material_ids=["M1"]),
        Route(id="R1", origin_node_id="P1", destination_node_id="F1", mode="sea", avg_lead_time_days=5, capacity=100),
        Order(id="O1", customer_id="C1", product_id="PR1", quantity=10),
        Shipment(id="SH1", order_id="O1", route_ids=["R1"], carrier_id="CAR1"),
    ])
    return repo


def test_port_closure_propagation():
    repo = _make_minimal_network()
    engine = PropagationEngine(repo=repo)
    event = PortClosure(id="E1", port_id="P1")
    impact = engine.propagate(event)
    assert "SH1" in impact.impacted_shipment_ids
    assert "O1" in impact.impacted_order_ids
    assert "C1" in impact.impacted_customer_ids
    assert "R1" in impact.impacted_route_ids


def test_cyber_incident_propagation():
    repo = _make_minimal_network()
    engine = PropagationEngine(repo=repo)
    event = CyberIncident(id="E2", provider_id="CAR1")
    impact = engine.propagate(event)
    assert "SH1" in impact.impacted_shipment_ids
    assert "O1" in impact.impacted_order_ids


def test_export_control_propagation():
    repo = _make_minimal_network()
    engine = PropagationEngine(repo=repo)
    event = ExportControl(id="E3", material_id="M1")
    impact = engine.propagate(event)
    assert "PR1" in impact.impacted_product_ids
    assert "O1" in impact.impacted_order_ids
