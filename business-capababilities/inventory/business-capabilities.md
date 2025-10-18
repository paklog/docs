# Inventory Service - Business Capabilities

**Service Overview**: The Inventory Service serves as the single source of truth for all product stock levels across the fulfillment network. It manages inventory quantities, allocations, reservations, locations, and provides a comprehensive audit trail through an immutable ledger pattern.

**Architecture**: Hexagonal Architecture with Domain-Driven Design (DDD)
**Technology Stack**: Spring Boot 3.2, Spring Data MongoDB, Spring Kafka, CloudEvents
**Domain Model**: Rich domain model with aggregates, entities, value objects, and domain events

---

## L1: Inventory Management

### L1.1: Description
Comprehensive management of product stock levels, including tracking on-hand quantities, allocated inventory, available-to-promise (ATP) calculations, and multi-location inventory management.

### L1.2: Strategic Value
- **Inventory Accuracy**: Single source of truth for all inventory data
- **Order Fulfillment**: Enable accurate ATP calculations for order promising
- **Operational Efficiency**: Real-time inventory visibility across all locations
- **Financial Accuracy**: Support accurate inventory valuation and reporting
- **Customer Satisfaction**: Prevent overselling and stockouts

---

## L2: Stock Level Management

### L2.1: Description
Track and manage inventory quantities at the product level, including on-hand quantities, allocated amounts, and available-to-promise calculations.

### L2.2: Business Value
- Real-time visibility into inventory positions
- Accurate ATP calculations for order fulfillment
- Prevention of overselling and stockouts
- Support for inventory planning and replenishment

### L2.3: L3 Capabilities

#### L3.1.1: Quantity on Hand Tracking
**Description**: Track the physical quantity of each product available in the warehouse.

**Technical Implementation**:
- `ProductStock` aggregate maintains `quantityOnHand` field
- Updates via inventory adjustment transactions
- Supports multi-location tracking via `StockLocation` aggregate

**Business Rules**:
- Quantity on hand cannot be negative
- All changes recorded in immutable ledger
- Supports decimal quantities for catch-weight items

**Key Metrics**:
- Current quantity on hand by SKU
- Inventory accuracy percentage
- Stock level variance

**Domain Model**:
```java
class ProductStock {
  private String sku;
  private StockLevel stockLevel;
  - quantityOnHand: BigDecimal
  - quantityAllocated: BigDecimal
  - availableToPromise: BigDecimal
}
```

**Related Services**: Product Catalog (SKU validation)

---

#### L3.1.2: Quantity Allocated Tracking
**Description**: Track inventory quantities that have been allocated (reserved) for specific orders but not yet physically picked.

**Technical Implementation**:
- Separate `quantityAllocated` field in `ProductStock` aggregate
- Updated when orders are created/validated
- Decremented when items are picked
- Supports partial allocations

**Business Rules**:
- Allocated quantity cannot exceed quantity on hand
- Allocations have expiration timeouts (configurable)
- Expired allocations automatically released
- Allocation priority based on order priority

**Key Metrics**:
- Total allocated quantity by SKU
- Allocation expiration rate
- Average allocation duration

**Domain Events**:
- `InventoryAllocatedEvent`
- `AllocationExpiredEvent`
- `AllocationReleasedEvent`

**Related Services**: Order Management (allocation requests)

---

#### L3.1.3: Available-to-Promise (ATP) Calculation
**Description**: Calculate the quantity of inventory available for new orders, considering on-hand quantities, existing allocations, and safety stock.

**Technical Implementation**:
- Formula: `ATP = QuantityOnHand - QuantityAllocated - SafetyStock`
- Real-time calculation on query
- Cached for performance with cache invalidation on updates
- Supports future ATP with expected receipts

**Business Rules**:
- ATP cannot be negative (exposed as 0)
- Safety stock levels configurable per SKU
- Reserved quantities excluded from ATP
- Future ATP includes scheduled receipts

**Key Metrics**:
- ATP by SKU
- ATP fulfillment rate (orders vs. ATP)
- Safety stock coverage days

**API Endpoints**:
- `GET /api/v1/inventory/{sku}/atp` - Get current ATP
- `GET /api/v1/inventory/atp/batch` - Batch ATP check

**Related Services**: Order Management (ATP checks before order acceptance)

---

#### L3.1.4: Safety Stock Management
**Description**: Maintain minimum safety stock levels to prevent stockouts and support service level agreements.

**Technical Implementation**:
- `safetyStockLevel` field in `ProductStock` aggregate
- Configurable per SKU
- Alerts when stock falls below safety level
- Considered in ATP calculations

**Business Rules**:
- Safety stock levels set based on demand variability
- Can be overridden for specific SKUs
- Alerts generated when breached
- Excluded from ATP to prevent allocation

**Key Metrics**:
- Safety stock coverage by SKU
- Stockout incidents
- Service level achievement

**Related Services**: None (configuration data)

---

#### L3.1.5: Stock Level Adjustments
**Description**: Record inventory adjustments for receipts, cycle counts, damage, and other inventory transactions.

**Technical Implementation**:
- `AdjustStockLevelCommand` processed via application service
- Creates immutable `InventoryLedgerEntry` for audit trail
- Updates `ProductStock` aggregate atomically
- Supports various adjustment types (receipt, adjustment, damage, return, etc.)

**Business Rules**:
- All adjustments require reason code
- Negative adjustments cannot reduce stock below allocated quantity
- Adjustments create ledger entries for audit
- User/system identification captured

**Adjustment Types**:
- `RECEIPT` - Goods received
- `ADJUSTMENT` - Cycle count adjustment
- `DAMAGE` - Damaged goods removal
- `RETURN` - Customer return
- `TRANSFER` - Location transfer
- `SHRINKAGE` - Theft/loss
- `FOUND` - Found inventory

**Key Metrics**:
- Adjustment frequency by type
- Adjustment accuracy (cycle count variance)
- Shrinkage rate

**API Endpoints**:
- `POST /api/v1/inventory/{sku}/adjust` - Record adjustment

**Domain Events**:
- `StockLevelChangedEvent`
- `InventoryAdjustedEvent`

**Related Services**: Warehouse Operations (cycle counts, receipts)

---

## L2: Inventory Allocation & Reservation

### L2.1: Description
Manage the allocation and reservation of inventory for orders, ensuring that promised inventory is protected for fulfillment.

### L2.2: Business Value
- Prevent overselling by reserving inventory for orders
- Support multi-channel order fulfillment
- Enable order prioritization
- Provide reservation flexibility with hold/release capabilities

### L2.3: L3 Capabilities

#### L3.2.1: Inventory Allocation
**Description**: Allocate (soft reserve) inventory for orders, reducing available-to-promise without physical reservation.

**Technical Implementation**:
- `AllocateInventoryCommand` processed via domain service
- Updates `quantityAllocated` in `ProductStock` aggregate
- Creates allocation record with expiration timestamp
- Idempotent operation (supports retries)

**Business Rules**:
- Allocation requires sufficient ATP
- Allocations expire after timeout (default: 24 hours)
- Cannot allocate more than ATP
- Supports partial allocation

**Key Metrics**:
- Allocation success rate
- Average allocation time
- Allocation expiration rate

**API Endpoints**:
- `POST /api/v1/inventory/allocate` - Allocate inventory
- `POST /api/v1/inventory/allocate/batch` - Batch allocation

**Domain Events**:
- `InventoryAllocatedEvent`
- `AllocationFailedEvent`

**Related Services**: Order Management (allocation requests)

---

#### L3.2.2: Inventory Deallocation
**Description**: Release previously allocated inventory back to available-to-promise pool.

**Technical Implementation**:
- `DeallocateInventoryCommand` processed via domain service
- Decrements `quantityAllocated` in `ProductStock`
- Creates ledger entry for audit
- Handles partial deallocation

**Business Rules**:
- Can only deallocate previously allocated quantity
- Deallocation restores ATP immediately
- Creates audit trail entry
- Supports cancellation reason codes

**Key Metrics**:
- Deallocation rate (% of allocations)
- Deallocation reasons
- Impact on ATP availability

**API Endpoints**:
- `POST /api/v1/inventory/deallocate` - Deallocate inventory

**Domain Events**:
- `InventoryDeallocatedEvent`

**Related Services**: Order Management (order cancellations)

---

#### L3.2.3: Physical Reservation Management
**Description**: Create physical reservations at specific warehouse locations for allocated inventory.

**Technical Implementation**:
- `StockLocation` aggregate manages `PhysicalReservation` entities
- Links allocated inventory to physical locations
- Supports multi-location reservations
- Tracks reservation status (RESERVED, PICKED, CANCELLED)

**Business Rules**:
- Physical reservations require prior allocation
- Must specify warehouse location
- Reservations decrease location-level ATP
- Cannot reserve from locations without sufficient stock

**Key Metrics**:
- Reservation accuracy by location
- Average reservation duration
- Location utilization rates

**Domain Model**:
```java
class StockLocation {
  private String locationId;
  private String sku;
  private List<PhysicalReservation> reservations;
  private BigDecimal quantityAtLocation;
}
```

**Domain Events**:
- `PhysicalReservationCreatedEvent`
- `ReservationCancelledEvent`

**Related Services**: Warehouse Operations (picking instructions)

---

#### L3.2.4: Allocation Expiration Management
**Description**: Automatically expire and release allocations that have exceeded their time-to-live.

**Technical Implementation**:
- Scheduled background job scans for expired allocations
- Configurable TTL per allocation type (default: 24h)
- Automatic deallocation of expired reservations
- Notifications for expiring allocations (warnings)

**Business Rules**:
- Standard allocations expire after 24 hours
- Rush orders have extended TTL (48 hours)
- Expired allocations auto-released
- Notifications sent before expiration (4 hours warning)

**Key Metrics**:
- Expiration rate (target: <5%)
- Average time to fulfillment
- Recovery of expired inventory

**Related Services**: Order Management (expiration notifications)

---

## L2: Multi-Location Inventory Management

### L2.1: Description
Manage inventory across multiple warehouse locations, distribution centers, and storage areas.

### L2.2: Business Value
- Optimize inventory placement for efficient fulfillment
- Support distributed fulfillment networks
- Enable location-based picking strategies
- Improve inventory visibility across facilities

### L2.3: L3 Capabilities

#### L3.3.1: Location-Based Stock Tracking
**Description**: Track inventory quantities at specific physical locations within warehouses.

**Technical Implementation**:
- `StockLocation` aggregate per SKU-location combination
- Hierarchical location structure (warehouse → zone → aisle → bin)
- Location-level quantity tracking
- Aggregation to warehouse-level totals

**Business Rules**:
- Each location has unique identifier
- Locations belong to warehouse hierarchy
- Stock transfers between locations tracked
- Location capacity constraints enforced

**Key Metrics**:
- Stock by location
- Location utilization percentage
- Inventory distribution across locations

**Related Services**: Warehouse Operations (location management)

---

#### L3.3.2: Inter-Location Stock Transfers
**Description**: Transfer inventory between physical locations within or across warehouses.

**Technical Implementation**:
- `TransferStockCommand` creates two-phase transfer
- Decrements source location, increments destination
- Creates transfer ledger entries
- Supports transfer-in-transit tracking

**Business Rules**:
- Cannot transfer more than available at source
- Transfer requires confirmation at destination
- Failed transfers automatically reversed
- Creates audit trail for both locations

**Key Metrics**:
- Transfer volume by location pair
- Transfer completion time
- Transfer accuracy rate

**Domain Events**:
- `StockTransferInitiatedEvent`
- `StockTransferCompletedEvent`
- `StockTransferCancelledEvent`

**Related Services**: Warehouse Operations (transfer execution)

---

#### L3.3.3: Location-Based ATP Calculation
**Description**: Calculate available-to-promise at specific locations to support distributed order promising.

**Technical Implementation**:
- ATP calculation scoped to warehouse location
- Aggregates across storage locations within warehouse
- Supports multi-location sourcing strategies
- Real-time updates as inventory moves

**Business Rules**:
- Location ATP = Location QOH - Location Allocated
- Cross-location ATP requires aggregation
- Considers location-specific safety stock
- Respects location picking priority

**Key Metrics**:
- ATP by warehouse location
- Location fulfillment rate
- Cross-location fulfillment rate

**API Endpoints**:
- `GET /api/v1/inventory/{sku}/atp?location={warehouseId}`

**Related Services**: Order Management (location-based order routing)

---

## L2: Inventory Audit & Compliance

### L2.1: Description
Maintain comprehensive, immutable audit trails of all inventory transactions for compliance, financial reporting, and operational analysis.

### L2.2: Business Value
- Regulatory compliance (SOX, financial audits)
- Root cause analysis for inventory discrepancies
- Support for financial inventory valuation
- Complete transaction history for investigations

### L2.3: L3 Capabilities

#### L3.4.1: Immutable Inventory Ledger
**Description**: Maintain append-only ledger of all inventory transactions using event sourcing principles.

**Technical Implementation**:
- `InventoryLedgerEntry` entity for each transaction
- Immutable records (no updates/deletes)
- Chronological ordering with timestamps
- Includes before/after quantities and transaction metadata

**Business Rules**:
- Every inventory change creates ledger entry
- Ledger entries never modified or deleted
- Contains complete transaction context
- Supports reconstruction of inventory state at any point in time

**Ledger Entry Types**:
- ALLOCATION
- DEALLOCATION
- ADJUSTMENT
- TRANSFER
- PICK
- RECEIPT
- RETURN
- DAMAGE
- CYCLE_COUNT

**Key Metrics**:
- Ledger entry volume
- Ledger query performance
- Storage growth rate

**Domain Model**:
```java
class InventoryLedgerEntry {
  private String entryId;
  private String sku;
  private TransactionType transactionType;
  private BigDecimal quantityBefore;
  private BigDecimal quantityAfter;
  private BigDecimal quantityChange;
  private String reasonCode;
  private LocalDateTime timestamp;
  private String userId;
  private String referenceId; // order ID, receipt ID, etc.
}
```

**API Endpoints**:
- `GET /api/v1/inventory/{sku}/ledger` - Get transaction history

**Related Services**: None (internal audit capability)

---

#### L3.4.2: Transaction History Query
**Description**: Query historical inventory transactions for analysis, reporting, and auditing.

**Technical Implementation**:
- MongoDB queries on `InventoryLedgerEntry` collection
- Indexing on SKU, timestamp, transaction type
- Support for date range and transaction type filtering
- Pagination for large result sets

**Business Rules**:
- Historical data never deleted (retention: indefinite)
- Supports complex queries (date ranges, transaction types, users)
- Read-only access (immutable)

**Key Metrics**:
- Query response time
- Most frequent query patterns
- Data retention period

**API Endpoints**:
- `GET /api/v1/inventory/{sku}/ledger?from=date&to=date&type=ADJUSTMENT`

**Related Services**: Analytics/BI systems (reporting)

---

#### L3.4.3: Inventory Reconciliation
**Description**: Reconcile physical inventory counts with system records and identify discrepancies.

**Technical Implementation**:
- Comparison of cycle count results with system quantities
- Variance calculation and reporting
- Automated adjustment creation for approved variances
- Discrepancy threshold alerting

**Business Rules**:
- Reconciliation requires physical count data
- Variances above threshold require approval
- Approved variances create adjustment transactions
- All reconciliations create ledger entries

**Key Metrics**:
- Inventory accuracy rate (target: >99%)
- Variance by SKU
- Variance by location
- Cycle count frequency

**Related Services**: Warehouse Operations (cycle counting)

---

#### L3.4.4: Audit Trail Reporting
**Description**: Generate comprehensive audit reports for compliance and financial reporting.

**Technical Implementation**:
- Aggregate queries across ledger entries
- Support for standard report formats (inventory movement, valuation)
- Exportable in multiple formats (CSV, Excel, PDF)
- Scheduled report generation

**Business Rules**:
- Reports must include all transactions (no filtering)
- Support for date range selection
- Include user and system attribution
- Digitally signed for compliance

**Key Metrics**:
- Report generation time
- Report usage frequency
- Data completeness percentage

**Related Services**: Finance systems (inventory valuation)

---

## L2: Event-Driven Integration

### L2.1: Description
Publish domain events to enable real-time integration with other fulfillment services using event-driven architecture.

### L2.2: Business Value
- Enable real-time inventory visibility across services
- Support event-driven order orchestration
- Decouple services for scalability and resilience
- Provide reliable event delivery guarantees

### L2.3: L3 Capabilities

#### L3.5.1: Transactional Outbox Pattern
**Description**: Guarantee reliable event publishing using transactional outbox pattern to ensure events are never lost.

**Technical Implementation**:
- Events written to MongoDB outbox table in same transaction as domain changes
- Background processor reads outbox and publishes to Kafka
- Marks events as published after successful Kafka delivery
- Retry logic for failed publishing attempts

**Business Rules**:
- Events published exactly once (idempotent)
- Events published in order for same aggregate
- Failed events retried with exponential backoff
- Alert on prolonged publishing failures

**Key Metrics**:
- Outbox processing lag (target: <1 second)
- Publishing failure rate
- Event ordering accuracy

**Related Services**: All services (event consumers)

---

#### L3.5.2: Inventory Domain Event Publishing
**Description**: Publish rich domain events for all significant inventory state changes.

**Technical Implementation**:
- CloudEvents format for standardization
- Kafka as event bus
- Schema registry for event schemas
- Event versioning support

**Published Events**:
- `InventoryAllocatedEvent`
- `InventoryDeallocatedEvent`
- `StockLevelChangedEvent`
- `ItemPickedEvent`
- `PhysicalReservationCreatedEvent`
- `AllocationExpiredEvent`
- `StockTransferCompletedEvent`
- `LowStockAlertEvent`

**Event Schema Example**:
```json
{
  "id": "evt-12345",
  "type": "com.paklog.inventory.allocated",
  "source": "inventory-service",
  "specversion": "1.0",
  "datacontenttype": "application/json",
  "data": {
    "sku": "PROD-123",
    "quantityAllocated": 5,
    "orderId": "ORD-67890",
    "allocatedAt": "2025-10-18T10:30:00Z"
  }
}
```

**Business Rules**:
- Events published after successful domain operation
- Include correlation ID for tracing
- Contain sufficient data to avoid lookups
- Published to dedicated topic: `fulfillment.inventory.v1.events`

**Key Metrics**:
- Events published per minute
- Event processing latency (end-to-end)
- Event consumption errors

**Related Services**:
- Order Management (allocation events)
- Warehouse Operations (pick events)
- Analytics (all events)

---

#### L3.5.3: Event Consumption
**Description**: Consume events from other services to maintain inventory accuracy and respond to fulfillment activities.

**Technical Implementation**:
- Kafka consumers for relevant topics
- Event handlers mapped to domain commands
- Idempotent processing (duplicate detection)
- Dead letter queue for failed events

**Consumed Events**:
- `OrderCreatedEvent` → Allocate inventory
- `OrderCancelledEvent` → Deallocate inventory
- `ItemPickedEvent` → Decrement allocated, create pick ledger entry
- `ItemPackedEvent` → Update status
- `ItemShippedEvent` → Finalize transaction
- `ProductCreatedEvent` → Initialize stock record

**Business Rules**:
- Events processed exactly once (idempotency keys)
- Failed events retried (max 3 attempts)
- Poison pill events moved to DLQ
- Ordering preserved per aggregate

**Key Metrics**:
- Event processing lag (target: <2 seconds)
- Processing error rate
- DLQ depth

**Related Services**:
- Order Management (order lifecycle events)
- Warehouse Operations (picking events)
- Product Catalog (product lifecycle events)

---

## L2: Performance & Scalability

### L2.1: Description
Ensure high performance, scalability, and reliability for inventory operations supporting high-volume fulfillment.

### L2.2: Business Value
- Support peak load periods (Black Friday, Cyber Monday)
- Minimize latency for real-time order processing
- Enable horizontal scaling for growth
- Provide consistent performance under load

### L2.3: L3 Capabilities

#### L3.6.1: Caching Strategy
**Description**: Multi-layer caching to optimize read performance for frequently accessed inventory data.

**Technical Implementation**:
- Redis for distributed cache
- Caffeine for in-memory L1 cache
- Cache-aside pattern with write-through updates
- Intelligent cache warming for popular SKUs

**Business Rules**:
- ATP cached for 30 seconds (configurable)
- Cache invalidated on inventory changes
- Popular SKUs always in cache (99th percentile access)
- Cache miss triggers synchronous load

**Key Metrics**:
- Cache hit rate (target: >90%)
- Cache latency (p95 < 5ms)
- Cache invalidation rate

**Related Services**: None (infrastructure)

---

#### L3.6.2: Database Optimization
**Description**: Optimize MongoDB queries and indexes for high-performance inventory operations.

**Technical Implementation**:
- Compound indexes on query patterns (SKU + location)
- Covered indexes for ATP queries
- Sharding on SKU for horizontal scaling
- Query profiling and optimization

**Business Rules**:
- All queries use indexes (no collection scans)
- Write operations optimized for throughput
- Read operations optimized for latency

**Key Metrics**:
- Query response time (p95 < 50ms)
- Index hit rate (target: 100%)
- Database CPU utilization

**Related Services**: None (infrastructure)

---

#### L3.6.3: Horizontal Scalability
**Description**: Support horizontal scaling to handle increased load and throughput.

**Technical Implementation**:
- Stateless service design
- MongoDB sharding by SKU
- Kafka consumer groups for parallel processing
- Load balancing across service instances

**Business Rules**:
- Auto-scaling based on CPU and request rate
- Graceful shutdown for deployments
- Circuit breakers for downstream dependencies

**Key Metrics**:
- Request throughput (requests/second)
- Instance count
- Auto-scaling events

**Related Services**: None (infrastructure)

---

## L2: Monitoring & Observability

### L2.1: Description
Comprehensive monitoring, alerting, and observability for operational excellence and proactive issue resolution.

### L2.2: Business Value
- Detect issues before they impact customers
- Support root cause analysis
- Enable data-driven optimization
- Provide business insights from operational data

### L2.3: L3 Capabilities

#### L3.7.1: Inventory Metrics Collection
**Description**: Collect and expose comprehensive metrics for inventory operations and business KPIs.

**Technical Implementation**:
- Prometheus metrics integration
- Custom business metrics (ATP, allocation rates, accuracy)
- Real-time dashboards in Grafana
- Metric-based alerting

**Key Metrics Exposed**:
- `inventory.stock.on_hand{sku}` - Current stock levels
- `inventory.atp{sku}` - Available to promise
- `inventory.allocation.rate` - Allocations per minute
- `inventory.allocation.success.rate` - Allocation success %
- `inventory.accuracy.rate` - Inventory accuracy from cycle counts
- `inventory.ledger.entries.total` - Total ledger entries
- `inventory.cache.hit.rate` - Cache effectiveness

**Business Rules**:
- Metrics collected in real-time
- Aggregations computed at multiple time windows
- Alerting on threshold breaches
- Historical metric retention (90 days)

**Related Services**: Infrastructure (Prometheus, Grafana)

---

#### L3.7.2: Distributed Tracing
**Description**: Trace inventory requests across service boundaries for performance analysis and debugging.

**Technical Implementation**:
- OpenTelemetry instrumentation
- Trace context propagation via headers
- Integration with Tempo for storage
- Trace correlation with logs and metrics

**Business Rules**:
- All requests traced with correlation IDs
- Span timing for each operation
- Linked traces across services
- Sampling strategy (100% for errors, 10% for success)

**Key Metrics**:
- End-to-end request latency by operation
- Service dependency performance
- Error rate by trace path

**Related Services**: All services (distributed tracing)

---

#### L3.7.3: Health Checks & Readiness Probes
**Description**: Provide comprehensive health checks for orchestration and load balancing.

**Technical Implementation**:
- Spring Boot Actuator health endpoints
- MongoDB connectivity check
- Kafka connectivity check
- Custom business health indicators (cache, outbox lag)

**Business Rules**:
- Health check responds in <100ms
- Liveness probe for restart decisions
- Readiness probe for traffic routing
- Detailed health status in response

**Health Checks**:
- `/actuator/health/liveness` - Is service alive?
- `/actuator/health/readiness` - Ready for traffic?
- `/actuator/health` - Detailed health status

**Related Services**: Infrastructure (Kubernetes, load balancers)

---

## Summary

The Inventory Service provides comprehensive inventory management capabilities through:

### Key Strengths
- **Accuracy**: Single source of truth with immutable audit trail
- **Scalability**: Horizontal scaling with caching and database optimization
- **Reliability**: Transactional outbox pattern for guaranteed event delivery
- **Visibility**: Real-time inventory positions across all locations
- **Compliance**: Complete audit trail for regulatory compliance

### Business Impact
- **Inventory Accuracy**: 99.5%+ accuracy rate
- **Order Fulfillment**: Real-time ATP for instant order validation
- **Audit Compliance**: 100% transaction traceability
- **Performance**: <50ms p95 latency for ATP queries
- **Scalability**: Supports 50,000+ transactions per hour

### Integration Points
- **Upstream**: Product Catalog (SKU validation), Warehouse Operations (receipts, cycle counts)
- **Downstream**: Order Management (allocations), Warehouse Operations (picking instructions)
- **Events**: Publishes inventory state changes, consumes order and warehouse events

### Domain Model Highlights
- **ProductStock Aggregate**: Manages quantities and allocations
- **StockLocation Aggregate**: Multi-location inventory management
- **InventoryLedgerEntry**: Immutable audit trail
- **PhysicalReservation Entity**: Location-specific reservations
- **Value Objects**: StockLevel, Location

### Technology Highlights
- Hexagonal architecture with DDD principles
- Transactional outbox pattern for reliable events
- CloudEvents for event standardization
- Multi-layer caching for performance
- Comprehensive observability stack
