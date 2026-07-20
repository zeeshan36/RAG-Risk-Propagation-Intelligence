"""Deterministic ground-truth impact calculators."""
from typing import Dict, List, Set

from models.events import (
    CyberIncident,
    Event,
    ExportControl,
    ExtremeWeather,
    PoliticalUnrest,
    PortClosure,
)
from synthetic_data.generators.network import SupplyChainNetwork


def calculate_ground_truth(
    event: Event, network: SupplyChainNetwork
) -> Dict[str, List[str]]:
    """Return the canonical ground-truth impacted IDs for an event."""
    if isinstance(event, PortClosure):
        return _port_closure_truth(event, network)
    if isinstance(event, ExtremeWeather):
        return _extreme_weather_truth(event, network)
    if isinstance(event, CyberIncident):
        return _cyber_incident_truth(event, network)
    if isinstance(event, ExportControl):
        return _export_control_truth(event, network)
    if isinstance(event, PoliticalUnrest):
        return _political_unrest_truth(event, network)
    return {}


def _port_closure_truth(event: PortClosure, network: SupplyChainNetwork) -> Dict[str, List[str]]:
    routes = [
        r
        for r in network.routes
        if r.origin_node_id == event.port_id or r.destination_node_id == event.port_id
    ]
    route_ids = {r.id for r in routes}
    shipments = [s for s in network.shipments if any(rid in route_ids for rid in s.route_ids)]
    return {
        "event_id": event.id,
        "impacted_route_ids": sorted(route_ids),
        "impacted_shipment_ids": sorted({s.id for s in shipments}),
        "impacted_order_ids": sorted({s.order_id for s in shipments}),
    }


def _extreme_weather_truth(event: ExtremeWeather, network: SupplyChainNetwork) -> Dict[str, List[str]]:
    facility_ids: Set[str] = set()
    for f in network.facilities:
        if f.lat is None or f.lon is None:
            continue
        if ((f.lat - event.center_lat) ** 2 + (f.lon - event.center_lon) ** 2) ** 0.5 <= event.radius_deg:
            facility_ids.add(f.id)
    route_ids = {
        r.id
        for r in network.routes
        if r.origin_node_id in facility_ids or r.destination_node_id in facility_ids
    }
    return {
        "event_id": event.id,
        "impacted_facility_ids": sorted(facility_ids),
        "impacted_route_ids": sorted(route_ids),
    }


def _cyber_incident_truth(event: CyberIncident, network: SupplyChainNetwork) -> Dict[str, List[str]]:
    shipments = [s for s in network.shipments if s.carrier_id == event.provider_id]
    return {
        "event_id": event.id,
        "impacted_shipment_ids": sorted({s.id for s in shipments}),
        "impacted_order_ids": sorted({s.order_id for s in shipments}),
    }


def _export_control_truth(event: ExportControl, network: SupplyChainNetwork) -> Dict[str, List[str]]:
    product_ids = {p.id for p in network.products if event.material_id in p.bom_material_ids}
    orders = [o for o in network.orders if o.product_id in product_ids]
    return {
        "event_id": event.id,
        "impacted_product_ids": sorted(product_ids),
        "impacted_order_ids": sorted({o.id for o in orders}),
    }


def _political_unrest_truth(event: PoliticalUnrest, network: SupplyChainNetwork) -> Dict[str, List[str]]:
    facility_ids = {f.id for f in network.facilities if f.region_id == event.region_id}
    route_ids = {
        r.id
        for r in network.routes
        if r.origin_node_id in facility_ids or r.destination_node_id in facility_ids
    }
    return {
        "event_id": event.id,
        "impacted_facility_ids": sorted(facility_ids),
        "impacted_route_ids": sorted(route_ids),
    }
