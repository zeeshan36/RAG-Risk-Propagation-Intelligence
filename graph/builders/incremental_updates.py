"""Incremental graph updates without a full rebuild."""
from typing import Any, Dict, List

from pydantic import BaseModel

from graph.schema.ontology import EdgeType, NodeType
from graph.utils.graph_client import GraphStore


class GraphDelta(BaseModel):
    """A structured delta for incremental graph updates."""

    add_nodes: List[Dict[str, Any]] = []
    update_nodes: List[Dict[str, Any]] = []
    remove_nodes: List[str] = []
    add_edges: List[Dict[str, Any]] = []
    update_edges: List[Dict[str, Any]] = []
    remove_edges: List[Dict[str, Any]] = []


def apply_delta(graph: GraphStore, delta: GraphDelta) -> Dict[str, int]:
    """Apply a delta to an existing graph store.

    Returns counts of applied operations.
    """
    stats = {
        "nodes_added": 0,
        "nodes_updated": 0,
        "nodes_removed": 0,
        "edges_added": 0,
        "edges_updated": 0,
        "edges_removed": 0,
    }

    for node in delta.add_nodes:
        node_type = NodeType(node["type"])
        node_id = node["id"]
        props = {k: v for k, v in node.items() if k not in ("type", "id")}
        graph.add_node(node_type, node_id, **props)
        stats["nodes_added"] += 1

    for node in delta.update_nodes:
        node_type = NodeType(node["type"])
        node_id = node["id"]
        props = {k: v for k, v in node.items() if k not in ("type", "id")}
        graph.upsert_node(node_type, node_id, **props)
        stats["nodes_updated"] += 1

    for node_id in delta.remove_nodes:
        if graph.remove_node(node_id):
            stats["nodes_removed"] += 1

    for edge in delta.add_edges:
        edge_type = EdgeType(edge["type"])
        graph.add_edge(
            edge_type, edge["source"], edge["target"], **edge.get("properties", {})
        )
        stats["edges_added"] += 1

    for edge in delta.update_edges:
        edge_type = EdgeType(edge["type"])
        graph.upsert_edge(
            edge_type, edge["source"], edge["target"], **edge.get("properties", {})
        )
        stats["edges_updated"] += 1

    for edge in delta.remove_edges:
        edge_type = EdgeType(edge["type"])
        if graph.remove_edge(edge_type, edge["source"], edge["target"]):
            stats["edges_removed"] += 1

    return stats
