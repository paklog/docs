# Order Management Service - Business Capabilities

**Service Overview**: The Order Management Service orchestrates the fulfillment order lifecycle from order receipt through shipment. It serves as the central coordinator for fulfillment operations, managing order validation, status tracking, and event-driven orchestration across the fulfillment network.

**Architecture**: Hexagonal Architecture (Ports & Adapters)
**Technology Stack**: Spring Boot, Spring Data MongoDB, Spring Kafka, CloudEvents
**Domain Model**: Aggregate-based design with FulfillmentOrder as the root aggregate

---

## L1: Order Fulfillment Orchestration

### L1.1: Description
Manage the complete lifecycle of fulfillment orders from initial receipt through final shipment, coordinating with inventory, warehouse, and shipment services to ensure successful order completion.

### L1.2: Strategic Value
- **Customer Satisfaction**: Ensure timely and accurate order fulfillment
- **Operational Efficiency**: Automate order processing and reduce manual intervention
- **Visibility**: Provide real-time order status across all stakeholders
- **Reliability**: Guarantee order processing with event-driven choreography
- **Scalability**: Support high-volume order processing during peak periods

---

## L2: Order Lifecycle Management

### L2.1: Description
Manage the state transitions of fulfillment orders through their complete lifecycle, from creation to shipment completion.

### L2.2: Business Value
- Standardized order processing workflow
- Clear visibility into order status
- Support for exception handling and cancellations
- Audit trail of all order state changes

### L2.3: Order Lifecycle States

**State Flow**: NEW → RECEIVED → VALIDATED → (PICKING → PACKING → SHIPPED) | INVALIDATED | CANCELLED

### L2.4: L3 Capabilities

#### L3.1.1: Order Creation & Receipt
**Description**: Receive and register new fulfillment orders from upstream order management or e-commerce systems.

**Technical Implementation**:
- RESTful API endpoint for order submission
- `FulfillmentOrder` aggregate creation
- Initial state: NEW
- Kafka event publication: `FulfillmentOrderReceivedEvent`
- Idempotent processing (duplicate detection via order ID)

**Business Rules**:
- Order must have unique order ID
- Must contain at least one order item
- Shipping address is required
- Customer information is required
- Order date/time captured at receipt

**Domain Model**:
```java
class FulfillmentOrder {
  private String orderId;
  private String customerId;
  private Address shippingAddress;
  private List<OrderItem> items;
  private OrderStatus status; // NEW, RECEIVED, VALIDATED, etc.
  private LocalDateTime createdAt;
  private LocalDateTime updatedAt;
  private Priority priority; // STANDARD, RUSH, EXPRESS
}

class OrderItem {
  private String sku;
  private int quantity;
  private BigDecimal unitPrice;
}
```

**Key Metrics**:
- Orders received per hour
- Average order size (items per order)
- Order receipt processing time

**API Endpoints**:
- `POST /api/v1/fulfillment_orders` - Create fulfillment order

**Domain Events**:
- `FulfillmentOrderReceivedEvent` - Published when order enters system

**Related Services**: E-commerce platform, OMS (upstream order source)

---

#### L3.1.2: Order Validation
**Description**: Validate that orders can be fulfilled by checking inventory availability, address validity, and business rules.

**Technical Implementation**:
- Automatic validation triggered by order receipt
- Inventory availability check via Inventory Service API
- Product validation via Product Catalog
- Address validation
- Business rule validation (hazmat restrictions, shipping rules)

**Business Rules**:
- All SKUs must exist in product catalog
- Sufficient inventory must be available (ATP check)
- Shipping address must be valid and serviceable
- Items must be compatible (no conflicting restrictions)
- Order value must be within configured limits

**Validation Checks**:
1. **Product Validation**: All SKUs exist in catalog
2. **Inventory Validation**: ATP >= ordered quantity for all items
3. **Address Validation**: Valid, deliverable address
4. **Hazmat Validation**: Hazmat items meet shipping requirements
5. **Business Rules**: Custom validation rules (geographic restrictions, etc.)

**Key Metrics**:
- Validation success rate (target: >95%)
- Validation processing time (target: <2 seconds)
- Validation failure reasons (breakdown)

**Domain Events**:
- `FulfillmentOrderValidatedEvent` - Order passed validation
- `FulfillmentOrderInvalidatedEvent` - Order failed validation

**Related Services**:
- Inventory Service (ATP check)
- Product Catalog (SKU validation)

---

#### L3.1.3: Order Invalidation Handling
**Description**: Handle orders that cannot be fulfilled due to validation failures.

**Technical Implementation**:
- State transition to INVALIDATED
- Capture validation failure reasons
- Notification to upstream systems
- Event publication for downstream consumers

**Business Rules**:
- Invalidated orders do not proceed to fulfillment
- Inventory allocations are not created
- Detailed error messages captured
- Notification sent to customer service

**Invalidation Reasons**:
- `INSUFFICIENT_INVENTORY` - One or more items out of stock
- `INVALID_SKU` - SKU not found in product catalog
- `INVALID_ADDRESS` - Undeliverable shipping address
- `HAZMAT_RESTRICTION` - Hazmat shipping restriction
- `GEOGRAPHIC_RESTRICTION` - Cannot ship to destination

**Key Metrics**:
- Invalidation rate by reason
- Time to invalidate
- Recovery rate (orders fixed and resubmitted)

**Domain Events**:
- `FulfillmentOrderInvalidatedEvent`

**Related Services**: Customer Service (notifications)

---

#### L3.1.4: Order Release for Fulfillment
**Description**: Release validated orders for fulfillment, triggering inventory allocation and warehouse operations.

**Technical Implementation**:
- Automatic release after successful validation
- State transition to RELEASED
- Triggers inventory allocation request
- Publishes event for warehouse operations

**Business Rules**:
- Only validated orders can be released
- Release triggers inventory allocation
- Priority orders released first
- Batch release for wave planning (optional)

**Key Metrics**:
- Time from validation to release (target: <1 minute)
- Release processing rate
- Release to shipment cycle time

**Domain Events**:
- `FulfillmentOrderReleasedEvent` - Triggers downstream processing

**Related Services**:
- Inventory Service (allocation request)
- Warehouse Operations (wave planning, pick list generation)

---

#### L3.1.5: Order Picking Tracking
**Description**: Track order status as items are picked in the warehouse.

**Technical Implementation**:
- Listens to `ItemPickedEvent` from Warehouse Operations
- Updates order status to IN_PROGRESS
- Tracks picked quantities per item
- Detects complete picking

**Business Rules**:
- Status changes to IN_PROGRESS when first item picked
- Tracks partial picking progress
- Detects pick completion when all items picked
- Handles short picks (quantity adjustments)

**Key Metrics**:
- Average pick time per order
- Pick completion rate
- Short pick rate

**Domain Events**:
- `FulfillmentOrderPickingCompletedEvent` - All items picked

**Related Services**: Warehouse Operations (picking events)

---

#### L3.1.6: Order Packing Tracking
**Description**: Track order status through the packing process.

**Technical Implementation**:
- Listens to packing events from Warehouse Operations
- Updates order status to PACKING
- Tracks carton assignments from Cartonization Service
- Validates packing completion

**Business Rules**:
- Packing begins after picking completion
- All items must be assigned to cartons
- Quality checks may be required
- Label generation triggered

**Key Metrics**:
- Average pack time per order
- Packing accuracy rate
- Cartonization efficiency

**Domain Events**:
- `FulfillmentOrderPackingCompletedEvent` - Ready for shipment

**Related Services**:
- Warehouse Operations (packing events)
- Cartonization Service (carton assignments)

---

#### L3.1.7: Order Shipment Completion
**Description**: Mark orders as shipped when handed off to carrier.

**Technical Implementation**:
- Receives shipment events from Shipment & Transportation
- State transition to SHIPPED
- Captures tracking information
- Final inventory adjustments
- Customer notification trigger

**Business Rules**:
- Order must be fully packed before shipping
- Tracking number captured
- Carrier and service level recorded
- Final order completion timestamp

**Key Metrics**:
- Order cycle time (received to shipped)
- On-time shipment rate
- Perfect order rate

**Domain Events**:
- `FulfillmentOrderShippedEvent` - Final order status

**Related Services**:
- Shipment & Transportation (tracking info)
- Customer notifications (email/SMS)

---

## L2: Order Modification & Cancellation

### L2.1: Description
Support order modifications and cancellations at various stages of the fulfillment lifecycle.

### L2.2: Business Value
- Flexibility to respond to customer change requests
- Reduce waste from unwanted shipments
- Improve customer satisfaction
- Optimize inventory utilization

### L2.3: L3 Capabilities

#### L3.2.1: Order Cancellation
**Description**: Cancel orders before shipment, releasing allocated inventory and stopping fulfillment activities.

**Technical Implementation**:
- RESTful API for cancellation requests
- State transition to CANCELLED
- Inventory deallocation request
- Warehouse work cancellation notification
- Refund trigger (if applicable)

**Business Rules**:
- Can cancel orders in NEW, RECEIVED, VALIDATED, or RELEASED states
- Cannot cancel orders in PACKING or SHIPPED states
- Partial cancellation supported (line item level)
- Inventory immediately released back to ATP
- Cancel-and-replace supported

**Cancellation Workflow**:
1. Validate order can be cancelled (status check)
2. Cancel warehouse work (if started)
3. Deallocate inventory
4. Update order status to CANCELLED
5. Publish cancellation event
6. Trigger refund (if payment captured)

**Key Metrics**:
- Cancellation rate (% of orders)
- Cancellation by lifecycle stage
- Inventory recovery time
- Late cancellation rate (after picking started)

**API Endpoints**:
- `POST /api/v1/fulfillment_orders/{orderId}/cancel`
- `POST /api/v1/fulfillment_orders/{orderId}/items/{itemId}/cancel` - Line item cancel

**Domain Events**:
- `FulfillmentOrderCancelledEvent`
- `OrderItemCancelledEvent`

**Related Services**:
- Inventory Service (deallocation)
- Warehouse Operations (work cancellation)
- Payment Service (refunds)

---

#### L3.2.2: Order Modification (Future Capability)
**Description**: Support modifications to order details (address, items, quantities) before fulfillment begins.

**Technical Implementation**:
- RESTful API for modification requests
- Validation of modification feasibility
- Re-validation after modification
- Event publishing for downstream updates

**Business Rules**:
- Only orders in NEW or RECEIVED states can be modified
- Address changes always allowed (pre-shipment)
- Item changes require re-validation
- Modifications may require additional payment or trigger refund

**Modification Types**:
- Address change
- Add/remove items
- Quantity changes
- Priority/service level change

**Key Metrics**:
- Modification request rate
- Modification approval rate
- Impact on cycle time

**Related Services**: Inventory (revalidation), Payment (price adjustments)

---

## L2: Order Prioritization & SLA Management

### L2.1: Description
Manage order priority levels and service level agreements to ensure critical orders are fulfilled first.

### L2.2: Business Value
- Meet customer expectations for delivery times
- Optimize resource allocation
- Support differentiated service levels
- Enable revenue optimization

### L2.3: L3 Capabilities

#### L3.3.1: Order Priority Classification
**Description**: Classify orders by priority level to drive fulfillment sequencing.

**Technical Implementation**:
- Priority field in FulfillmentOrder aggregate
- Priority levels: STANDARD, RUSH, EXPRESS, CRITICAL
- Automatic classification based on service level
- Manual priority override capability

**Business Rules**:
- EXPRESS orders have 24-hour SLA
- RUSH orders have 48-hour SLA
- STANDARD orders have 3-5 day SLA
- CRITICAL orders bypass normal queue
- Priority affects allocation timeout and wave planning

**Key Metrics**:
- Orders by priority level
- SLA compliance by priority
- Priority override frequency

**Related Services**: Warehouse Operations (wave planning considers priority)

---

#### L3.3.2: SLA Tracking & Monitoring
**Description**: Track order progress against service level agreements and alert on at-risk orders.

**Technical Implementation**:
- SLA deadline calculation at order receipt
- Real-time progress monitoring
- Alert generation for at-risk orders
- Dashboard for SLA compliance

**Business Rules**:
- SLA clock starts at order receipt
- Weekends/holidays excluded for STANDARD (configurable)
- Alerts at 75% and 90% of SLA time
- Escalation for SLA breaches

**Key Metrics**:
- SLA compliance rate (target: >95%)
- Average fulfillment time by priority
- At-risk order count
- SLA breach reasons

**Related Services**: None (internal monitoring)

---

## L2: Order Visibility & Tracking

### L2.1: Description
Provide comprehensive visibility into order status, location, and estimated delivery for customers and internal stakeholders.

### L2.2: Business Value
- Reduce customer service inquiries
- Enable proactive customer communication
- Support warehouse performance monitoring
- Enable data-driven process improvements

### L2.3: L3 Capabilities

#### L3.4.1: Order Status Query
**Description**: Query current status and details of fulfillment orders.

**Technical Implementation**:
- RESTful API for order lookup
- Support for query by order ID, customer ID, status
- Pagination for bulk queries
- Response includes full order details and history

**Business Rules**:
- Real-time status (no caching)
- Include estimated delivery date
- Show current location (warehouse, in-transit, delivered)
- Include exception information if applicable

**Key Metrics**:
- Query response time (target: <100ms)
- Query volume
- Most common query patterns

**API Endpoints**:
- `GET /api/v1/fulfillment_orders/{orderId}` - Get order details
- `GET /api/v1/fulfillment_orders?customerId={id}&status={status}` - Query orders
- `GET /api/v1/fulfillment_orders/{orderId}/history` - Order event history

**Related Services**: Customer portal, Customer service tools

---

#### L3.4.2: Order Event History
**Description**: Provide complete event history showing all state transitions and activities for an order.

**Technical Implementation**:
- Event sourcing of all order state changes
- Chronological event log per order
- Includes timestamps, user attribution, event details
- Queryable via API

**Business Rules**:
- All state changes logged as events
- Events immutable (append-only)
- Includes system and manual events
- Unlimited retention

**Key Metrics**:
- Average events per order
- Event history query performance
- Storage growth rate

**Related Services**: None (internal capability)

---

#### L3.4.3: Bulk Order Status Reporting
**Description**: Support bulk status queries and reporting for operational dashboards.

**Technical Implementation**:
- Aggregation queries across orders
- Support for filtering by date range, status, priority
- Export capabilities (CSV, Excel)
- Scheduled report generation

**Business Rules**:
- Reports run on read replicas (no production impact)
- Maximum query window: 90 days
- Large result sets paginated
- Reports cached for 5 minutes

**Key Metrics**:
- Report generation time
- Most requested report types
- Export volume

**API Endpoints**:
- `GET /api/v1/fulfillment_orders/summary?from=date&to=date`
- `GET /api/v1/fulfillment_orders/export?status=SHIPPED&from=date`

**Related Services**: Business intelligence, Analytics platforms

---

## L2: Event-Driven Orchestration

### L2.1: Description
Orchestrate fulfillment operations through event-driven choreography, publishing and consuming events to coordinate across services.

### L2.2: Business Value
- Loose coupling between services
- Scalability and resilience
- Asynchronous processing
- Event-driven audit trail

### L2.3: L3 Capabilities

#### L3.5.1: Order Event Publishing
**Description**: Publish domain events for all significant order state changes to enable downstream processing.

**Technical Implementation**:
- Kafka as event bus
- CloudEvents format for standardization
- Event schema versioning
- Guaranteed delivery (Kafka durability)

**Published Events**:
- `FulfillmentOrderReceivedEvent` - Order entered system
- `FulfillmentOrderValidatedEvent` - Order validated successfully
- `FulfillmentOrderInvalidatedEvent` - Order failed validation
- `FulfillmentOrderReleasedEvent` - Order released for fulfillment
- `FulfillmentOrderPickingCompletedEvent` - Picking completed
- `FulfillmentOrderPackingCompletedEvent` - Packing completed
- `FulfillmentOrderShippedEvent` - Order handed to carrier
- `FulfillmentOrderCancelledEvent` - Order cancelled

**Event Schema Example**:
```json
{
  "id": "evt-order-12345",
  "type": "com.paklog.order.validated",
  "source": "order-management-service",
  "specversion": "1.0",
  "time": "2025-10-18T10:30:00Z",
  "datacontenttype": "application/json",
  "data": {
    "orderId": "ORD-67890",
    "customerId": "CUST-123",
    "items": [
      {"sku": "PROD-001", "quantity": 2}
    ],
    "priority": "STANDARD",
    "validatedAt": "2025-10-18T10:30:00Z"
  }
}
```

**Business Rules**:
- Events published after successful state transition
- Events include correlation ID for tracing
- Events contain full order context (avoid lookups)
- Published to topic: `fulfillment.order.v1.events`

**Key Metrics**:
- Events published per minute
- Event publishing latency
- Event schema compliance rate

**Related Services**: All downstream services

---

#### L3.5.2: Warehouse Event Consumption
**Description**: Consume events from Warehouse Operations to track fulfillment progress.

**Technical Implementation**:
- Kafka consumers for warehouse topic
- Event handlers update order status
- Idempotent event processing
- Dead letter queue for failed events

**Consumed Events**:
- `PickingStartedEvent` - Update order to IN_PROGRESS
- `ItemPickedEvent` - Track picked quantities
- `PickingCompletedEvent` - All items picked
- `PackingCompletedEvent` - Order packed and labeled
- `QualityCheckCompletedEvent` - QC passed

**Business Rules**:
- Events processed exactly once (idempotency)
- Out-of-order events handled gracefully
- Failed events retried (max 3 attempts)
- Poison pill events moved to DLQ

**Key Metrics**:
- Event processing lag (target: <2 seconds)
- Processing error rate
- DLQ depth

**Related Services**: Warehouse Operations

---

#### L3.5.3: Inventory Event Consumption
**Description**: Consume events from Inventory Service to track allocation and stock status.

**Technical Implementation**:
- Kafka consumers for inventory topic
- Event handlers update order state
- Correlation of inventory events to orders

**Consumed Events**:
- `InventoryAllocatedEvent` - Allocation successful
- `AllocationFailedEvent` - Insufficient inventory
- `InventoryDeallocatedEvent` - Allocation released (cancellation)

**Business Rules**:
- Allocation failures trigger order invalidation
- Track allocation IDs for audit
- Handle allocation expiration events

**Key Metrics**:
- Allocation success rate
- Time to allocate
- Allocation failure reasons

**Related Services**: Inventory Service

---

## L2: Exception Handling & Recovery

### L2.1: Description
Handle exceptional scenarios and provide recovery mechanisms for failed or problematic orders.

### L2.2: Business Value
- Minimize order failures
- Automated recovery where possible
- Clear escalation paths
- Maintain customer satisfaction

### L2.3: L3 Capabilities

#### L3.6.1: Automated Retry Logic
**Description**: Automatically retry failed operations with exponential backoff.

**Technical Implementation**:
- Spring Retry integration
- Configurable retry policies per operation type
- Exponential backoff (1s, 2s, 4s, 8s)
- Maximum retry attempts (default: 3)

**Business Rules**:
- Transient failures retried automatically
- Permanent failures escalated
- Retry count tracked in order metadata
- Alert on excessive retries

**Key Metrics**:
- Retry success rate
- Average retries per order
- Operations requiring retry

**Related Services**: All dependent services

---

#### L3.6.2: Dead Letter Queue Processing
**Description**: Handle events and operations that have permanently failed after retries.

**Technical Implementation**:
- DLQ for failed Kafka events
- Manual review and reprocessing interface
- Root cause analysis tools
- Alerting on DLQ depth

**Business Rules**:
- Events moved to DLQ after 3 failed attempts
- DLQ monitored with alerts (depth > 10)
- Manual intervention required for reprocessing
- Track DLQ resolution time

**Key Metrics**:
- DLQ depth
- Average resolution time
- DLQ entry reasons

**Related Services**: Operations team (manual intervention)

---

## L2: Monitoring & Observability

### L2.1: Description
Comprehensive monitoring, metrics, and observability for operational excellence.

### L2.2: Business Value
- Proactive issue detection
- Performance optimization
- Business intelligence
- Compliance and reporting

### L2.3: L3 Capabilities

#### L3.7.1: Order Metrics Collection
**Description**: Collect and expose comprehensive metrics for order operations and business KPIs.

**Technical Implementation**:
- Prometheus metrics integration
- Custom business metrics
- Real-time Grafana dashboards
- Metric-based alerting

**Key Metrics Exposed**:
- `orders.received.total` - Total orders received
- `orders.status{status}` - Orders by status
- `orders.cycle.time` - Average fulfillment cycle time
- `orders.sla.compliance` - SLA compliance percentage
- `orders.cancellation.rate` - Cancellation rate
- `orders.validation.success.rate` - Validation success rate
- `orders.priority{priority}` - Orders by priority

**Business Rules**:
- Metrics updated in real-time
- Dashboards auto-refresh (30 seconds)
- Alerts on metric thresholds
- Historical retention (90 days)

**Related Services**: Infrastructure (Prometheus, Grafana)

---

#### L3.7.2: Distributed Tracing
**Description**: Trace order requests across all service boundaries for end-to-end visibility.

**Technical Implementation**:
- OpenTelemetry instrumentation
- Trace context propagation
- Integration with Tempo
- Correlation with logs and metrics

**Business Rules**:
- All requests traced with correlation ID
- Trace includes all downstream service calls
- Sampling: 100% for errors, 10% for success
- Trace retention: 30 days

**Key Metrics**:
- End-to-end order latency
- Service dependency performance
- Error rate by trace path

**Related Services**: All services (distributed tracing)

---

## Summary

The Order Management Service provides comprehensive order fulfillment orchestration through:

### Key Strengths
- **Orchestration**: Event-driven coordination across fulfillment services
- **Visibility**: Real-time order status and complete history
- **Flexibility**: Support for cancellations and modifications
- **Reliability**: Automated retry and exception handling
- **Scalability**: Event-driven architecture for high throughput

### Business Impact
- **Order Throughput**: 10,000+ orders per hour
- **SLA Compliance**: >95% on-time fulfillment
- **Cancellation Flexibility**: Support cancellation up to packing stage
- **Order Accuracy**: >99% perfect order rate
- **Cycle Time**: Average 4-6 hours receipt to shipment (STANDARD)

### Integration Points
- **Upstream**: E-commerce platforms, OMS systems
- **Downstream**: Inventory (allocation), Warehouse (fulfillment), Shipment (tracking)
- **Events**: Publishes order lifecycle events, consumes warehouse and inventory events

### Order Lifecycle
```
NEW → RECEIVED → VALIDATED → RELEASED → IN_PROGRESS → PACKING → SHIPPED
                     ↓            ↓
                INVALIDATED   CANCELLED
```

### Technology Highlights
- Hexagonal architecture for clean boundaries
- Event-driven choreography via Kafka
- CloudEvents for event standardization
- Idempotent event processing
- Comprehensive observability
