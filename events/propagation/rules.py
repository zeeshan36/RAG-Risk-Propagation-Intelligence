"""Minimal-mode propagation rules using repository joins."""
from decimal import Decimal
from typing import TYPE_CHECKING, Dict, List, Optional, Set

from events.propagation.impact_result import ImpactResult
from models.domain import (
    Customer,
    Facility,
    Order,
    Port,
    Product,
    Route,
    Shipment,
)
from models.events import (
    CyberIncident,
    ExportControl,
    ExtremeWeather,
    PoliticalUnrest,
    PortClosure,
)

if TYPE_CHECKING:
    from data_ingestion.batch.simple_repository import SimpleRepository


def propagate_port_closure(
    event: PortClosure, repo: "SimpleRepository"
) -> ImpactResult:
    result = ImpactResult(event_id=event.id, event_type=event.type)
    port = _get_or_none(repo, Port, event.port_id)
    if port:
        result.add("Port", port.id, port.name)

    impacted_routes = repo.find(
        Route,
        lambda r: r.origin_node_id == event.port_id
        or r.destination_node_id == event.port_id,
    )
    _propagate_routes(result, repo, {r.id for r in impacted_routes})
    return result


def propagate_extreme_weather(
    event: ExtremeWeather,
    repo: "SimpleRepository",
    geo_mapper: Optional[object] = None,
) -> ImpactResult:
    result = ImpactResult(event_id=event.id, event_type=event.type)

    if geo_mapper is not None:
        impacted_facilities = repo.find(
            Facility,
            lambda f: geo_mapper.point_in_circle(
                f.lat, f.lon, event.center_lat, event.center_lon, event.radius_deg
            ),
        )
    else:
        # Minimal-mode fallback: simple euclidean-degree circle check.
        impacted_facilities = repo.find(
            Facility,
            lambda f: _in_circle(f.lat, f.lon, event),
        )

    facility_ids = {f.id for f in impacted_facilities}
    for facility in impacted_facilities:
        result.add("Facility", facility.id, facility.name)

    impacted_routes = repo.find(
        Route,
        lambda r: r.origin_node_id in facility_ids
        or r.destination_node_id in facility_ids,
    )
    _propagate_routes(result, repo, {r.id for r in impacted_routes})
    return result


def _in_circle(lat: Optional[float], lon: Optional[float], event: ExtremeWeather) -> bool:
    if lat is None or lon is None:
        return False
    return (
        (lat - event.center_lat) ** 2 + (lon - event.center_lon) ** 2
    ) ** 0.5 <= event.radius_deg


def propagate_cyber_incident(
    event: CyberIncident, repo: "SimpleRepository"
) -> ImpactResult:
    result = ImpactResult(event_id=event.id, event_type=event.type)
    impacted_shipments = repo.find(Shipment, lambda s: s.carrier_id == event.provider_id)
    _propagate_shipments(result, repo, impacted_shipments)
    return result


def propagate_export_control(
    event: ExportControl, repo: "SimpleRepository"
) -> ImpactResult:
    result = ImpactResult(event_id=event.id, event_type=event.type)
    impacted_products = repo.find(
        Product, lambda p: event.material_id in p.bom_material_ids
    )
    product_ids = {p.id for p in impacted_products}
    for product in impacted_products:
        result.add("Product", product.id, product.name)

    impacted_orders = repo.find(Order, lambda o: o.product_id in product_ids)
    _propagate_orders(result, repo, impacted_orders)
    return result


def propagate_political_unrest(
    event: PoliticalUnrest, repo: "SimpleRepository"
) -> ImpactResult:
    result = ImpactResult(event_id=event.id, event_type=event.type)
    impacted_facilities = repo.find(
        Facility, lambda f: f.region_id == event.region_id
    )
    facility_ids = {f.id for f in impacted_facilities}
    for facility in impacted_facilities:
        result.add("Facility", facility.id, facility.name)

    impacted_routes = repo.find(
        Route,
        lambda r: r.origin_node_id in facility_ids
        or r.destination_node_id in facility_ids,
    )
    _propagate_routes(result, repo, {r.id for r in impacted_routes})
    return result


def _propagate_routes(
    result: ImpactResult, repo: "SimpleRepository", route_ids: Set[str]
) -> None:
    for route_id in route_ids:
        result.add("Route", route_id)
        result.impacted_route_ids.append(route_id)
    impacted_shipments = repo.find(
        Shipment, lambda s: any(rid in route_ids for rid in s.route_ids)
    )
    _propagate_shipments(result, repo, impacted_shipments)


def _propagate_shipments(
    result: ImpactResult, repo: "SimpleRepository", shipments: List[Shipment]
) -> None:
    order_ids: Set[str] = set()
    for shipment in shipments:
        result.add("Shipment", shipment.id)
        result.impacted_shipment_ids.append(shipment.id)
        order_ids.add(shipment.order_id)

    impacted_orders = [repo.get(Order, oid) for oid in order_ids]
    _propagate_orders(result, repo, impacted_orders)


def _propagate_orders(
    result: ImpactResult, repo: "SimpleRepository", orders: List[Order]
) -> None:
    customer_ids: Set[str] = set()
    product_ids: Set[str] = set()
    revenue: Decimal = Decimal("0.00")
    for order in orders:
        result.add("Order", order.id)
        result.impacted_order_ids.append(order.id)
        customer_ids.add(order.customer_id)
        product_ids.add(order.product_id)
        revenue += Decimal(order.revenue)

    for customer_id in customer_ids:
        customer = _get_or_none(repo, Customer, customer_id)
        result.add("Customer", customer_id, customer.name if customer else None)
        result.impacted_customer_ids.append(customer_id)

    for product_id in product_ids:
        product = _get_or_none(repo, Product, product_id)
        result.add("Product", product_id, product.name if product else None)
        result.impacted_product_ids.append(product_id)

    result.estimated_revenue_at_risk = float(revenue)


def _get_or_none(repo: "SimpleRepository", model_cls, entity_id: str):
    try:
        return repo.get(model_cls, entity_id)
    except Exception:
        return None
