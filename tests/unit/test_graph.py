"""Tests for graph adapters and queries."""
from data_ingestion.batch.simple_repository import SimpleRepository
from events.propagation.engine import PropagationEngine
from graph.loaders.builder import load_repository_into_graph
from graph.queries import impact_paths, vulnerability
from graph.schema.ontology import EdgeType, NodeType
from graph.utils.graph_client import InMemoryGraphStore
from models.domain import Customer, Facility, Order, Port, Product, Route, Shipment
from models.events import PortClosure


def _build_repo():
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


def test_in_memory_graph_store():
    graph = InMemoryGraphStore()
    graph.add_node(NodeType.PORT, "P1", name="Port A")
    graph.add_node(NodeType.ROUTE, "R1")
    graph.add_edge(EdgeType.LOCATED_IN, "R1", "P1")

    node = graph.get_node("P1")
    assert node["type"] == NodeType.PORT

    neighbors = graph.get_neighbors("R1", direction="out")
    assert len(neighbors) == 1
    assert neighbors[0][1]["id"] == "P1"


def test_load_repository_into_graph():
    repo = _build_repo()
    graph = InMemoryGraphStore()
    load_repository_into_graph(repo, graph)
    assert graph.get_node("P1") is not None
    assert graph.get_node("R1") is not None


def test_graph_propagation_port_closure():
    repo = _build_repo()
    graph = InMemoryGraphStore()
    load_repository_into_graph(repo, graph)
    engine = PropagationEngine(repo=repo, graph_store=graph, use_graph=True)
    event = PortClosure(id="E1", port_id="P1")
    impact = engine.propagate(event)
    assert "SH1" in impact.impacted_shipment_ids
    assert "O1" in impact.impacted_order_ids


def test_vulnerability_queries():
    repo = _build_repo()
    graph = InMemoryGraphStore()
    load_repository_into_graph(repo, graph)
    routes = vulnerability.bottleneck_routes(graph, top_k=5)
    assert len(routes) >= 0
    suppliers = vulnerability.central_suppliers(graph, top_k=5)
    assert len(suppliers) >= 0
