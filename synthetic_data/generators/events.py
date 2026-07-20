"""Synthetic event generators with ground-truth labels."""
import random
import uuid
from typing import Dict, List, Tuple

from models.events import (
    CyberIncident,
    Event,
    ExportControl,
    ExtremeWeather,
    PoliticalUnrest,
    PortClosure,
    Severity,
)
from synthetic_data.generators.network import SupplyChainNetwork


def _make_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def generate_port_closure_event(
    network: SupplyChainNetwork, rng: random.Random
) -> Tuple[Event, Dict]:
    port = rng.choice(network.ports)
    event_id = _make_id("EV_PORTCLOSE")
    event = PortClosure(
        id=event_id,
        port_id=port.id,
        expected_duration_hours=rng.randint(24, 168),
        severity=rng.choice(list(Severity)),
        affected_operations="full",
    )

    impacted_routes = [
        r
        for r in network.routes
        if r.origin_node_id == port.id or r.destination_node_id == port.id
    ]
    impacted_route_ids = {r.id for r in impacted_routes}
    impacted_shipments = [
        s for s in network.shipments if any(rid in impacted_route_ids for rid in s.route_ids)
    ]
    ground_truth = {
        "event_id": event_id,
        "impacted_route_ids": list(impacted_route_ids),
        "impacted_shipment_ids": [s.id for s in impacted_shipments],
        "impacted_order_ids": list({s.order_id for s in impacted_shipments}),
    }
    return event, ground_truth


def generate_extreme_weather_event(
    network: SupplyChainNetwork, rng: random.Random
) -> Tuple[Event, Dict]:
    event_id = _make_id("EV_WEATHER")
    # Center the weather event near an existing facility so ground truth is non-empty.
    anchor = rng.choice(network.facilities)
    center_lat = (anchor.lat or 0.0) + rng.uniform(-1.0, 1.0)
    center_lon = (anchor.lon or 0.0) + rng.uniform(-1.0, 1.0)
    radius = 10.0

    event = ExtremeWeather(
        id=event_id,
        hazard_type=rng.choice(["flood", "storm", "heatwave"]),
        center_lat=center_lat,
        center_lon=center_lon,
        radius_deg=radius,
        severity=rng.choice([Severity.MEDIUM, Severity.HIGH]),
    )

    def in_circle(lat: float, lon: float) -> bool:
        return ((lat - center_lat) ** 2 + (lon - center_lon) ** 2) ** 0.5 <= radius

    impacted_facilities = [
        f for f in network.facilities if f.lat is not None and f.lon is not None and in_circle(f.lat, f.lon)
    ]
    impacted_facility_ids = {f.id for f in impacted_facilities}
    impacted_routes = [
        r
        for r in network.routes
        if r.origin_node_id in impacted_facility_ids
        or r.destination_node_id in impacted_facility_ids
    ]
    impacted_route_ids = {r.id for r in impacted_routes}
    ground_truth = {
        "event_id": event_id,
        "impacted_facility_ids": list(impacted_facility_ids),
        "impacted_route_ids": list(impacted_route_ids),
    }
    return event, ground_truth


def generate_cyber_incident_event(
    network: SupplyChainNetwork, rng: random.Random
) -> Tuple[Event, Dict]:
    provider_ids = {s.carrier_id for s in network.shipments}
    provider_id = rng.choice(list(provider_ids))
    event_id = _make_id("EV_CYBER")

    event = CyberIncident(
        id=event_id,
        provider_id=provider_id,
        impacted_systems=["tracking", "booking"],
        functional_impact=rng.choice(["tracking", "booking", "billing"]),
    )

    impacted_shipments = [s for s in network.shipments if s.carrier_id == provider_id]
    ground_truth = {
        "event_id": event_id,
        "provider_id": provider_id,
        "impacted_shipment_ids": [s.id for s in impacted_shipments],
        "impacted_order_ids": list({s.order_id for s in impacted_shipments}),
    }
    return event, ground_truth


def generate_export_control_event(
    network: SupplyChainNetwork, rng: random.Random
) -> Tuple[Event, Dict]:
    material = rng.choice(network.materials)
    event_id = _make_id("EV_EXPORT")

    event = ExportControl(
        id=event_id,
        material_id=material.id,
        country=f"Country-{rng.randint(1, 10)}",
        restriction_type=rng.choice(["ban", "quota"]),
    )

    impacted_products = [
        p for p in network.products if material.id in p.bom_material_ids
    ]
    impacted_product_ids = {p.id for p in impacted_products}
    impacted_orders = [
        o for o in network.orders if o.product_id in impacted_product_ids
    ]
    ground_truth = {
        "event_id": event_id,
        "material_id": material.id,
        "impacted_product_ids": list(impacted_product_ids),
        "impacted_order_ids": [o.id for o in impacted_orders],
    }
    return event, ground_truth


def generate_political_unrest_event(
    network: SupplyChainNetwork, rng: random.Random
) -> Tuple[Event, Dict]:
    region = rng.choice(network.regions)
    event_id = _make_id("EV_UNREST")

    event = PoliticalUnrest(
        id=event_id,
        region_id=region.id,
        impacted_sectors=["transport", "manufacturing"],
        severity=rng.choice([Severity.MEDIUM, Severity.HIGH]),
    )

    impacted_facilities = [f for f in network.facilities if f.region_id == region.id]
    impacted_facility_ids = {f.id for f in impacted_facilities}
    impacted_routes = [
        r
        for r in network.routes
        if r.origin_node_id in impacted_facility_ids
        or r.destination_node_id in impacted_facility_ids
    ]
    impacted_route_ids = {r.id for r in impacted_routes}
    ground_truth = {
        "event_id": event_id,
        "region_id": region.id,
        "impacted_facility_ids": list(impacted_facility_ids),
        "impacted_route_ids": list(impacted_route_ids),
    }
    return event, ground_truth


EVENT_GENERATORS = {
    "port_closure": generate_port_closure_event,
    "extreme_weather": generate_extreme_weather_event,
    "cyber_incident": generate_cyber_incident_event,
    "export_control": generate_export_control_event,
    "political_unrest": generate_political_unrest_event,
}


def generate_event(
    scenario_name: str, network: SupplyChainNetwork, seed: int = 42
) -> Tuple[Event, Dict]:
    rng = random.Random(seed)
    generator = EVENT_GENERATORS[scenario_name]
    return generator(network, rng)
