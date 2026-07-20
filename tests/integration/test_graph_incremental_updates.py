"""Incremental graph update tests."""
from data_ingestion.batch.simple_repository import SimpleRepository
from graph.builders.incremental_updates import GraphDelta, apply_delta
from graph.loaders.builder import load_repository_into_graph
from graph.queries import impact_paths
from graph.schema.ontology import EdgeType, NodeType
from graph.utils.graph_client import InMemoryGraphStore
from models.domain import Customer, Facility, Order, Port, Product, Route, Shipment
from models.events import PortClosure


def _build_baseline_graph():
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
    graph = InMemoryGraphStore()
    load_repository_into_graph(repo, graph)
    return graph


def test_incremental_add_route_and_order():
    graph = _build_baseline_graph()

    delta = GraphDelta(
        add_nodes=[
            {"type": NodeType.PORT.value, "id": "P2", "name": "Port B"},
            {"type": NodeType.ROUTE.value, "id": "R2", "mode": "air"},
            {"type": NodeType.ORDER.value, "id": "O2"},
            {"type": NodeType.SHIPMENT.value, "id": "SH2", "carrier_id": "CAR2"},
        ],
        add_edges=[
            {"type": EdgeType.LOCATED_IN.value, "source": "P2", "target": "R1"},
            {"type": EdgeType.SHIPS_TO.value, "source": "R2", "target": "P2"},
            {"type": EdgeType.FULFILLS.value, "source": "SH2", "target": "O2"},
            {"type": EdgeType.USES_ROUTE.value, "source": "SH2", "target": "R2"},
        ],
    )
    stats = apply_delta(graph, delta)
    assert stats["nodes_added"] == 4
    assert stats["edges_added"] == 4

    event = PortClosure(id="EV1", port_id="P2")
    impact = impact_paths.propagate_event(graph, event, SimpleRepository())
    assert "SH2" in impact.impacted_shipment_ids


def test_incremental_update_and_remove():
    graph = _build_baseline_graph()

    # Update a node property.
    delta = GraphDelta(
        update_nodes=[
            {"type": NodeType.PORT.value, "id": "P1", "name": "Port A Updated"},
        ],
    )
    stats = apply_delta(graph, delta)
    assert stats["nodes_updated"] == 1
    assert graph.get_node("P1")["properties"]["name"] == "Port A Updated"

    # Remove a route edge so the propagation path is broken.
    delta = GraphDelta(
        remove_edges=[
            {"type": EdgeType.LOCATED_IN.value, "source": "R1", "target": "P1"},
        ],
    )
    stats = apply_delta(graph, delta)
    assert stats["edges_removed"] == 1
