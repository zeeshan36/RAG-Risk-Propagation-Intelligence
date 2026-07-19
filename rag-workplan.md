# Supply Chain Risk Propagation GraphRAG Pipeline Workplan

## 1. Objectives and Scope

- Provide real-time impact analysis for sudden disruptions (ports, facilities, routes, suppliers, sanctions, weather, cyber incidents).
- Support multi-hop risk propagation from events to suppliers, routes, facilities, SKUs, customers, and revenue.
- Offer actionable mitigation recommendations (reroutes, resourcing, prioritization) grounded in graph context and contracts.
- Cover initial scenarios: sudden port closure, extreme weather, cyber attack on logistics provider, export controls/sanctions, political unrest/strikes.

## 2. Stakeholders and Requirements

- Stakeholder groups: supply chain/logistics, procurement, sales/customer success, risk & compliance, IT/security, finance.
- Run domain workshops to:
  - Identify critical customers, SKUs, routes, suppliers, and facilities.
  - Define what "impact" means for each team (e.g., delay beyond SLA, revenue at risk, margin risk, compliance exposure).
  - Map desired outputs: dashboards, alerts, narrative reports, API responses.

## 3. Data Landscape and Governance

### 3.1 Internal Systems

- ERP: orders, BOMs, suppliers, SKUs, invoices, financials.
- TMS/WMS: shipments, lanes, routes, carriers, warehouse locations, inventory levels.
- CRM: customers, contracts, SLAs, priority tiers.
- Procurement portals: supplier profiles, performance data, certifications.
- Contract repositories: legal clauses, penalties, force majeure, rerouting rights.

### 3.2 External Data

- Weather/climate APIs and hazard maps.
- Sanctions and export control lists (OFAC, EU, UN, national lists).
- News feeds and risk intelligence (ports, strikes, political unrest).
- Cyber threat intelligence and incident feeds for key providers.

### 3.3 Spatial Data

- Geospatial representations of ports, facilities, warehouses, factories, customer regions, and route segments (points, lines, polygons).

### 3.4 Governance

- Define ownership, SLAs, and access controls for each source.
- Classify data (public, internal, restricted) and enforce RBAC.
- Establish data quality rules and freshness thresholds.

## 4. Knowledge Graph and Schema Design

### 4.1 Core Node Types

- Physical: Facility, Warehouse, Factory, Port, Region, RouteSegment.
- Logistical: Shipment, Container, Order, SKU/Product, Carrier.
- Organizational: Supplier, Customer, LogisticsProvider, BusinessUnit.
- Financial/contractual: Contract, SLA, Invoice, RevenueStream.
- Risk/Event: Event with subtypes (PortClosure, ExtremeWeather, CyberIncident, ExportControl, PoliticalUnrest, Strike, etc.).

### 4.2 Edge Types

- Structural edges: supplies, ships_to, served_by, located_in, uses_route, depends_on, complies_with.
- Exposure edges: exposed_to_risk, affected_by_event, alternative_for, backup_for.
- Financial edges: contributes_to_revenue, contributes_to_margin, has_penalty_in_contract.
- Temporal edges: valid_from, valid_to, occurred_at, forecast_for, updated_at.

### 4.3 Schema Validation

- Validate that typical queries are supported by explicit paths, for example:
  - Event -> Port -> RouteSegment -> Shipment -> Order -> Customer -> RevenueStream.
  - ExportControl -> Material -> Supplier -> Component -> BOM -> Product -> Order -> Customer.

## 5. Event Ontology and Propagation Rules

### 5.1 Event Model

- Common attributes: type, start_time, expected_duration, severity, confidence, data_source, region/geometry.
- Type-specific attributes:
  - PortClosure: port_id, affected_operations (full/partial), impacted modes.
  - ExtremeWeather: hazard_type, intensity, affected_polygon, lead_time.
  - CyberIncident: provider_id, impacted systems, functional impact (tracking, booking, billing).
  - ExportControl: material_id, country_id, restriction_type, exceptions.
  - PoliticalUnrest/Strike: region_id, impacted sectors, likely duration.

### 5.2 Propagation Rules

- Rule examples:
  - PortClosure affects port -> all route segments using that port -> shipments on those segments -> orders -> customers -> revenue streams.
  - ExtremeWeather affects polygon -> facilities and route segments inside polygon -> inventory and production -> downstream orders and customers.
  - ExportControl affects material -> suppliers of that material -> components and BOMs -> products -> orders -> customers and revenue.
  - CyberIncident affects logistics provider -> lanes operated by provider -> shipments on those lanes -> orders and customers (visibility and delay risk).

- Implement rules using:
  - Declarative graph queries or a rule DSL.
  - Optional graph ML to estimate propagation weights and probabilities.

## 6. Data Ingestion Architecture

### 6.1 Batch Ingestion (Historical Backbone)

- Extract from ERP/TMS/WMS/CRM/procurement and normalize into canonical models.
- Build initial knowledge graph:
  - Map entities to nodes and resolve identities across systems.
  - Create structural, financial, and contractual edges.
- Ingest contracts and regulatory documents:
  - Use LLM-based extractors to identify clauses and link them to Contract and Regulation nodes.

### 6.2 Streaming Ingestion (Events and Updates)

- Connect to event streams:
  - TMS/WMS: shipment status changes, reroutes, delivery confirmations.
  - Facility monitoring: outages, capacity changes.
  - External APIs: weather alerts, sanctions updates, news micro-events.

- For each incoming event:
  - Parse and classify into event ontology using pattern matching + LLM.
  - Bind to graph entities via ID matching and geospatial joins.
  - Create Event node and exposure edges, run propagation rules to update impacted nodes.

- Maintain CDC pipelines for master data changes.

## 7. Infrastructure and Storage

- Graph database:
  - Choose a scalable property graph store and design indexes on ports, facilities, suppliers, customers, regions.
- Vector store:
  - Create embeddings for document chunks (contracts, SLAs, regulations, incident reports) and index them by node IDs.
- Spatial database:
  - Store geometries and indexes for spatial filters and joins.
- Orchestration:
  - Use a RAG framework to combine graph traversal and vector retrieval.
- Observability:
  - Logging, metrics, tracing, and graph health dashboards (node/edge counts, staleness indicators).

## 8. GraphRAG Retrieval Architecture

### 8.1 Query Understanding

- Classify incoming queries:
  - Scenario impact ("impact of event X on customers in region Y").
  - Exploratory vulnerability ("top 10 most vulnerable routes").
  - Mitigation planning ("best reroute options for shipments affected by event Z").

- Extract anchors (event_id, supplier_id, port_id, region, time horizon) via LLMs.

### 8.2 Graph Retrieval

- Local retrieval:
  - Starting at an Event node, traverse a bounded neighborhood to find affected shipments, orders, customers, facilities, routes.

- Global retrieval:
  - Use graph algorithms to identify central suppliers, bottleneck routes, and vulnerable clusters for more strategic queries.

### 8.3 Text Retrieval

- Retrieve relevant contracts, SLAs, regulations, historical incident reports using embeddings.
- Link text chunks to graph nodes so the LLM sees both structure and evidence.

### 8.4 Generation Layer

- Compose prompts containing:
  - Structured graph paths and metrics.
  - Text snippets from contracts, playbooks, and incident histories.

- Instruct the LLM to:
  - Explain impact along explicit paths.
  - Quantify risk (orders, shipments, revenue, lead time changes).
  - Recommend mitigation actions referencing alternative nodes (backup facilities, routes, suppliers).

- Include guardrails (templates, explicit "use only provided facts", consistency checks).

## 9. Scenario-Specific Workflows

### 9.1 Sudden Port Closure

- Trigger: PortClosure event tied to Port node.
- GraphRAG steps:
  - Traverse from port to routes, shipments, orders, customers, revenue.
  - Retrieve contracts and SLAs linked to impacted customers and carriers.
- Outputs:
  - Impact dashboard listing shipments, customers, SKUs, revenue at risk.
  - LLM-generated narrative with prioritized reroute options and communication recommendations.

### 9.2 Extreme Weather

- Trigger: ExtremeWeather event with polygon and severity.
- GraphRAG steps:
  - Spatial join to facilities and route segments; traverse to shipments, orders, inventory.
  - Retrieve disaster recovery playbooks and historical event reports.
- Outputs:
  - Risk map overlay; list of facilities and shipments at high/medium/low risk.
  - LLM narrative with stock repositioning, production shifts, and transport adjustments.

### 9.3 Cyber Attack on Logistics Provider

- Trigger: CyberIncident event tied to LogisticsProvider node.
- GraphRAG steps:
  - Traverse provider to lanes, shipments, orders, customers.
  - Retrieve SLAs, cyber incident response documents, and prior cases.
- Outputs:
  - Impact list of shipments with tracking loss or delay risk.
  - LLM narrative recommending rerouting, alternative providers, and customer messaging.

### 9.4 Export Control / Sanctions

- Trigger: ExportControl event tied to Material/Country/Supplier nodes.
- GraphRAG steps:
  - Traverse material/country to suppliers, BOM components, products, orders, customers, revenue.
  - Retrieve regulatory text and compliance policies.
- Outputs:
  - Affected products, orders, customers, revenue; list of alternate materials/suppliers.
  - LLM narrative describing compliance obligations and mitigation paths.

### 9.5 Political Unrest / Strikes

- Trigger: PoliticalUnrest/Strike event tied to Region and sector nodes.
- GraphRAG steps:
  - Spatial join to facilities/routes; traverse to suppliers, shipments, orders.
  - Retrieve labor law documents and prior event histories.
- Outputs:
  - Scenario range (best/worst case), facilities and routes at risk.
  - LLM narrative recommending production reallocation, demand throttling, and safety stock adjustments.

## 10. Testing and Evaluation

- Historical scenario replay:
  - Replay past disruptions and compare outputs to known impacts and decisions.
- Synthetic scenario testing:
  - Use synthetic graphs and events with labeled ground truth to validate propagation, retrieval, and generation.
- Metrics:
  - Retrieval: precision/recall on impacted nodes, hit rate for key contracts/playbooks.
  - Generation: factual accuracy, alignment with expert assessments, user trust.
  - System: latency, throughput, resource usage.

## 11. Security, Compliance, and Operations

- Role-based access control for sensitive financial and customer data.
- Audit logging for all queries, retrieved subgraphs, and recommendations.
- Disaster recovery and multi-region deployment for the graph store.
- Human-in-the-loop processes for high-impact actions.

## 12. Implementation Roadmap (High-Level)

- Phase 1 (0–2 months): Stakeholder alignment, requirements, data inventory, governance.
- Phase 2 (2–5 months): Schema design, initial graph construction, spatial integration.
- Phase 3 (4–8 months): Streaming ingestion, GraphRAG infra, core retrieval pipeline.
- Phase 4 (7–12 months): Scenario workflows, evaluation suite, UI integration.
- Phase 5 (12+ months): Global rollout, more event types, advanced propagation ML, continuous tuning.
