# Inventory Service - Domain Architecture & Business Capabilities

## Service Overview

The Inventory Service serves as the single source of truth for all product stock levels across the fulfillment network. It manages inventory quantities, allocations, reservations, locations, and provides a comprehensive audit trail through an immutable ledger pattern.

**Architecture Pattern**: Hexagonal Architecture with Domain-Driven Design (DDD)
**Technology Stack**: Spring Boot 3.2, Spring Data MongoDB, Spring Kafka, CloudEvents
**Integration Pattern**: Event-Driven Architecture with Transactional Outbox Pattern

---

## Domain Model & Bounded Context

### Bounded Context: Inventory Management

The Inventory Management bounded context encompasses all aspects of tracking, allocating, and managing product stock across the fulfillment network.

#### Context Boundaries

**Responsibilities (What's IN)**:
- Track on-hand inventory quantities by SKU and location
- Manage inventory allocations and reservations
- Calculate Available-to-Promise (ATP)
- Maintain immutable audit trail of all inventory transactions
- Manage multi-location inventory
- Process inventory adjustments (receipts, cycle counts, damages)
- Publish inventory state change events

**External Dependencies (What's OUT)**:
- Product master data (Product Catalog context)
- Order demand and allocation requests (Order Management context)
- Physical picking and inventory movement (Warehouse Operations context)
- Inventory valuation and financial reporting (Finance context - external)

#### Ubiquitous Language

**Core Domain Terms**:

- **Quantity on Hand (QOH)**: Physical quantity of product in warehouse
- **Quantity Allocated**: Quantity reserved for specific orders but not yet picked
- **Available-to-Promise (ATP)**: Quantity available for new orders (QOH - Allocated - Safety Stock)
- **Safety Stock**: Minimum quantity maintained to prevent stockouts
- **Physical Reservation**: Location-specific inventory reservation for picking
- **Inventory Ledger**: Immutable record of all inventory transactions
- **Stock Location**: Physical location where inventory is stored
- **Allocation**: Soft reservation of inventory for an order
- **Deallocation**: Release of allocated inventory back to ATP
- **Inventory Adjustment**: Change to inventory quantity with reason code
- **Cycle Count**: Physical count of inventory for accuracy verification

---

## Subdomain Classification

### Core Domain: Inventory Tracking & Allocation

**Strategic Importance**: HIGH - Critical business capability

This is the heart of the inventory service and provides significant business value through:
- Preventing overselling through accurate ATP
- Enabling real-time inventory visibility
- Supporting multi-channel fulfillment
- Providing complete audit trail for compliance

**Subdomains**:

#### 1. **Inventory Allocation & Promising** (Core)
- **Complexity**: High - Complex state management and concurrency
- **Strategic Value**: High - Directly impacts revenue and customer satisfaction
- **Volatility**: Medium - Business rules evolve with business needs
- **Business Differentiation**: PRIMARY differentiator
- **Investment Priority**: High - Continuous refinement needed

#### 2. **Multi-Location Inventory Management** (Core)
- **Complexity**: High - Distributed inventory tracking
- **Strategic Value**: High - Enables distributed fulfillment
- **Volatility**: Medium - Changes with network expansion
- **Business Differentiation**: Competitive advantage
- **Investment Priority**: High - Supports growth strategy

#### 3. **Inventory Audit & Compliance** (Supporting)
- **Complexity**: Medium - Event sourcing and ledger management
- **Strategic Value**: High - Regulatory compliance and financial reporting
- **Volatility**: Low - Stable requirements
- **Business Differentiation**: Required capability
- **Investment Priority**: Medium - Maintain and enhance

#### 4. **Inventory Adjustments** (Supporting)
- **Complexity**: Low - CRUD with business logic
- **Strategic Value**: Medium - Operational necessity
- **Volatility**: Low - Stable processes
- **Business Differentiation**: Standard capability
- **Investment Priority**: Low - Maintain existing functionality

---

## Domain Model

### Aggregates

#### 1. ProductStock (Aggregate Root)

**Description**: Manages all stock information for a product (SKU) including quantities, allocations, and reservations.

```java
@AggregateRoot
public class ProductStock {
    private String sku; // Aggregate ID
    private StockLevel stockLevel;
    private SafetyStockLevel safetyStock;
    private List<Allocation> allocations;
    private int version; // Optimistic locking

    // Business methods
    public AllocationResult allocate(String orderId, int quantity, Duration ttl);
    public void deallocate(String allocationId);
    public int calculateAvailableToPromise();
    public void adjustStock(int quantityChange, AdjustmentReason reason);
    public boolean hasSufficientATP(int requestedQuantity);

    // Invariants
    private void ensureQuantityOnHandNotNegative();
    private void ensureAllocatedDoesNotExceedOnHand();
}
```

**Invariants**:
- Quantity on hand ≥ 0
- Quantity allocated ≤ quantity on hand
- ATP = QOH - Allocated - Safety Stock
- All changes create ledger entries

**Domain Events**:
- `StockLevelChangedEvent`
- `InventoryAllocatedEvent`
- `InventoryDeallocatedEvent`
- `LowStockAlertEvent`

---

#### 2. StockLocation (Aggregate Root)

**Description**: Manages inventory at a specific physical location within the warehouse, including physical reservations for picking.

```java
@AggregateRoot
public class StockLocation {
    private String locationId; // Composite: SKU + Location
    private String sku;
    private String warehouseId;
    private String zone;
    private String aisle;
    private String bin;
    private int quantityAtLocation;
    private List<PhysicalReservation> reservations;

    // Business methods
    public PhysicalReservation createReservation(
        String orderId,
        int quantity,
        LocalDateTime expiresAt
    );

    public void fulfillReservation(String reservationId, int quantityPicked);
    public void cancelReservation(String reservationId);
    public int calculateAvailableAtLocation();

    // Invariants
    private void ensureReservationsDoNotExceedQuantity();
    private void ensureLocationExists();
}
```

**Invariants**:
- Quantity at location ≥ 0
- Total reserved quantity ≤ quantity at location
- Location must exist in warehouse hierarchy

**Domain Events**:
- `PhysicalReservationCreatedEvent`
- `ReservationFulfilledEvent`
- `ReservationCancelledEvent`
- `StockTransferredEvent`

---

#### 3. InventoryLedgerEntry (Aggregate Root - Event Sourced)

**Description**: Immutable record of inventory transaction for complete audit trail.

```java
@AggregateRoot
public class InventoryLedgerEntry {
    private String entryId; // Aggregate ID
    private String sku;
    private TransactionType transactionType;
    private int quantityBefore;
    private int quantityAfter;
    private int quantityChange;
    private AdjustmentReason reasonCode;
    private LocalDateTime timestamp;
    private String userId;
    private String referenceId; // Order ID, Receipt ID, etc.
    private Map<String, String> metadata;

    // Immutable - no business methods that change state
    // Only factory method for creation

    public static InventoryLedgerEntry create(
        String sku,
        TransactionType type,
        int quantityBefore,
        int quantityAfter,
        AdjustmentReason reason,
        String userId,
        String referenceId
    );
}
```

**Invariants**:
- Ledger entries are immutable (never updated or deleted)
- Must have valid reason code
- Timestamp cannot be in future
- Quantity change = quantityAfter - quantityBefore

**Domain Events**:
- `LedgerEntryCreatedEvent`

---

### Entities

#### Allocation

**Description**: Represents allocation of inventory for a specific order.

```java
@Entity
public class Allocation {
    private String allocationId;
    private String orderId;
    private int quantityAllocated;
    private AllocationStatus status;
    private LocalDateTime allocatedAt;
    private LocalDateTime expiresAt;
    private Priority priority;

    public boolean isExpired();
    public void expire();
    public void fulfill();
}
```

---

#### PhysicalReservation

**Description**: Location-specific reservation for picking.

```java
@Entity
public class PhysicalReservation {
    private String reservationId;
    private String orderId;
    private String pickListId;
    private int quantityReserved;
    private int quantityPicked;
    private ReservationStatus status;
    private LocalDateTime reservedAt;
    private LocalDateTime expiresAt;

    public void recordPick(int quantity);
    public boolean isFullyPicked();
    public void cancel(String reason);
}
```

---

### Value Objects

#### StockLevel

```java
@ValueObject
public class StockLevel {
    private int quantityOnHand;
    private int quantityAllocated;
    private int quantityReserved; // Physical reservations

    public int calculateAvailable() {
        return quantityOnHand - quantityAllocated;
    }

    public StockLevel adjustQuantityOnHand(int adjustment) {
        return new StockLevel(
            quantityOnHand + adjustment,
            quantityAllocated,
            quantityReserved
        );
    }

    public StockLevel allocate(int quantity) {
        if (quantity > calculateAvailable()) {
            throw new InsufficientInventoryException();
        }
        return new StockLevel(
            quantityOnHand,
            quantityAllocated + quantity,
            quantityReserved
        );
    }
}
```

#### SafetyStockLevel

```java
@ValueObject
public class SafetyStockLevel {
    private int minimumLevel;
    private int reorderPoint;
    private int maximumLevel;

    public boolean isBelowSafety(int currentQuantity);
    public boolean shouldReorder(int currentQuantity);
}
```

#### Location

```java
@ValueObject
public class Location {
    private String warehouseId;
    private String zone;
    private String aisle;
    private String bin;

    public String toLocationCode(); // e.g., "WH01-Z01-A05-B12"
    public boolean isInZone(String zoneId);
}
```

---

## Domain Services

### AllocationService

**Responsibility**: Orchestrate inventory allocation across locations and handle concurrency.

```java
@DomainService
public class AllocationService {

    public AllocationResult allocateInventory(
        String sku,
        String orderId,
        int quantity,
        AllocationStrategy strategy
    );

    public void deallocateInventory(String sku, String allocationId);

    public void handleAllocationExpiration(String sku, String allocationId);

    public List<StockLocation> findLocationsWithAvailableStock(
        String sku,
        int requiredQuantity
    );
}
```

---

### InventoryReconciliationService

**Responsibility**: Reconcile physical inventory counts with system records.

```java
@DomainService
public class InventoryReconciliationService {

    public ReconciliationResult reconcile(
        String sku,
        String locationId,
        int physicalCount,
        String countedBy
    );

    public void processVariance(
        String sku,
        int systemQuantity,
        int physicalQuantity,
        VarianceApproval approval
    );

    public BigDecimal calculateInventoryAccuracy(
        LocalDate from,
        LocalDate to
    );
}
```

---

### ATP CalculationService

**Responsibility**: Calculate Available-to-Promise across locations and time horizons.

```java
@DomainService
public class ATPCalculationService {

    public int calculateCurrentATP(String sku);

    public int calculateLocationATP(String sku, String warehouseId);

    public Map<LocalDate, Integer> calculateFutureATP(
        String sku,
        int daysAhead,
        List<PlannedReceipt> plannedReceipts
    );

    public boolean canFulfill(String sku, int quantity, String warehouseId);
}
```

---

## Application Layer

### Ports (Interfaces)

#### Input Ports (Use Cases)

```java
// Commands
public interface AllocateInventoryCommand {
    AllocationResult execute(AllocateInventoryRequest request);
}

public interface DeallocateInventoryCommand {
    void execute(DeallocateInventoryRequest request);
}

public interface AdjustStockLevelCommand {
    void execute(StockAdjustmentRequest request);
}

public interface CreatePhysicalReservationCommand {
    PhysicalReservation execute(CreateReservationRequest request);
}

// Queries
public interface GetATPQuery {
    int execute(String sku);
}

public interface GetStockLevelQuery {
    StockLevel execute(String sku);
}

public interface GetInventoryLedgerQuery {
    List<InventoryLedgerEntry> execute(String sku, DateRange dateRange);
}
```

#### Output Ports (Dependencies)

```java
// Repository ports
public interface ProductStockRepository {
    Optional<ProductStock> findBySku(String sku);
    void save(ProductStock productStock);
    List<ProductStock> findBySkus(List<String> skus);
}

public interface StockLocationRepository {
    Optional<StockLocation> findBySkuAndLocation(String sku, String locationId);
    List<StockLocation> findBySku(String sku);
    void save(StockLocation stockLocation);
}

public interface InventoryLedgerRepository {
    void append(InventoryLedgerEntry entry);
    List<InventoryLedgerEntry> findBySku(String sku, Pageable pageable);
}

// External service ports
public interface ProductCatalogClient {
    boolean productExists(String sku);
    ProductInfo getProductInfo(String sku);
}

public interface EventPublisher {
    void publish(DomainEvent event);
}

// Outbox for reliable event publishing
public interface OutboxRepository {
    void save(OutboxEvent event);
    List<OutboxEvent> findUnpublished(int batchSize);
    void markAsPublished(String eventId);
}
```

---

## Infrastructure Layer

### Adapters

#### Inbound Adapters

**REST Controller**
```java
@RestController
@RequestMapping("/api/v1/inventory")
public class InventoryController {

    @GetMapping("/{sku}/atp")
    public ResponseEntity<ATPResponse> getATP(@PathVariable String sku);

    @PostMapping("/allocate")
    public ResponseEntity<AllocationResponse> allocate(
        @RequestBody AllocateRequest request
    );

    @PostMapping("/deallocate")
    public ResponseEntity<Void> deallocate(
        @RequestBody DeallocateRequest request
    );

    @PostMapping("/{sku}/adjust")
    public ResponseEntity<Void> adjustStock(
        @PathVariable String sku,
        @RequestBody StockAdjustmentRequest request
    );

    @GetMapping("/{sku}/ledger")
    public ResponseEntity<List<LedgerEntryResponse>> getLedger(
        @PathVariable String sku,
        @RequestParam(required = false) LocalDate from,
        @RequestParam(required = false) LocalDate to
    );
}
```

**Event Listener**
```java
@Component
public class OrderEventListener {

    @KafkaListener(topics = "fulfillment.order.v1.events")
    public void handleOrderValidated(FulfillmentOrderValidatedEvent event) {
        // Allocate inventory for validated order
    }

    @KafkaListener(topics = "fulfillment.order.v1.events")
    public void handleOrderCancelled(FulfillmentOrderCancelledEvent event) {
        // Deallocate inventory for cancelled order
    }
}

@Component
public class WarehouseEventListener {

    @KafkaListener(topics = "fulfillment.warehouse.v1.events")
    public void handleItemPicked(ItemPickedEvent event) {
        // Decrement inventory and allocation
    }
}
```

#### Outbound Adapters

**MongoDB Adapter**
```java
@Repository
public class MongoProductStockRepository implements ProductStockRepository {

    private final MongoTemplate mongoTemplate;

    @Override
    public Optional<ProductStock> findBySku(String sku) {
        return Optional.ofNullable(
            mongoTemplate.findById(sku, ProductStock.class)
        );
    }

    @Override
    public void save(ProductStock productStock) {
        mongoTemplate.save(productStock);
    }
}
```

**Transactional Outbox Adapter**
```java
@Component
public class OutboxEventPublisher implements EventPublisher {

    private final OutboxRepository outboxRepository;

    @Override
    @Transactional
    public void publish(DomainEvent event) {
        // Save event to outbox in same transaction as domain change
        OutboxEvent outboxEvent = new OutboxEvent(
            event.getId(),
            event.getType(),
            event.toJson(),
            OutboxStatus.PENDING
        );
        outboxRepository.save(outboxEvent);
    }
}

@Component
@Scheduled(fixedDelay = 1000) // Poll every second
public class OutboxProcessor {

    public void processOutbox() {
        List<OutboxEvent> pending = outboxRepository.findUnpublished(100);

        for (OutboxEvent event : pending) {
            try {
                kafkaTemplate.send(topicName, event.getPayload());
                outboxRepository.markAsPublished(event.getId());
            } catch (Exception e) {
                // Retry logic with exponential backoff
            }
        }
    }
}
```

**Cache Adapter**
```java
@Component
public class InventoryCacheService {

    private final RedisTemplate<String, Object> redisTemplate;

    public Optional<Integer> getCachedATP(String sku) {
        String key = "atp:" + sku;
        return Optional.ofNullable(
            (Integer) redisTemplate.opsForValue().get(key)
        );
    }

    public void cacheATP(String sku, int atp, Duration ttl) {
        String key = "atp:" + sku;
        redisTemplate.opsForValue().set(key, atp, ttl);
    }

    public void invalidateATP(String sku) {
        String key = "atp:" + sku;
        redisTemplate.delete(key);
    }
}
```

---

## Business Capabilities

### L1: Inventory Management

Single source of truth for all product stock levels across the fulfillment network.

---

### L2: Stock Level Management

#### L3.1: Quantity on Hand Tracking
- Track physical inventory quantities
- Support multi-location tracking
- Handle decimal quantities (catch-weight items)
- Real-time accuracy

#### L3.2: Quantity Allocated Tracking
- Track allocated (soft reserved) inventory
- Manage allocation expiration
- Support priority-based allocation
- Handle partial allocations

#### L3.3: Available-to-Promise (ATP) Calculation
- Real-time ATP calculation
- Multi-location ATP aggregation
- Future ATP with planned receipts
- Safety stock consideration

#### L3.4: Safety Stock Management
- Configure min/max levels per SKU
- Alert on safety stock breaches
- Dynamic safety stock (future)
- Service level optimization

#### L3.5: Stock Level Adjustments
- Receipt processing
- Cycle count adjustments
- Damage/shrinkage recording
- Return processing
- Transfer adjustments

---

### L2: Inventory Allocation & Reservation

#### L3.6: Inventory Allocation
- Allocate inventory for orders
- Priority-based allocation
- Allocation expiration management
- Multi-location allocation

#### L3.7: Inventory Deallocation
- Release allocated inventory
- Cancellation handling
- Partial deallocation support
- Automatic expiration processing

#### L3.8: Physical Reservation Management
- Location-specific reservations
- Reservation for picking
- Multi-location reservations
- Reservation tracking and fulfillment

#### L3.9: Allocation Expiration Management
- Scheduled expiration checks
- Configurable TTL per allocation type
- Automatic deallocation
- Expiration notifications

---

### L2: Multi-Location Inventory Management

#### L3.10: Location-Based Stock Tracking
- Track inventory by physical location
- Hierarchical location structure
- Location-level quantities
- Warehouse-level aggregation

#### L3.11: Inter-Location Stock Transfers
- Transfer inventory between locations
- Two-phase transfer (in-transit tracking)
- Transfer confirmation
- Transfer audit trail

#### L3.12: Location-Based ATP Calculation
- ATP by warehouse
- ATP by zone/aisle/bin
- Multi-location sourcing
- Location priority rules

---

### L2: Inventory Audit & Compliance

#### L3.13: Immutable Inventory Ledger
- Append-only transaction log
- Complete audit trail
- Event sourcing pattern
- State reconstruction capability

#### L3.14: Transaction History Query
- Query historical transactions
- Filter by date, type, user
- Pagination support
- Audit report generation

#### L3.15: Inventory Reconciliation
- Cycle count processing
- Variance calculation
- Approval workflows
- Accuracy reporting

#### L3.16: Audit Trail Reporting
- Compliance reports
- Financial inventory valuation
- Transaction summaries
- Export capabilities

---

### L2: Event-Driven Integration

#### L3.17: Transactional Outbox Pattern
- Guaranteed event delivery
- Exactly-once processing
- Ordered event publishing
- Retry mechanism

#### L3.18: Inventory Domain Event Publishing
- Stock level changes
- Allocation/deallocation events
- Low stock alerts
- Transfer events

#### L3.19: Event Consumption
- Order events (allocate/deallocate)
- Warehouse events (picks, receipts)
- Product events (initialization)
- Idempotent processing

---

## Integration Patterns

### Context Mapping

#### Product Catalog (Upstream - Customer/Supplier)
- **Type**: Conformist relationship
- **Integration**: Event-driven + REST
- **Dependency**: Product SKU validation
- **Protection**: Local product cache

#### Order Management (Upstream - Published Language)
- **Type**: Published Language (CloudEvents)
- **Integration**: Event-driven via Kafka
- **Contract**: AsyncAPI specification
- **Collaboration**: Allocation requests/confirmations

#### Warehouse Operations (Bi-directional - Partnership)
- **Type**: Partnership
- **Integration**: Event-driven (both directions)
- **Collaboration**: Inventory transactions
- **Contracts**: Joint event schema design

---

## Event Schemas

### InventoryAllocatedEvent

```json
{
  "specversion": "1.0",
  "type": "com.paklog.inventory.allocated",
  "source": "inventory-service",
  "id": "alloc-12345",
  "time": "2025-10-18T10:30:00Z",
  "datacontenttype": "application/json",
  "data": {
    "allocationId": "alloc-12345",
    "sku": "PROD-123",
    "orderId": "ORD-67890",
    "quantityAllocated": 5,
    "allocatedAt": "2025-10-18T10:30:00Z",
    "expiresAt": "2025-10-19T10:30:00Z",
    "warehouseId": "WH01"
  }
}
```

### StockLevelChangedEvent

```json
{
  "specversion": "1.0",
  "type": "com.paklog.inventory.stock.changed",
  "source": "inventory-service",
  "id": "stock-change-456",
  "time": "2025-10-18T10:30:00Z",
  "datacontenttype": "application/json",
  "data": {
    "sku": "PROD-123",
    "quantityBefore": 100,
    "quantityAfter": 95,
    "quantityChange": -5,
    "transactionType": "PICK",
    "reasonCode": "ORDER_FULFILLMENT",
    "referenceId": "ORD-67890",
    "warehouseId": "WH01",
    "userId": "picker-001"
  }
}
```

---

## Quality Attributes

### Consistency
- **Strong Consistency**: Optimistic locking for concurrent updates
- **Eventual Consistency**: Event-driven propagation to other services
- **ACID**: Transaction boundaries around aggregate changes

### Performance
- **ATP Queries**: <50ms p95 latency
- **Cache Hit Rate**: >90% for frequently accessed SKUs
- **Throughput**: 50,000+ transactions per hour

### Reliability
- **Availability**: 99.95% uptime SLA
- **Data Durability**: MongoDB replication
- **Event Delivery**: Guaranteed via outbox pattern
- **Idempotency**: Duplicate event handling

---

## Summary

The Inventory Service is a critical bounded context providing:

- **Clear Domain Model**: Rich aggregates with business invariants
- **Event Sourcing**: Immutable audit trail via ledger
- **Reliable Integration**: Transactional outbox for guaranteed event delivery
- **Multi-Location Support**: Distributed inventory tracking
- **High Performance**: Caching and optimized queries
- **Compliance**: Complete audit trail for financial and regulatory requirements

Business Impact: 99.5%+ accuracy, real-time ATP, 100% traceability, <50ms query latency.
