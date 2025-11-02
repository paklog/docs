# Apache Pinot Adoption Plan for Paklog’s Event‑Driven Data Mesh

## 1) Goals & Principles
- Domain ownership: each service team owns its source‑aligned data product(s).
- Kafka as the backbone: Pinot consumes directly from Kafka topics defined in AsyncAPI.
- Near real‑time analytics: <2s end‑to‑end latency for priority products.
- Schemas as contracts: derive Pinot schemas from AsyncAPI and CloudEvents payloads.
- Self‑serve: standard templates, CI/CD, and a UI for discovery and querying.
- Secure by default: TLS/SASL to Kafka; RBAC on tables; governance & lineage.

## 2) Chosen UI(s)
- Primary Data Mesh UI (catalog & ownership): DataHub (OSS) for data product discovery, ownership, lineage, SLAs, and governance metadata. Pinot tables will be surfaced in DataHub via the Pinot and Kafka ingestion sources.
- Query & Visualization UI: Apache Superset connected to Pinot for ad‑hoc SQL, dashboards, and self‑serve exploration by domain teams.

Rationale: DataHub provides the “data mesh product” experience (contracts, ownership, lineage) and Superset gives an easy, OSS query/BI layer for Pinot. Pinot’s built‑in Controller UI remains for admin/ops.

## 3) High‑Level Architecture
- Kafka topics (from `apis/**/asyncapi.yaml`) are the source of truth.
- Pinot Realtime tables ingest from Kafka via LLC (low‑level consumer) with JSON decoder.
- Optional hybrid tables: Realtime + Offline for cost/performance (batch compact to Parquet in object storage, then ingest as offline segments). Phase 2.
- Pinot tenants per domain (e.g., `tenant: domain-fulfillment`, `tenant: domain-support`, etc.) to isolate resources and manage SLAs.
- DataHub catalogs Kafka topics, Pinot datasets, ownership, tags, and lineage; Superset connects to Pinot for querying.

## 4) Standards & Conventions
- Table naming: `dp_<service>_<product>_v1` (Pinot creates `_REALTIME` internally). Example: `dp_order_management_events_v1`.
- Common event columns:
  - CloudEvents envelope: `event_time`, `event_id`, `event_type`, `event_source`, `event_subject`, `trace_id`, `correlation_id`.
  - Domain keys (e.g., `order_id`, `ticket_id`, `sku`, `lpn`, `wave_id`).
- Time column: `event_time` (EPOCH millis) as `timeColumnName` for ingestion and TTL.
- Dedup/upsert:
  - Event tables: enable upsert with `primaryKeyColumns: ["event_id"]` to deduplicate at‑least‑once delivery.
  - Latest‑state tables (selective): upsert by entity key (e.g., `sku`, `ticket_id`) with `partialUpsert` if needed.
- Indexing defaults:
  - Inverted index on common dims (e.g., `event_type`, `warehouse_id`, `sku`).
  - Bloom filters for high‑cardinality keys (e.g., `order_id`, `ticket_id`).
  - Range index on numeric/time filter columns (e.g., `event_time`, `lat`, `lon`).
  - Star‑tree for aggregate‑heavy products (Phase 2 after baselines).
- Retention policy: default 30 days for event tables; domain‑specific overrides per product.
- Security & PII:
  - Tag columns with `classification` (public/internal/confidential/restricted). Avoid PII in Pinot where possible; or tokenize in ingest transforms.

## 5) Security & Access
- Kafka:
  - Use cluster security from AsyncAPI: SASL/SCRAM for production and staging.
  - Configure Pinot stream properties with TLS/SASL and Schema Registry (if applicable).
- Pinot:
  - Enable RBAC; group roles per domain.
  - Multi‑tenancy: per‑domain server and broker tenants with replication >= 2.
- DataHub & Superset:
  - SSO via OAuth/OIDC; restrict sensitive datasets to domain roles.

## 6) Infra & Sizing (initial)
- Deploy Pinot (Controller, Broker, Server, Minion) on Kubernetes. Co‑deploy ZooKeeper/Helix or use managed ZK.
- Start with 3 controller replicas, 3 brokers, 6 servers (r5d.xlarge‑equiv) for core domains.
- Kafka partitions: align Pinot parallelism with topic partitions for high‑throughput streams.
- Storage: NVMe/local SSD for Pinot Servers; object storage (S3/GCS) for batch segments (Phase 2).

## 7) Ingestion Design
- Realtime ingestion via Kafka LLC:
  - `stream.kafka.consumer.type: lowlevel`
  - JSON decoder: `org.apache.pinot.plugin.stream.kafka.KafkaJSONMessageDecoder`
  - Transform configs to flatten CloudEvents and nested payloads from AsyncAPI.
- Example transforms:
  - `event_time = fromDateTime(time, "yyyy-MM-dd'T'HH:mm:ssXXX")`
  - `trace_id = jsonPathString(extensions, '$.traceparent')`
  - `ticket_id = jsonPathString(data, '$.ticket.id')` (service‑specific)

## 8) CI/CD & Automation
- Repo layout:
  - `pinot/`
    - `schemas/<service>/<product>.schema.json`
    - `tables/<service>/<product>.table.json`
    - `data-products/<service>/<product>.yaml` (mesh metadata for DataHub)
  - Generator (Phase 2): derive candidate Pinot schemas from AsyncAPI payloads and CE envelope.
- Pipelines:
  - Validate schema/table JSON with `pinot-admin.sh Validate`.
  - Apply via Controller API per environment (dev → staging → prod) with approvals.
  - Register datasets in DataHub on merge to `main`.

## 9) Example Pinot Configs (selected)

### 9.1 Order Management — source‑aligned event product
Schema `dp_order_management_events_v1`:
```json
{
  "schemaName": "dp_order_management_events_v1",
  "dimensionFieldSpecs": [
    {"name": "event_id", "dataType": "STRING"},
    {"name": "event_type", "dataType": "STRING"},
    {"name": "event_source", "dataType": "STRING"},
    {"name": "event_subject", "dataType": "STRING"},
    {"name": "order_id", "dataType": "STRING"},
    {"name": "seller_fulfillment_order_id", "dataType": "STRING"},
    {"name": "correlation_id", "dataType": "STRING"},
    {"name": "trace_id", "dataType": "STRING"}
  ],
  "dateTimeFieldSpecs": [
    {"name": "event_time", "dataType": "LONG", "format": "1:MILLISECONDS:EPOCH", "granularity": "1:MILLISECONDS"}
  ],
  "primaryKeyColumns": ["event_id"]
}
```
Table (Realtime) `dp_order_management_events_v1`:
```json
{
  "tableName": "dp_order_management_events_v1",
  "tableType": "REALTIME",
  "tenants": {"server": "domain-fulfillment", "broker": "domain-fulfillment"},
  "segmentsConfig": {
    "timeColumnName": "event_time",
    "replication": "2",
    "retentionTimeUnit": "DAYS",
    "retentionTimeValue": "30"
  },
  "tableIndexConfig": {
    "invertedIndexColumns": ["event_type"],
    "bloomFilterColumns": ["order_id", "event_id"],
    "rangeIndexColumns": ["event_time"]
  },
  "ingestionConfig": {
    "transformConfigs": [
      {"columnName": "event_id", "transformFunction": "jsonPathString($, '$.id')"},
      {"columnName": "event_type", "transformFunction": "jsonPathString($, '$.type')"},
      {"columnName": "event_source", "transformFunction": "jsonPathString($, '$.source')"},
      {"columnName": "event_subject", "transformFunction": "jsonPathString($, '$.subject')"},
      {"columnName": "event_time", "transformFunction": "fromDateTime(jsonPathString($, '$.time'), 'yyyy-MM-dd''T''HH:mm:ss[.SSS]XXX')"},
      {"columnName": "order_id", "transformFunction": "jsonPathString($, '$.data.order_id')"},
      {"columnName": "seller_fulfillment_order_id", "transformFunction": "jsonPathString($, '$.data.seller_fulfillment_order_id')"}
    ]
  },
  "upsertConfig": {"mode": "FULL", "primaryKeyColumns": ["event_id"], "hashFunction": "NONE"},
  "routing": {"instanceSelectorType": "strictReplication"},
  "metadata": {"customConfigs": {"product.owner": "fulfillment-platform@paklog.com", "product.sla": "p95<2s"}},
  "streamConfig": {
    "streamType": "kafka",
    "stream.kafka.topic.name": "fulfillment.order_management.v1.events",
    "stream.kafka.consumer.type": "lowlevel",
    "stream.kafka.decoder.class.name": "org.apache.pinot.plugin.stream.kafka.KafkaJSONMessageDecoder",
    "stream.kafka.broker.list": "<BROKERS>",
    "stream.kafka.security.protocol": "SASL_PLAINTEXT",
    "stream.kafka.sasl.mechanism": "SCRAM-SHA-512"
  }
}
```

### 9.2 Inventory — latest stock level (upsert by SKU)
Schema `dp_inventory_stock_level_v1`:
```json
{
  "schemaName": "dp_inventory_stock_level_v1",
  "dimensionFieldSpecs": [
    {"name": "sku", "dataType": "STRING"}
  ],
  "metricFieldSpecs": [
    {"name": "quantity_on_hand", "dataType": "INT"},
    {"name": "quantity_allocated", "dataType": "INT"},
    {"name": "available_to_promise", "dataType": "INT"}
  ],
  "dateTimeFieldSpecs": [
    {"name": "event_time", "dataType": "LONG", "format": "1:MILLISECONDS:EPOCH", "granularity": "1:MILLISECONDS"}
  ],
  "primaryKeyColumns": ["sku"]
}
```
Table (Realtime) `dp_inventory_stock_level_v1` (consumes `fulfillment.inventory.v1.events` `StockLevelChanged`):
```json
{
  "tableName": "dp_inventory_stock_level_v1",
  "tableType": "REALTIME",
  "upsertConfig": {"mode": "PARTIAL", "primaryKeyColumns": ["sku"], "hashFunction": "NONE"},
  "ingestionConfig": {
    "transformConfigs": [
      {"columnName": "sku", "transformFunction": "jsonPathString($, '$.data.sku')"},
      {"columnName": "event_time", "transformFunction": "fromDateTime(jsonPathString($, '$.time'), 'yyyy-MM-dd''T''HH:mm:ss[.SSS]XXX')"},
      {"columnName": "quantity_on_hand", "transformFunction": "jsonPathInt($, '$.data.new_stock_level.quantity_on_hand')"},
      {"columnName": "quantity_allocated", "transformFunction": "jsonPathInt($, '$.data.new_stock_level.quantity_allocated')"},
      {"columnName": "available_to_promise", "transformFunction": "jsonPathInt($, '$.data.new_stock_level.available_to_promise')"}
    ]
  },
  "segmentsConfig": {"timeColumnName": "event_time", "replication": "2"},
  "tableIndexConfig": {"bloomFilterColumns": ["sku"], "rangeIndexColumns": ["event_time"]},
  "streamConfig": {
    "streamType": "kafka",
    "stream.kafka.topic.name": "fulfillment.inventory.v1.events",
    "stream.kafka.consumer.type": "lowlevel",
    "stream.kafka.decoder.class.name": "org.apache.pinot.plugin.stream.kafka.KafkaJSONMessageDecoder",
    "stream.kafka.broker.list": "<BROKERS>"
  }
}
```

### 9.3 Customer Experience Hub — tickets events
Schema `dp_customerx_ticket_events_v1` and realtime table ingesting from:
- `customerx.tickets.created`
- `customerx.tickets.updated`
- `customerx.tickets.resolved`

Key columns: `event_id` (dedup), `ticket_id`, `customer_id`, `status`, `priority`, `channel`, `agent_id`, `warehouse_id`, `event_time`.

### 9.4 Physical Tracking — movement & location events
Realtime product `dp_physical_tracking_events_v1` ingesting channels:
- `licenseplate.created|moved|consumed|item.added|item.removed`
- `location.state.changed|blocked|unblocked`

Key columns: `event_id`, `lpn`, `warehouse_id`, `from_location`, `to_location`, `movement_type`, `changed_at -> event_time`.

### 9.5 Wave Planning — wave lifecycle
Realtime product `dp_wave_planning_events_v1` ingesting channels: `wave.created|optimized|released|started|completed|cancelled|merged`.

### 9.6 Value‑Added Services — unified VAS events
Realtime product `dp_vas_events_v1` from topic `support-intelligence.value-added-services.events`.

### 9.7 Yard Management — yard events
Realtime product `dp_yard_management_events_v1` from topic `transportation-logistics.yard-management.events`.

## 10) Per‑Service Source‑Aligned Data Products (min. one per service)
Below are one source‑aligned product per service (based on AsyncAPI). All are Realtime unless noted. Owners are indicative and should be adjusted.

- cartonization → `dp_cartonization_events_v1`
  - Kafka: `cartonization.requests|responses|solutions|events` (start with `cartonization.events`)
  - Keys: `event_id`, `order_id`, `session_id`; time: `event_time`; owner: WMS

- cross-docking-operations → `dp_cross_docking_events_v1`
  - Kafka: `transportation-logistics.cross-docking.events`
  - Keys: `event_id`, `shipment_id`, `dock_id`; time: `event_time`; owner: TL

- customer-experience-hub → `dp_customerx_ticket_events_v1`
  - Kafka: `customerx.tickets.created|updated|resolved`
  - Keys: `event_id`(dedup), `ticket_id`, `customer_id`; time: `event_time`; owner: CX

- digital-twin-simulation → `dp_digital_twin_events_v1`
  - Kafka: `digital-twin.events`
  - Keys: `event_id`, `simulation_id`; time: `event_time`; owner: R&D

- equipment-asset-management → `dp_equipment_events_v1`
  - Kafka: `equipment.asset.lifecycle|maintenance.operations|workorders|predictions|utilization` (start with `asset.lifecycle`)
  - Keys: `event_id`, `asset_id`; time: `event_time`; owner: Ops

- financial-settlement → `dp_financial_settlement_events_v1`
  - Kafka: (to be confirmed; no AsyncAPI found) — onboard when topics available.

- inventory → `dp_inventory_stock_level_v1` (upsert latest by `sku`)
  - Kafka: `fulfillment.inventory.v1.events` (StockLevelChanged)
  - Keys: `sku`; time: `event_time`; owner: Inventory

- last-mile-delivery → `dp_last_mile_events_v1`
  - Kafka: `delivery-events` (per AsyncAPI)
  - Keys: `event_id`, `shipment_id`, `stop_id`; time: `event_time`; owner: TL

- location-master-service → `dp_location_master_events_v1`
  - Kafka: `location.created|capacity.changed|slotting.changed|status.changed|blocked|unblocked|deactivated|zone.created`
  - Keys: `location_id`, `warehouse_id`; time: `event_time`; owner: WMS

- order-management → `dp_order_management_events_v1`
  - Kafka: `fulfillment.order_management.v1.events`
  - Keys: `event_id`, `order_id`; time: `event_time`; owner: OM

- pack-ship-service → `dp_pack_ship_events_v1`
  - Kafka: `packing.*`, `shipment.created|label.generated|dispatched`
  - Keys: `event_id`, `session_id`, `shipment_id`; time: `event_time`; owner: WES

- performance-intelligence → `dp_performance_intelligence_events_v1`
  - Kafka: (to be confirmed) — define metrics ingestion topics and onboard.

- physical-tracking-service → `dp_physical_tracking_events_v1`
  - Kafka: `licenseplate.*`, `location.*`, `physical.movement`, `rtls.position.update`
  - Keys: `event_id`, `lpn`, `movement_id`; time: `event_time`; owner: WES

- pick-execution-service → `dp_pick_execution_events_v1`
  - Kafka: `pick.session.started|completed|cancelled|confirmed|short|path.optimized`, `putwall.*`
  - Keys: `event_id`, `pick_session_id`, `order_id`; time: `event_time`; owner: WES

- predictive-analytics-platform → `dp_predictive_analytics_events_v1`
  - Kafka: (to be confirmed) — onboard predictive outputs (forecasts, scores) when topics are ready.

- product-catalog → `dp_product_catalog_events_v1`
  - Kafka: `product.events`
  - Keys: `event_id`, `product_id`, `sku`; time: `event_time`; owner: Catalog

- quality-compliance → `dp_quality_compliance_events_v1`
  - Kafka: `support-intelligence.quality-compliance.events`
  - Keys: `event_id`, `order_id`; time: `event_time`; owner: QA

- returns-management → `dp_returns_events_v1`
  - Kafka: `paklog.returns.*` (initiated, rma‑approved/denied, received, condition‑assessed, disposition, refund, completed)
  - Keys: `event_id`, `return_id`, `order_id`; time: `event_time`; owner: Returns

- robotics-fleet-management → `dp_robotics_events_v1`
  - Kafka: `robot.*` (registered, task.*, battery.*, charging.*)
  - Keys: `event_id`, `robot_id`, `task_id`; time: `event_time`; owner: Robotics

- shipment-transportation → `dp_shipment_transport_events_v1`
  - Kafka: `fulfillment.shipment.v1.events` (plus upstream `fulfillment.warehouse.v1.events` as needed)
  - Keys: `event_id`, `shipment_id`; time: `event_time`; owner: TL

- sustainability-management → `dp_sustainability_events_v1`
  - Kafka: `sustainability.*` (emissions, goals, waste, renewable, route, certification, offset, report)
  - Keys: `event_id`, `shipment_id`; time: `event_time`; owner: Sustainability

- task-execution-service → `dp_task_execution_events_v1`
  - Kafka: `task.created|assigned|started|completed|failed|cancelled|priority.changed|queue.rebalanced`
  - Keys: `event_id`, `task_id`, `worker_id`; time: `event_time`; owner: WES

- value-added-services → `dp_vas_events_v1`
  - Kafka: `support-intelligence.value-added-services.events`
  - Keys: `event_id`, `order_id`; time: `event_time`; owner: VAS

- wave-planning-service → `dp_wave_planning_events_v1`
  - Kafka: `wave.*` (created, optimized, released, started, completed, cancelled, merged)
  - Keys: `event_id`, `wave_id`; time: `event_time`; owner: WMS

- wes-orchestration-engine → `dp_wes_orchestration_events_v1`
  - Kafka: `physical-operations.wes-orchestration.workflow-events` (start with workflow)
  - Keys: `event_id`, `workflow_id`; time: `event_time`; owner: WES

- workload-planning-service → `dp_workload_planning_events_v1`
  - Kafka: `forecast.generated|plan.created|approved|published|cancelled|worker.assigned|removed|plan.optimized`
  - Keys: `event_id`, `plan_id`; time: `event_time`; owner: Ops

- yard-management-system → `dp_yard_management_events_v1`
  - Kafka: `transportation-logistics.yard-management.events`
  - Keys: `event_id`, `yard_session_id`, `trailer_id`; time: `event_time`; owner: TL

For each product, DataHub metadata (owner, SLA, domain, tags, PII flags) is stored under `data-products/<service>/<product>.yaml` and synced to the catalog.

## 11) Observability & SLOs
- Ingestion lag: alert when `currentTime - max(event_time)` > 60s.
- Query latency: p95 < 500ms for filters on common dims; p95 < 2s for aggregates.
- Freshness: p95 end‑to‑end (Kafka → Pinot visible) < 5s.
- Error budgets and on‑call routing per domain tenant.

## 12) Rollout Plan
Phase 0: Foundations (1–2 weeks)
- Stand up dev Pinot cluster, connect to dev Kafka, enable Superset and DataHub.
- Create shared templates for schema/table configs and DataHub product YAML.

Phase 1: First‑class products (2–3 weeks)
- Onboard 6 key services: Order Management, Inventory, Physical Tracking, Pack & Ship, Customer Experience, VAS.
- Ship example dashboards in Superset; register products in DataHub with ownership.

Phase 2: Scale (3–4 weeks)
- Onboard remaining services; introduce hybrid tables + star‑tree where needed.
- Add compaction/batch pipeline to object storage for cost efficiency.

Phase 3: Governance & QoS (ongoing)
- Enforce data contracts from AsyncAPI, schema evolution checks in CI.
- Tighten RBAC, PII handling, lineage coverage.

## 13) Next Steps (Actionable)
- Pick the first 3 services to implement end‑to‑end (recommend: Order Management, Inventory, Physical Tracking).
- Create `pinot/` folder with schemas and tables for those 3 products.
- Stand up Superset + DataHub in staging and wire Pinot.
- Define SLAs and owners in DataHub for the initial products.
- Validate ingestion configs against staging Kafka; run test traffic.

