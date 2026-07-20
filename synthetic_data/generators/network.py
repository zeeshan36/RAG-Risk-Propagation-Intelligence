"""Synthetic supply-chain network generator."""
import random
import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import List

from models.domain import (
    Contract,
    Customer,
    Facility,
    FacilityType,
    Material,
    Order,
    Port,
    Product,
    Region,
    RevenueStream,
    Route,
    RouteMode,
    Shipment,
    ShipmentStatus,
    Supplier,
)


def _make_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@dataclass
class SupplyChainNetwork:
    regions: List[Region] = field(default_factory=list)
    facilities: List[Facility] = field(default_factory=list)
    ports: List[Port] = field(default_factory=list)
    suppliers: List[Supplier] = field(default_factory=list)
    customers: List[Customer] = field(default_factory=list)
    materials: List[Material] = field(default_factory=list)
    products: List[Product] = field(default_factory=list)
    routes: List[Route] = field(default_factory=list)
    orders: List[Order] = field(default_factory=list)
    shipments: List[Shipment] = field(default_factory=list)
    contracts: List[Contract] = field(default_factory=list)
    revenue_streams: List[RevenueStream] = field(default_factory=list)


def generate_network(
    num_regions: int = 5,
    num_facilities: int = 50,
    num_ports: int = 10,
    num_suppliers: int = 40,
    num_customers: int = 80,
    num_materials: int = 30,
    num_products: int = 60,
    num_orders: int = 500,
    num_shipments: int = 600,
    num_routes: int = 200,
    seed: int = 42,
) -> SupplyChainNetwork:
    rng = random.Random(seed)

    regions = [
        Region(id=f"R{i}", name=f"Region-{i}") for i in range(num_regions)
    ]

    facilities: List[Facility] = []
    for _ in range(num_facilities):
        region = rng.choice(regions)
        facilities.append(
            Facility(
                id=_make_id("F"),
                type=rng.choice(list(FacilityType)),
                name=f"Facility-{rng.randint(1, 1000)}",
                region_id=region.id,
                lat=rng.uniform(-60, 60),
                lon=rng.uniform(-150, 150),
            )
        )

    ports: List[Port] = []
    for _ in range(num_ports):
        region = rng.choice(regions)
        ports.append(
            Port(
                id=_make_id("P"),
                name=f"Port-{rng.randint(1, 1000)}",
                region_id=region.id,
                lat=rng.uniform(-60, 60),
                lon=rng.uniform(-150, 150),
                modes=rng.sample(list(RouteMode), k=rng.randint(1, 2)),
            )
        )

    suppliers = [
        Supplier(
            id=_make_id("S"),
            name=f"Supplier-{rng.randint(1, 1000)}",
            country=f"Country-{rng.randint(1, 10)}",
            criticality_score=rng.uniform(0, 1),
        )
        for _ in range(num_suppliers)
    ]

    customers = [
        Customer(
            id=_make_id("C"),
            name=f"Customer-{rng.randint(1, 1000)}",
            region_id=rng.choice(regions).id,
            criticality_score=rng.uniform(0, 1),
        )
        for _ in range(num_customers)
    ]

    materials = [
        Material(
            id=_make_id("M"),
            name=f"Material-{rng.randint(1, 1000)}",
            restricted_flag=False,
        )
        for _ in range(num_materials)
    ]

    products = []
    for _ in range(num_products):
        bom = rng.sample(materials, k=rng.randint(1, min(4, num_materials)))
        products.append(
            Product(
                id=_make_id("PR"),
                name=f"Product-{rng.randint(1, 1000)}",
                sku=f"SKU-{rng.randint(1000, 9999)}",
                bom_material_ids=[m.id for m in bom],
            )
        )

    all_nodes = facilities + ports
    routes: List[Route] = []
    attempts = 0
    while len(routes) < num_routes and attempts < num_routes * 10:
        attempts += 1
        origin = rng.choice(all_nodes)
        dest = rng.choice(all_nodes)
        if origin.id == dest.id:
            continue
        routes.append(
            Route(
                id=_make_id("RTE"),
                origin_node_id=origin.id,
                destination_node_id=dest.id,
                mode=rng.choice(list(RouteMode)),
                avg_lead_time_days=rng.randint(3, 30),
                capacity=rng.randint(50, 500),
            )
        )

    orders: List[Order] = []
    for _ in range(num_orders):
        customer = rng.choice(customers)
        product = rng.choice(products)
        quantity = rng.randint(1, 100)
        revenue = Decimal(str(round(quantity * rng.uniform(100, 500), 2)))
        margin = Decimal(str(round(float(revenue) * rng.uniform(0.2, 0.5), 2)))
        orders.append(
            Order(
                id=_make_id("O"),
                customer_id=customer.id,
                product_id=product.id,
                quantity=quantity,
                order_date=None,
                promised_delivery_date=None,
                revenue=revenue,
                margin=margin,
            )
        )

    shipments: List[Shipment] = []
    for _ in range(num_shipments):
        order = rng.choice(orders)
        route_path = rng.sample(routes, k=rng.randint(1, min(3, len(routes))))
        shipments.append(
            Shipment(
                id=_make_id("SH"),
                order_id=order.id,
                route_ids=[r.id for r in route_path],
                carrier_id=_make_id("CAR"),
                depart_time=None,
                arrival_time=None,
                status=ShipmentStatus.PLANNED,
            )
        )

    contracts = [
        Contract(
            id=_make_id("CON"),
            customer_id=rng.choice(customers).id,
            carrier_id=None,
            sla_days=rng.randint(3, 14),
            penalty_per_day=Decimal(str(round(rng.uniform(50, 500), 2))),
            force_majeure_clause=rng.choice([True, False]),
        )
        for _ in range(num_customers // 4)
    ]

    revenue_streams = [
        RevenueStream(
            id=_make_id("REV"),
            order_id=order.id,
            amount=order.revenue,
            margin=order.margin,
            period="2026-Q1",
        )
        for order in orders[: num_orders // 2]
    ]

    return SupplyChainNetwork(
        regions=regions,
        facilities=facilities,
        ports=ports,
        suppliers=suppliers,
        customers=customers,
        materials=materials,
        products=products,
        routes=routes,
        orders=orders,
        shipments=shipments,
        contracts=contracts,
        revenue_streams=revenue_streams,
    )
