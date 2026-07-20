"""Tests for canonical domain and event models."""
from decimal import Decimal

import pytest
from pydantic import TypeAdapter, ValidationError

from models.domain import Customer, Facility, FacilityType, Order, Port, Product, Route, RouteMode, Shipment, ShipmentStatus, Supplier
from models.events import CyberIncident, Event, ExportControl, ExtremeWeather, PoliticalUnrest, PortClosure, Severity


def test_supplier_validation():
    supplier = Supplier(id="S1", name="Acme", country="US", criticality_score=0.8)
    assert supplier.criticality_score == 0.8


def test_supplier_score_out_of_range():
    with pytest.raises(ValidationError):
        Supplier(id="S1", name="Acme", country="US", criticality_score=1.5)


def test_facility_and_port():
    facility = Facility(id="F1", type=FacilityType.FACTORY, name="Factory A", region_id="R1", lat=10.0, lon=20.0)
    assert facility.type == FacilityType.FACTORY
    port = Port(id="P1", name="Port A", region_id="R1", modes=[RouteMode.SEA])
    assert RouteMode.SEA in port.modes


def test_route_order_shipment():
    route = Route(id="R1", origin_node_id="P1", destination_node_id="F1", mode=RouteMode.SEA, avg_lead_time_days=5, capacity=100)
    assert route.avg_lead_time_days == 5
    order = Order(id="O1", customer_id="C1", product_id="PR1", quantity=10, revenue=Decimal("1000.00"), margin=Decimal("200.00"))
    assert order.revenue == Decimal("1000.00")
    shipment = Shipment(id="SH1", order_id="O1", route_ids=["R1"], carrier_id="CAR1", status=ShipmentStatus.PLANNED)
    assert shipment.route_ids == ["R1"]


def test_event_union_discriminates():
    raw = {"id": "EV1", "type": "PortClosure", "port_id": "P1", "severity": "high"}
    event = TypeAdapter(Event).validate_python(raw)
    assert isinstance(event, PortClosure)
    assert event.port_id == "P1"


def test_all_event_subtypes():
    events = [
        PortClosure(id="E1", port_id="P1"),
        ExtremeWeather(id="E2", hazard_type="flood", center_lat=0.0, center_lon=0.0, radius_deg=5.0),
        CyberIncident(id="E3", provider_id="PRV1"),
        ExportControl(id="E4", material_id="M1"),
        PoliticalUnrest(id="E5", region_id="R1"),
    ]
    for event in events:
        assert event.severity in Severity
