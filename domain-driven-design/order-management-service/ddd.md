# Order Management Service - Domain Architecture & Business Capabilities

## Service Overview

The Order Management Service orchestrates the fulfillment order lifecycle from order receipt through shipment. It serves as the central coordinator for fulfillment operations, managing order validation, status tracking, and event-driven orchestration across the fulfillment network.

**Architecture Pattern**: Hexagonal Architecture (Ports & Adapters)
**Technology Stack**: Spring Boot, Spring Data MongoDB, Spring Kafka, CloudEvents
**Integration Pattern**: Event-Driven Choreography

---

## Domain Model & Bounded Context

### Bounded Context: Fulfillment Order Management

The Fulfillment Order Management bounded context focuses on the orchestration and lifecycle management of orders within the fulfillment network.

#### Context Boundaries

**Responsibilities (What's IN)**:
- Receive and validate fulfillment orders
- Manage order lifecycle state transitions
- Coordinate order fulfillment across services
- Track order status and progress
- Handle order cancellations and modifications
- Maintain order history and audit trail
- Calculate and track service level agreements (SLAs)
- Publish order lifecycle events

**External Dependencies (What's OUT)**:
- Customer order placement (E-commerce/OMS - upstream)
- Product validation (Product Catalog context)
- Inventory availability checking (Inventory context)
- Physical picking and packing (Warehouse Operations context)
- Shipment creation and tracking (Shipment & Transportation context)
- Customer notifications (Notification service - external)
- Payment processing (Payment service - external)

#### Ubiquitous Language

**Core Domain Terms**:

- **Fulfillment Order**: An order received for fulfillment in the warehouse
- **Order Item**: Individual line item within an order (SKU + quantity)
- **Order Validation**: Process of verifying order can be fulfilled
- **Order Release**: Making order available for warehouse fulfillment
- **Order Status**: Current state in the fulfillment lifecycle
- **Service Level Agreement (SLA)**: Expected delivery timeframe
- **Order Priority**: Urgency level (STANDARD, RUSH, EXPRESS, CRITICAL)
- **Shipping Address**: Delivery destination for the order
- **Order Cancellation**: Stopping fulfillment before shipment
- **Order Invalidation**: Marking order as unfulfillable due to validation failures
- **Perfect Order**: Order delivered on-time, complete, and damage-free

---

## Subdomain Classification

### Core Domain: Order Fulfillment Orchestration

**Strategic Importance**: HIGH - Central coordination point

This is the heart of the order management service and provides significant business value through:
- Orchestrating complex fulfillment workflows
- Ensuring order accuracy and timely delivery
- Providing visibility across the fulfillment network
- Enabling customer satisfaction through reliable fulfillment

**Subdomains**:

#### 1. **Order Lifecycle Management** (Core)
- **Complexity**: High - Complex state machine and orchestration
- **Strategic Value**: High - Core fulfillment capability
- **Volatility**: Medium - Business processes evolve
- **Business Differentiation**: PRIMARY differentiator
- **Investment Priority**: High - Continuous improvement needed

#### 2. **Order Validation & Promising** (Core)
- **Complexity**: High - Multi-service coordination
- **Strategic Value**: High - Prevents order failures
- **Volatility**: Medium - Rules change with business needs
- **Business Differentiation**: Competitive advantage
- **Investment Priority**: High - Critical for customer satisfaction

#### 3. **Order Visibility & Tracking** (Supporting)
- **Complexity**: Medium - Event aggregation and querying
- **Strategic Value**: High - Customer service enabler
- **Volatility**: Low - Stable requirements
- **Business Differentiation**: Standard capability
- **Investment Priority**: Medium - Maintain and enhance

#### 4. **Order Modification & Cancellation** (Supporting)
- **Complexity**: Medium - Workflow coordination
- **Strategic Value**: Medium - Customer flexibility
- **Volatility**: Low - Stable processes
- **Business Differentiation**: Standard capability
- **Investment Priority**: Low - Maintain existing functionality

---

## Domain Model

### Aggregates

#### 1. FulfillmentOrder (Aggregate Root)

**Description**: The central aggregate representing an order being fulfilled, managing its complete lifecycle from receipt to shipment.

```java
@AggregateRoot
public class FulfillmentOrder {
    private String orderId; // Aggregate ID
    private String customerId;
    private Address shippingAddress;
    private List<OrderItem> items;
    private OrderStatus status;
    private Priority priority;
    private ServiceLevel serviceLevel;
    private SLADeadline slaDeadline;
    private OrderTimestamps timestamps;
    private List<OrderStatusTransition> statusHistory;
    private int version; // Optimistic locking

    // Business methods
    public void validate(ValidationRules rules);
    public void invalidate(List<ValidationFailure> failures);
    public void release();
    public void cancel(CancellationReason reason);
    public void markPickingStarted();
    public void markPickingCompleted();
    public void markPackingCompleted();
    public void markShipped(TrackingInfo trackingInfo);

    // Invariants
    private void ensureNotAlreadyShipped();
    private void ensureCanBeCancelled();
    private void ensureValidStatusTransition(OrderStatus newStatus);
}
```

**Order Status State Machine**:
```
NEW → RECEIVED → VALIDATED → RELEASED → IN_PROGRESS → PACKING → SHIPPED
         ↓            ↓
    INVALIDATED  CANCELLED
```

**Invariants**:
- Order must have at least one order item
- Shipping address is required and valid
- Status transitions follow defined state machine
- Cannot cancel after SHIPPED status
- SLA deadline must be in future when order created

**Domain Events**:
- `FulfillmentOrderReceivedEvent`
- `FulfillmentOrderValidatedEvent`
- `FulfillmentOrderInvalidatedEvent`
- `FulfillmentOrderReleasedEvent`
- `FulfillmentOrderPickingCompletedEvent`
- `FulfillmentOrderPackingCompletedEvent`
- `FulfillmentOrderShippedEvent`
- `FulfillmentOrderCancelledEvent`

---

### Entities

#### OrderItem

**Description**: Represents a line item within an order.

```java
@Entity
public class OrderItem {
    private String orderItemId;
    private String sku;
    private int quantityOrdered;
    private int quantityFulfilled;
    private BigDecimal unitPrice;
    private ItemStatus status;

    public void markPicked(int quantity);
    public void markShipped();
    public boolean isFullyFulfilled();
    public boolean isShortPicked();
}

enum ItemStatus {
    PENDING,
    ALLOCATED,
    PICKED,
    PACKED,
    SHIPPED,
    CANCELLED
}
```

---

#### OrderStatusTransition

**Description**: Records each status transition for audit and analysis.

```java
@Entity
public class OrderStatusTransition {
    private OrderStatus fromStatus;
    private OrderStatus toStatus;
    private LocalDateTime transitionedAt;
    private String transitionedBy; // User or System
    private String reason;

    public Duration getDurationInStatus() {
        // Calculate time spent in previous status
    }
}
```

---

### Value Objects

#### Address

```java
@ValueObject
public class Address {
    private String recipientName;
    private String addressLine1;
    private String addressLine2;
    private String city;
    private String state;
    private String postalCode;
    private String country;
    private AddressType type; // RESIDENTIAL, COMMERCIAL

    public boolean isValid();
    public boolean isInternational();
    public String toFormattedString();
}
```

#### SLADeadline

```java
@ValueObject
public class SLADeadline {
    private LocalDateTime orderReceivedAt;
    private LocalDateTime expectedShipmentBy;
    private LocalDateTime expectedDeliveryBy;
    private Priority priority;

    public boolean isBreached();
    public boolean isAtRisk(double thresholdPercentage);
    public Duration remainingTime();
    public double percentageElapsed();
}
```

#### OrderTimestamps

```java
@ValueObject
public class OrderTimestamps {
    private LocalDateTime createdAt;
    private LocalDateTime receivedAt;
    private LocalDateTime validatedAt;
    private LocalDateTime releasedAt;
    private LocalDateTime pickingStartedAt;
    private LocalDateTime pickingCompletedAt;
    private LocalDateTime packingCompletedAt;
    private LocalDateTime shippedAt;

    public Duration getProcessingTime();
    public Duration getPickingDuration();
    public Duration getPackingDuration();
}
```

#### Priority

```java
@ValueObject
public enum Priority {
    STANDARD(3, Duration.ofDays(3)),
    RUSH(2, Duration.ofDays(2)),
    EXPRESS(1, Duration.ofHours(24)),
    CRITICAL(0, Duration.ofHours(4));

    private final int level;
    private final Duration sla;

    // Business methods
    public boolean hasHigherPriorityThan(Priority other);
    public Duration getAllocationTTL();
}
```

---

## Domain Services

### OrderValidationService

**Responsibility**: Orchestrate multi-step order validation process.

```java
@DomainService
public class OrderValidationService {

    public ValidationResult validate(FulfillmentOrder order);

    private ValidationResult validateProducts(List<OrderItem> items);
    private ValidationResult validateInventoryAvailability(List<OrderItem> items);
    private ValidationResult validateAddress(Address address);
    private ValidationResult validateBusinessRules(FulfillmentOrder order);
}
```

---

### OrderOrchestrationService

**Responsibility**: Coordinate order processing across services.

```java
@DomainService
public class OrderOrchestrationService {

    public void processNewOrder(FulfillmentOrder order);
    public void handleValidationResult(String orderId, ValidationResult result);
    public void handleInventoryAllocated(String orderId, AllocationResult result);
    public void handlePickingCompleted(String orderId, PickingResult result);
    public void handleShipmentCreated(String orderId, ShipmentInfo shipment);
}
```

---

### SLATrackingService

**Responsibility**: Monitor order progress against SLAs.

```java
@DomainService
public class SLATrackingService {

    public SLAStatus calculateSLAStatus(FulfillmentOrder order);
    public List<FulfillmentOrder> findAtRiskOrders(double thresholdPercentage);
    public List<FulfillmentOrder> findBreachedOrders();
    public SLAMetrics calculateSLAMetrics(LocalDate from, LocalDate to);
}
```

---

## Application Layer

### Ports (Interfaces)

#### Input Ports (Use Cases)

```java
// Commands
public interface CreateFulfillmentOrderCommand {
    FulfillmentOrder execute(CreateOrderRequest request);
}

public interface CancelFulfillmentOrderCommand {
    void execute(String orderId, CancellationReason reason);
}

public interface ReleaseOrderCommand {
    void execute(String orderId);
}

// Queries
public interface GetOrderStatusQuery {
    OrderStatus execute(String orderId);
}

public interface GetOrderDetailsQuery {
    FulfillmentOrder execute(String orderId);
}

public interface GetOrderHistoryQuery {
    List<OrderStatusTransition> execute(String orderId);
}

public interface ListOrdersQuery {
    List<FulfillmentOrder> execute(OrderSearchCriteria criteria);
}
```

#### Output Ports (Dependencies)

```java
// Repository ports
public interface FulfillmentOrderRepository {
    Optional<FulfillmentOrder> findById(String orderId);
    void save(FulfillmentOrder order);
    List<FulfillmentOrder> findByStatus(OrderStatus status);
    List<FulfillmentOrder> findByCustomerId(String customerId);
}

// External service ports
public interface ProductCatalogClient {
    boolean allProductsExist(List<String> skus);
    List<ProductInfo> getProducts(List<String> skus);
}

public interface InventoryClient {
    ATPCheckResult checkAvailability(List<OrderItem> items);
}

public interface EventPublisher {
    void publish(DomainEvent event);
}
```

---

## Infrastructure Layer

### Adapters

#### Inbound Adapters

**REST Controller**
```java
@RestController
@RequestMapping("/api/v1/fulfillment_orders")
public class FulfillmentOrderController {

    @PostMapping
    public ResponseEntity<OrderResponse> createOrder(
        @RequestBody CreateOrderRequest request
    );

    @GetMapping("/{orderId}")
    public ResponseEntity<OrderResponse> getOrder(
        @PathVariable String orderId
    );

    @PostMapping("/{orderId}/cancel")
    public ResponseEntity<Void> cancelOrder(
        @PathVariable String orderId,
        @RequestBody CancellationRequest request
    );

    @GetMapping
    public ResponseEntity<List<OrderResponse>> listOrders(
        @RequestParam(required = false) String customerId,
        @RequestParam(required = false) OrderStatus status,
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "20") int size
    );

    @GetMapping("/{orderId}/history")
    public ResponseEntity<List<StatusTransitionResponse>> getHistory(
        @PathVariable String orderId
    );
}
```

**Event Listener - Inventory Events**
```java
@Component
public class InventoryEventListener {

    @KafkaListener(topics = "fulfillment.inventory.v1.events")
    public void handleInventoryAllocated(InventoryAllocatedEvent event) {
        // Update order status, potentially release for fulfillment
    }

    @KafkaListener(topics = "fulfillment.inventory.v1.events")
    public void handleAllocationFailed(AllocationFailedEvent event) {
        // Invalidate order due to insufficient inventory
    }
}
```

**Event Listener - Warehouse Events**
```java
@Component
public class WarehouseEventListener {

    @KafkaListener(topics = "fulfillment.warehouse.v1.events")
    public void handlePickingCompleted(PickingCompletedEvent event) {
        // Update order status to packing
    }

    @KafkaListener(topics = "fulfillment.warehouse.v1.events")
    public void handlePackingCompleted(PackingCompletedEvent event) {
        // Update order status to ready for shipment
    }
}
```

**Event Listener - Shipment Events**
```java
@Component
public class ShipmentEventListener {

    @KafkaListener(topics = "fulfillment.shipment.v1.events")
    public void handleShipmentCreated(ShipmentCreatedEvent event) {
        // Update order with tracking information
    }

    @KafkaListener(topics = "fulfillment.shipment.v1.events")
    public void handleShipmentDelivered(ShipmentDeliveredEvent event) {
        // Mark order as delivered
    }
}
```

#### Outbound Adapters

**MongoDB Adapter**
```java
@Repository
public class MongoFulfillmentOrderRepository implements FulfillmentOrderRepository {

    private final MongoTemplate mongoTemplate;

    @Override
    public Optional<FulfillmentOrder> findById(String orderId) {
        return Optional.ofNullable(
            mongoTemplate.findById(orderId, FulfillmentOrder.class)
        );
    }

    @Override
    public void save(FulfillmentOrder order) {
        mongoTemplate.save(order);
    }

    @Override
    public List<FulfillmentOrder> findByStatus(OrderStatus status) {
        Query query = new Query(Criteria.where("status").is(status));
        return mongoTemplate.find(query, FulfillmentOrder.class);
    }
}
```

**Kafka Event Publisher**
```java
@Component
public class KafkaEventPublisher implements EventPublisher {

    private final KafkaTemplate<String, CloudEvent> kafkaTemplate;
    private static final String TOPIC = "fulfillment.order.v1.events";

    @Override
    public void publish(DomainEvent event) {
        CloudEvent cloudEvent = CloudEventBuilder.v1()
            .withId(event.getId())
            .withType(event.getType())
            .withSource(URI.create("order-management-service"))
            .withData(event.toJson().getBytes())
            .build();

        kafkaTemplate.send(TOPIC, cloudEvent);
    }
}
```

---

## Business Capabilities

### L1: Order Fulfillment Orchestration

Manage the complete lifecycle of fulfillment orders from initial receipt through final shipment, coordinating with inventory, warehouse, and shipment services.

---

### L2: Order Lifecycle Management

#### L3.1: Order Creation & Receipt
- Receive fulfillment orders from upstream systems
- Validate order structure and required fields
- Assign unique order ID
- Publish `FulfillmentOrderReceivedEvent`

#### L3.2: Order Validation
- Validate all SKUs exist in product catalog
- Check inventory availability (ATP)
- Validate shipping address
- Verify hazmat shipping restrictions
- Apply business rules validation

#### L3.3: Order Invalidation Handling
- Capture validation failure reasons
- Transition to INVALIDATED status
- Notify upstream systems
- No inventory allocation created

#### L3.4: Order Release for Fulfillment
- Release validated orders for picking
- Trigger inventory allocation
- Publish release event for warehouse
- Support priority-based release

#### L3.5: Order Status Tracking
- Track order through all lifecycle stages
- Maintain status history
- Calculate time in each status
- Real-time status updates

#### L3.6: Order Completion
- Mark order as shipped
- Capture tracking information
- Final status transition
- Customer notification trigger

---

### L2: Order Modification & Cancellation

#### L3.7: Order Cancellation
- Cancel orders before shipment
- Release allocated inventory
- Cancel warehouse work
- Support partial cancellation (line items)
- Trigger refund process

#### L3.8: Order Modification (Future)
- Address changes pre-shipment
- Add/remove items (early stages)
- Quantity adjustments
- Re-validation after modification

---

### L2: Order Prioritization & SLA Management

#### L3.9: Order Priority Classification
- Support multiple priority levels
- Automatic classification by service level
- Manual priority override
- Priority-based allocation timeouts

#### L3.10: SLA Tracking & Monitoring
- Calculate SLA deadlines at receipt
- Real-time progress monitoring
- At-risk order identification
- SLA breach detection and alerting

#### L3.11: SLA Compliance Reporting
- SLA compliance percentage
- Breach reason analysis
- Performance by priority level
- Trend analysis

---

### L2: Order Visibility & Tracking

#### L3.12: Order Status Query
- Real-time order status lookup
- Multi-criteria search (customer, status, date)
- Pagination support
- Response includes all order details

#### L3.13: Order Event History
- Complete status transition history
- User and system attribution
- Timestamps for all transitions
- Duration in each status

#### L3.14: Bulk Order Reporting
- Aggregated order statistics
- Date range queries
- Export capabilities
- Operational dashboards

---

### L2: Event-Driven Orchestration

#### L3.15: Order Event Publishing
- Publish all lifecycle events
- CloudEvents format
- Guaranteed delivery
- Event versioning

#### L3.16: Inventory Event Consumption
- Process allocation confirmations
- Handle allocation failures
- Track inventory transactions
- Idempotent processing

#### L3.17: Warehouse Event Consumption
- Track picking progress
- Track packing completion
- Handle quality check results
- Update order status

#### L3.18: Shipment Event Consumption
- Capture shipment creation
- Track delivery status
- Update customer with tracking
- Handle delivery exceptions

---

## Integration Patterns

### Context Mapping

#### E-commerce/OMS (Upstream - Open Host Service)
- **Type**: Open Host Service
- **Integration**: REST API or Event-driven
- **Contract**: Order submission API
- **Protection**: Input validation and sanitization

#### Product Catalog (Upstream - Customer/Supplier)
- **Type**: Customer/Supplier
- **Integration**: Synchronous REST API
- **Dependency**: Product existence validation
- **Protection**: Circuit breaker, cache

#### Inventory (Partner - Partnership)
- **Type**: Partnership
- **Integration**: Event-driven (bi-directional)
- **Collaboration**: Allocation requests/responses
- **Contract**: Joint event schema definition

#### Warehouse Operations (Downstream - Customer/Supplier)
- **Type**: Customer/Supplier
- **Integration**: Event-driven
- **Contract**: Order management publishes, warehouse consumes
- **Evolution**: Event versioning

#### Shipment & Transportation (Downstream - Customer/Supplier)
- **Type**: Customer/Supplier
- **Integration**: Event-driven
- **Contract**: Shipment requests and tracking updates
- **Collaboration**: Shared understanding of shipment data

---

## Event Schemas

### FulfillmentOrderReceivedEvent

```json
{
  "specversion": "1.0",
  "type": "com.paklog.order.received",
  "source": "order-management-service",
  "id": "evt-order-12345",
  "time": "2025-10-18T10:30:00Z",
  "datacontenttype": "application/json",
  "data": {
    "orderId": "ORD-67890",
    "customerId": "CUST-123",
    "items": [
      {"sku": "PROD-001", "quantity": 2, "unitPrice": 29.99},
      {"sku": "PROD-002", "quantity": 1, "unitPrice": 49.99}
    ],
    "shippingAddress": {
      "recipientName": "John Doe",
      "addressLine1": "123 Main St",
      "city": "San Francisco",
      "state": "CA",
      "postalCode": "94105",
      "country": "US"
    },
    "priority": "STANDARD",
    "receivedAt": "2025-10-18T10:30:00Z"
  }
}
```

### FulfillmentOrderValidatedEvent

```json
{
  "specversion": "1.0",
  "type": "com.paklog.order.validated",
  "source": "order-management-service",
  "id": "evt-order-valid-123",
  "time": "2025-10-18T10:30:30Z",
  "datacontenttype": "application/json",
  "data": {
    "orderId": "ORD-67890",
    "customerId": "CUST-123",
    "items": [
      {"sku": "PROD-001", "quantity": 2},
      {"sku": "PROD-002", "quantity": 1}
    ],
    "priority": "STANDARD",
    "warehouseId": "WH01",
    "validatedAt": "2025-10-18T10:30:30Z",
    "slaDeadline": "2025-10-21T17:00:00Z"
  }
}
```

### FulfillmentOrderCancelledEvent

```json
{
  "specversion": "1.0",
  "type": "com.paklog.order.cancelled",
  "source": "order-management-service",
  "id": "evt-order-cancel-456",
  "time": "2025-10-18T11:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "orderId": "ORD-67890",
    "customerId": "CUST-123",
    "cancelledBy": "CUSTOMER",
    "cancellationReason": "CUSTOMER_REQUEST",
    "previousStatus": "VALIDATED",
    "cancelledAt": "2025-10-18T11:00:00Z"
  }
}
```

---

## Quality Attributes

### Reliability
- **Availability**: 99.95% uptime SLA
- **Idempotency**: Duplicate order detection
- **Event Delivery**: At-least-once delivery via Kafka
- **Retry Logic**: Exponential backoff for transient failures

### Performance
- **Order Creation**: <500ms p95 latency
- **Order Query**: <100ms p95 latency
- **Throughput**: 10,000+ orders per hour
- **Event Processing Lag**: <2 seconds

### Scalability
- **Horizontal Scaling**: Stateless service design
- **Event Partitioning**: Kafka partitions by order ID
- **Database**: MongoDB sharding support
- **Caching**: Redis for frequently accessed orders

---

## Summary

The Order Management Service is the central orchestrator of the fulfillment network:

- **Clear Domain Model**: Rich aggregate with lifecycle state machine
- **Event-Driven Choreography**: Loosely coupled service coordination
- **Partnership Patterns**: Collaborative integration with Inventory and Warehouse
- **SLA Management**: Proactive monitoring and alerting
- **High Visibility**: Complete order history and real-time status

Business Impact: 10,000+ orders/hour, >95% SLA compliance, >99% perfect order rate, 4-6 hour average cycle time.
