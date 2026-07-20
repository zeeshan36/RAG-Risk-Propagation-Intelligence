"""Knowledge-graph node and edge type definitions."""
from enum import Enum
from typing import Any, Dict


class NodeType(str, Enum):
    REGION = "Region"
    SUPPLIER = "Supplier"
    FACILITY = "Facility"
    PORT = "Port"
    ROUTE = "Route"
    MATERIAL = "Material"
    PRODUCT = "Product"
    CUSTOMER = "Customer"
    ORDER = "Order"
    SHIPMENT = "Shipment"
    CONTRACT = "Contract"
    REVENUE_STREAM = "RevenueStream"
    EVENT = "Event"


class EdgeType(str, Enum):
    LOCATED_IN = "LOCATED_IN"
    SUPPLIES = "SUPPLIES"
    SHIPS_TO = "SHIPS_TO"
    SERVED_BY = "SERVED_BY"
    USES_ROUTE = "USES_ROUTE"
    DEPENDS_ON = "DEPENDS_ON"
    HAS_BOM = "HAS_BOM"
    PLACED_BY = "PLACED_BY"
    CONTAINS = "CONTAINS"
    FULFILLS = "FULFILLS"
    HAS_CONTRACT = "HAS_CONTRACT"
    GENERATES = "GENERATES"
    AFFECTED_BY = "AFFECTED_BY"


def make_node(node_type: NodeType, node_id: str, **props: Any) -> Dict[str, Any]:
    return {"type": node_type, "id": node_id, "properties": dict(props)}


def make_edge(
    edge_type: EdgeType, source_id: str, target_id: str, **props: Any
) -> Dict[str, Any]:
    return {
        "type": edge_type,
        "source": source_id,
        "target": target_id,
        "properties": dict(props),
    }
