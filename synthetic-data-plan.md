# Synthetic Data Generation and Testing Plan for Supply Chain GraphRAG

## 1. Goals

- Generate synthetic yet realistic supply chain graphs and events to test GraphRAG functionality end-to-end.
- Provide labeled ground truth for propagation, retrieval, and generation layers.
- Cover happy-path, edge-case, and stress-test scenarios for all supported event types (port closure, extreme weather, cyber incident, export control, political unrest).

## 2. Synthetic Supply Chain Graph Design

### 2.1 Core Entities

Represent the supply chain as tables/JSON collections that will be ingested into the graph:

- `facilities`: id, type (warehouse/factory/DC), name, region_id, lat, lon.
- `ports`: id, name, region_id, lat, lon, modes (sea/road/rail).
- `suppliers`: id, name, country, criticality_score.
- `customers`: id, name, region_id, criticality_score.
- `routes`: id, origin_node_id, destination_node_id, mode, avg_lead_time_days, capacity.
- `materials`: id, name, restricted_flag.
- `products`: id, name, sku, bom_material_ids[].
- `orders`: id, customer_id, product_id, quantity, order_date, promised_delivery_date, revenue, margin.
- `shipments`: id, order_id, route_ids[], carrier_id, depart_time, arrival_time, status.
- `contracts`: id, customer_id, carrier_id, sla_days, penalty_per_day, force_majeure_clause.

### 2.2 Graph Generation Logic (Pseudo-code)

```python
import random
import uuid
from typing import List, Dict

NUM_REGIONS = 5
NUM_FACILITIES = 50
NUM_PORTS = 10
NUM_SUPPLIERS = 40
NUM_CUSTOMERS = 80
NUM_MATERIALS = 30
NUM_PRODUCTS = 60
NUM_ORDERS = 500
NUM_SHIPMENTS = 600

# Helpers

def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

regions = [
    {"id": f"R{i}", "name": f"Region-{i}"} for i in range(NUM_REGIONS)
]

facilities = []
for _ in range(NUM_FACILITIES):
    region = random.choice(regions)
    facilities.append({
        "id": make_id("F"),
        "type": random.choice(["warehouse", "factory", "dc"]),
        "name": "Facility-" + str(random.randint(1, 1000)),
        "region_id": region["id"],
        "lat": random.uniform(-60, 60),
        "lon": random.uniform(-150, 150),
    })

ports = []
for _ in range(NUM_PORTS):
    region = random.choice(regions)
    ports.append({
        "id": make_id("P"),
        "name": "Port-" + str(random.randint(1, 1000)),
        "region_id": region["id"],
        "lat": random.uniform(-60, 60),
        "lon": random.uniform(-150, 150),
        "modes": ["sea", "road"]
    })

suppliers = []
for _ in range(NUM_SUPPLIERS):
    suppliers.append({
        "id": make_id("S"),
        "name": "Supplier-" + str(random.randint(1, 1000)),
        "country": f"Country-{random.randint(1, 10)}",
        "criticality_score": random.uniform(0, 1)
    })

customers = []
for _ in range(NUM_CUSTOMERS):
    region = random.choice(regions)
    customers.append({
        "id": make_id("C"),
        "name": "Customer-" + str(random.randint(1, 1000)),
        "region_id": region["id"],
        "criticality_score": random.uniform(0, 1)
    })

materials = []
for _ in range(NUM_MATERIALS):
    materials.append({
        "id": make_id("M"),
        "name": "Material-" + str(random.randint(1, 1000)),
        "restricted_flag": False
    })

products = []
for _ in range(NUM_PRODUCTS):
    bom = random.sample(materials, k=random.randint(1, 4))
    products.append({
        "id": make_id("PR"),
        "name": "Product-" + str(random.randint(1, 1000)),
        "sku": "SKU-" + str(random.randint(1000, 9999)),
        "bom_material_ids": [m["id"] for m in bom]
    })

routes = []
all_nodes = facilities + ports
for _ in range(200):
    origin = random.choice(all_nodes)
    dest = random.choice(all_nodes)
    if origin["id"] == dest["id"]:
        continue
    routes.append({
        "id": make_id("RTE"),
        "origin_node_id": origin["id"],
        "destination_node_id": dest["id"],
        "mode": random.choice(["sea", "air", "road", "rail"]),
        "avg_lead_time_days": random.randint(3, 30),
        "capacity": random.randint(50, 500)
    })

orders = []
for _ in range(NUM_ORDERS):
    customer = random.choice(customers)
    product = random.choice(products)
    quantity = random.randint(1, 100)
    revenue = quantity * random.uniform(100, 500)
    margin = revenue * random.uniform(0.2, 0.5)
    orders.append({
        "id": make_id("O"),
        "customer_id": customer["id"],
        "product_id": product["id"],
        "quantity": quantity,
        "order_date": "2026-01-01",
        "promised_delivery_date": "2026-01-15",
        "revenue": revenue,
        "margin": margin
    })

shipments = []
for _ in range(NUM_SHIPMENTS):
    order = random.choice(orders)
    route_path = random.sample(routes, k=random.randint(1, 3))
    shipments.append({
        "id": make_id("SH"),
        "order_id": order["id"],
        "route_ids": [r["id"] for r in route_path],
        "carrier_id": make_id("CAR"),
        "depart_time": "2026-01-02T00:00:00Z",
        "arrival_time": "2026-01-14T00:00:00Z",
        "status": "planned"
    })
```

This generator gives you a full synthetic network that you can ingest into the graph store and RAG pipeline.

## 3. Synthetic Event Generators with Ground Truth

### 3.1 Port Closure Event

Represent events as structures tied to graph entities:

```python
def generate_port_closure_event(ports, routes, shipments):
    port = random.choice(ports)
    event_id = make_id("EV_PORTCLOSE")
    event = {
        "id": event_id,
        "type": "PortClosure",
        "port_id": port["id"],
        "start_time": "2026-02-01T00:00:00Z",
        "expected_duration_hours": random.randint(24, 168),
        "severity": random.choice(["low", "medium", "high"])
    }

    # Ground truth: impacted routes and shipments
    impacted_routes = [
        r for r in routes
        if r["origin_node_id"] == port["id"] or r["destination_node_id"] == port["id"]
    ]
    impacted_route_ids = {r["id"] for r in impacted_routes}

    impacted_shipments = [
        s for s in shipments
        if any(rid in impacted_route_ids for rid in s["route_ids"])
    ]

    ground_truth = {
        "event_id": event_id,
        "impacted_route_ids": list(impacted_route_ids),
        "impacted_shipment_ids": [s["id"] for s in impacted_shipments],
        "impacted_order_ids": list({s["order_id"] for s in impacted_shipments})
    }

    return event, ground_truth
```

### 3.2 Extreme Weather Event (Polygon-Based)

```python
def generate_weather_event(facilities, routes):
    event_id = make_id("EV_WEATHER")
    # Define a synthetic polygon as bounding box
    center_lat = random.uniform(-40, 40)
    center_lon = random.uniform(-100, 100)
    radius = 10.0

    event = {
        "id": event_id,
        "type": "ExtremeWeather",
        "hazard_type": random.choice(["flood", "storm", "heatwave"]),
        "center_lat": center_lat,
        "center_lon": center_lon,
        "radius_deg": radius,
        "severity": random.choice(["medium", "high"])
    }

    def in_circle(lat, lon):
        return ((lat - center_lat)**2 + (lon - center_lon)**2) ** 0.5 <= radius

    impacted_facilities = [f for f in facilities if in_circle(f["lat"], f["lon"])]
    impacted_facility_ids = {f["id"] for f in impacted_facilities}

    impacted_routes = [
        r for r in routes
        if r["origin_node_id"] in impacted_facility_ids or r["destination_node_id"] in impacted_facility_ids
    ]
    impacted_route_ids = {r["id"] for r in impacted_routes}

    ground_truth = {
        "event_id": event_id,
        "impacted_facility_ids": list(impacted_facility_ids),
        "impacted_route_ids": list(impacted_route_ids)
    }

    return event, ground_truth
```

### 3.3 Cyber Incident Event

```python
def generate_cyber_incident_event(shipments):
    event_id = make_id("EV_CYBER")
    # Choose a synthetic provider id from shipments
    provider_ids = {s["carrier_id"] for s in shipments}
    provider_id = random.choice(list(provider_ids))

    event = {
        "id": event_id,
        "type": "CyberIncident",
        "provider_id": provider_id,
        "start_time": "2026-03-01T00:00:00Z",
        "impact": random.choice(["tracking", "booking", "billing"])
    }

    impacted_shipments = [s for s in shipments if s["carrier_id"] == provider_id]

    ground_truth = {
        "event_id": event_id,
        "provider_id": provider_id,
        "impacted_shipment_ids": [s["id"] for s in impacted_shipments],
        "impacted_order_ids": list({s["order_id"] for s in impacted_shipments})
    }

    return event, ground_truth
```

### 3.4 Export Control Event

```python
def generate_export_control_event(materials, products, orders):
    material = random.choice(materials)
    event_id = make_id("EV_EXPORT")

    event = {
        "id": event_id,
        "type": "ExportControl",
        "material_id": material["id"],
        "country": f"Country-{random.randint(1, 10)}",
        "restriction_type": random.choice(["ban", "quota"])
    }

    impacted_products = [
        p for p in products if material["id"] in p["bom_material_ids"]
    ]
    impacted_product_ids = {p["id"] for p in impacted_products}

    impacted_orders = [
        o for o in orders if o["product_id"] in impacted_product_ids
    ]

    ground_truth = {
        "event_id": event_id,
        "material_id": material["id"],
        "impacted_product_ids": list(impacted_product_ids),
        "impacted_order_ids": [o["id"] for o in impacted_orders]
    }

    return event, ground_truth
```

### 3.5 Political Unrest / Strike Event

```python
def generate_unrest_event(regions, facilities, routes):
    region = random.choice(regions)
    event_id = make_id("EV_UNREST")

    event = {
        "id": event_id,
        "type": "PoliticalUnrest",
        "region_id": region["id"],
        "impacted_sectors": ["transport", "manufacturing"],
        "severity": random.choice(["medium", "high"])
    }

    impacted_facilities = [
        f for f in facilities if f["region_id"] == region["id"]
    ]
    impacted_facility_ids = {f["id"] for f in impacted_facilities}

    impacted_routes = [
        r for r in routes
        if any(node_id in impacted_facility_ids for node_id in [r["origin_node_id"], r["destination_node_id"]])
    ]
    impacted_route_ids = {r["id"] for r in impacted_routes}

    ground_truth = {
        "event_id": event_id,
        "region_id": region["id"],
        "impacted_facility_ids": list(impacted_facility_ids),
        "impacted_route_ids": list(impacted_route_ids)
    }

    return event, ground_truth
```

## 4. Test Scenario Bundles

For each synthetic event generator, define scenario bundles:

- Single-clean-event scenarios: one event, consistent data, no concurrent disruptions.
- Multi-event scenarios: combine two or more events (e.g., port closure + export control) with merged ground truth.
- Edge-case scenarios: missing coordinates, incomplete BOMs, ambiguous regions, conflicting data.
- Stress scenarios: many events in short time over large graphs to test performance and robustness.

## 5. Using Synthetic Data in Tests

- Ingest generated tables into the graph and document stores.
- Fire synthetic events into the streaming ingestion pipeline.
- Capture pipeline outputs (impacted entities, recommended actions, LLM narratives).
- Compare against ground_truth objects:
  - Propagation correctness: impacted IDs match.
  - Retrieval coverage: required nodes/documents appear in context.
  - Generation accuracy: key facts and mitigation suggestions match expectations.

## 6. Extensions

- Add probabilistic labels (e.g., delayed_with_probability) for advanced propagation models.
- Annotate scenarios with expert-written summaries to evaluate LLM narrative quality.
- Parameterize generator for small unit-test graphs vs large stress-test networks.
