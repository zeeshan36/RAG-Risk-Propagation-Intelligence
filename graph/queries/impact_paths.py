"""Graph traversal queries for event impact propagation."""
from collections import deque
from typing import TYPE_CHECKING, List, Set

from events.propagation.impact_result import ImpactResult
from graph.schema.ontology import EdgeType, NodeType
from graph.utils.graph_client import GraphStore
from models.events import (
    CyberIncident,
    Event,
    ExportControl,
    ExtremeWeather,
    PoliticalUnrest,
    PortClosure,
)

if TYPE_CHECKING:
    from data_ingestion.batch.simple_repository import SimpleRepository


def propagate_event(
    graph: GraphStore, event: "Event", repo: "SimpleRepository"
) -> ImpactResult:
    """Propagate an event through the graph and return impacted entities."""
    graph.add_node(
        NodeType.EVENT,
        event.id,
        type=event.type,
        severity=event.severity.value,
        expected_duration_hours=event.expected_duration_hours,
    )

    anchor_ids = _event_anchor_ids(event, repo)
    for anchor_id in anchor_ids:
        graph.add_edge(EdgeType.AFFECTED_BY, event.id, anchor_id)

    reachable = _reachable_nodes(graph, [event.id], max_depth=8)
    result = ImpactResult(event_id=event.id, event_type=event.type)
    for node in reachable:
        if node["id"] == event.id:
            continue
        node_type = node.get("type", "")
        props = node.get("properties", {})
        name = props.get("name")
        if node_type == NodeType.SHIPMENT.value:
            result.add("Shipment", node["id"])
            result.impacted_shipment_ids.append(node["id"])
        elif node_type == NodeType.ORDER.value:
            result.add("Order", node["id"])
            result.impacted_order_ids.append(node["id"])
            revenue = props.get("revenue", 0.0)
            if isinstance(revenue, (int, float)):
                result.estimated_revenue_at_risk += revenue
        elif node_type == NodeType.CUSTOMER.value:
            result.add("Customer", node["id"], name)
            result.impacted_customer_ids.append(node["id"])
        elif node_type == NodeType.PRODUCT.value:
            result.add("Product", node["id"], name)
            result.impacted_product_ids.append(node["id"])
        elif node_type == NodeType.ROUTE.value:
            result.add("Route", node["id"])
            result.impacted_route_ids.append(node["id"])
        elif node_type == NodeType.FACILITY.value:
            result.add("Facility", node["id"], name)
            result.impacted_facility_ids.append(node["id"])
        elif node_type == NodeType.PORT.value:
            result.add("Port", node["id"], name)

    return result


def _event_anchor_ids(event: "Event", repo: "SimpleRepository") -> List[str]:
    from models.domain import Facility, Shipment
    from models.events import (
        CyberIncident,
        ExportControl,
        ExtremeWeather,
        PoliticalUnrest,
        PortClosure,
    )

    if isinstance(event, PortClosure):
        return [event.port_id]
    if isinstance(event, ExtremeWeather):
        # In graph mode we still use the repository for the polygon-to-facility join
        # unless a geospatial mapper is wired in. For testing we fall back to region.
        facilities = repo.find(Facility, lambda f: _in_weather_circle(f, event))
        return [f.id for f in facilities]
    if isinstance(event, CyberIncident):
        shipments = repo.find(Shipment, lambda s: s.carrier_id == event.provider_id)
        return [s.id for s in shipments]
    if isinstance(event, ExportControl):
        return [event.material_id]
    if isinstance(event, PoliticalUnrest):
        facilities = repo.find(Facility, lambda f: f.region_id == event.region_id)
        return [f.id for f in facilities]
    return []


def _in_weather_circle(facility, event: ExtremeWeather) -> bool:
    if facility.lat is None or facility.lon is None:
        return False
    return (
        (facility.lat - event.center_lat) ** 2
        + (facility.lon - event.center_lon) ** 2
    ) ** 0.5 <= event.radius_deg


def _reachable_nodes(
    graph: GraphStore, start_ids: List[str], max_depth: int = 6
) -> List[dict]:
    visited: Set[str] = set(start_ids)
    queue = deque([(node_id, 0) for node_id in start_ids])
    collected: List[dict] = []
    while queue:
        node_id, depth = queue.popleft()
        node = graph.get_node(node_id)
        if node is None:
            continue
        collected.append(node)
        if depth >= max_depth:
            continue
        for _, neighbor in graph.get_neighbors(node_id, direction="both"):
            neighbor_id = neighbor["id"]
            if neighbor_id not in visited:
                visited.add(neighbor_id)
                queue.append((neighbor_id, depth + 1))
    return collected
