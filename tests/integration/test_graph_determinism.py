"""Graph construction determinism tests."""
from data_ingestion.batch.simple_repository import SimpleRepository
from graph.loaders.builder import load_repository_into_graph
from graph.utils.graph_client import InMemoryGraphStore
from models.domain import Customer, Facility, Order, Port, Product, Route, Shipment


def _build_repo():
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
    return repo


def _graph_signature(graph: InMemoryGraphStore):
    nodes = {nid for nid in graph._nodes}
    edges = {
        (e["type"].value, e["source"], e["target"])
        for e in graph._edges.values()
    }
    return nodes, edges


def test_graph_build_is_deterministic():
    repo1 = _build_repo()
    repo2 = _build_repo()

    graph1 = InMemoryGraphStore()
    graph2 = InMemoryGraphStore()

    load_repository_into_graph(repo1, graph1)
    load_repository_into_graph(repo2, graph2)

    nodes1, edges1 = _graph_signature(graph1)
    nodes2, edges2 = _graph_signature(graph2)

    assert nodes1 == nodes2
    assert edges1 == edges2
