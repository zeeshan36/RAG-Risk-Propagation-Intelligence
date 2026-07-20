"""Convert canonical domain models into graph nodes and edges."""
from typing import TYPE_CHECKING

from graph.schema.ontology import EdgeType, NodeType
from graph.utils.graph_client import GraphStore

if TYPE_CHECKING:
    from data_ingestion.batch.simple_repository import SimpleRepository


def load_repository_into_graph(
    repo: "SimpleRepository", graph: GraphStore
) -> None:
    """Load all entities from the repository into the graph store."""
    from models.domain import (
        Contract,
        Customer,
        Facility,
        Material,
        Order,
        Port,
        Product,
        Region,
        RevenueStream,
        Route,
        Shipment,
        Supplier,
    )

    for region in repo.list(Region):
        graph.add_node(NodeType.REGION, region.id, name=region.name)

    for supplier in repo.list(Supplier):
        graph.add_node(
            NodeType.SUPPLIER,
            supplier.id,
            name=supplier.name,
            country=supplier.country,
            criticality_score=supplier.criticality_score,
        )

    for facility in repo.list(Facility):
        graph.add_node(
            NodeType.FACILITY,
            facility.id,
            name=facility.name,
            facility_type=facility.type.value,
            lat=facility.lat,
            lon=facility.lon,
        )
        graph.add_edge(EdgeType.LOCATED_IN, facility.id, facility.region_id)

    for port in repo.list(Port):
        graph.add_node(
            NodeType.PORT,
            port.id,
            name=port.name,
            modes=[m.value for m in port.modes],
            lat=port.lat,
            lon=port.lon,
        )
        graph.add_edge(EdgeType.LOCATED_IN, port.id, port.region_id)

    for material in repo.list(Material):
        graph.add_node(
            NodeType.MATERIAL,
            material.id,
            name=material.name,
            restricted=material.restricted_flag,
        )

    for product in repo.list(Product):
        graph.add_node(
            NodeType.PRODUCT, product.id, name=product.name, sku=product.sku
        )
        for material_id in product.bom_material_ids:
            graph.add_edge(EdgeType.HAS_BOM, product.id, material_id)

    for customer in repo.list(Customer):
        graph.add_node(
            NodeType.CUSTOMER,
            customer.id,
            name=customer.name,
            criticality_score=customer.criticality_score,
        )
        graph.add_edge(EdgeType.LOCATED_IN, customer.id, customer.region_id)

    for route in repo.list(Route):
        graph.add_node(
            NodeType.ROUTE,
            route.id,
            mode=route.mode.value,
            avg_lead_time_days=route.avg_lead_time_days,
            capacity=route.capacity,
        )
        graph.add_edge(EdgeType.SHIPS_TO, route.id, route.destination_node_id)
        graph.add_edge(EdgeType.LOCATED_IN, route.id, route.origin_node_id)

    for order in repo.list(Order):
        graph.add_node(
            NodeType.ORDER,
            order.id,
            quantity=order.quantity,
            revenue=float(order.revenue),
            margin=float(order.margin),
        )
        graph.add_edge(EdgeType.PLACED_BY, order.id, order.customer_id)
        graph.add_edge(EdgeType.CONTAINS, order.id, order.product_id)

    for shipment in repo.list(Shipment):
        graph.add_node(
            NodeType.SHIPMENT,
            shipment.id,
            carrier_id=shipment.carrier_id,
            status=shipment.status.value,
        )
        graph.add_edge(EdgeType.FULFILLS, shipment.id, shipment.order_id)
        for route_id in shipment.route_ids:
            graph.add_edge(EdgeType.USES_ROUTE, shipment.id, route_id)

    for contract in repo.list(Contract):
        graph.add_node(
            NodeType.CONTRACT,
            contract.id,
            sla_days=contract.sla_days,
            penalty_per_day=float(contract.penalty_per_day),
            force_majeure=contract.force_majeure_clause,
        )
        if contract.customer_id:
            graph.add_edge(EdgeType.HAS_CONTRACT, contract.customer_id, contract.id)
        if contract.carrier_id:
            graph.add_edge(EdgeType.HAS_CONTRACT, contract.carrier_id, contract.id)

    for revenue in repo.list(RevenueStream):
        graph.add_node(
            NodeType.REVENUE_STREAM,
            revenue.id,
            amount=float(revenue.amount),
            margin=float(revenue.margin),
            period=revenue.period,
        )
        graph.add_edge(EdgeType.GENERATES, revenue.order_id, revenue.id)
