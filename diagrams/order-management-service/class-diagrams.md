# Order Management Service - Class Diagrams

## Domain Model Overview

```mermaid
classDiagram
    class Order {
        <<Aggregate Root>>
        -String orderId
        -String customerId
        -OrderType orderType
        -OrderStatus status
        -Priority priority
        -Address shippingAddress
        -Address billingAddress
        -List~OrderLine~ orderLines
        -ShippingMethod shippingMethod
        -PaymentInfo paymentInfo
        -Money totalAmount
        -DateTime orderDate
        -DateTime requiredDate
        -DateTime shippedDate
        -List~DomainEvent~ events
        +validate() OrderValidation
        +prioritize() Priority
        +allocateInventory() AllocationResult
        +cancel(reason) void
        +split(criteria) List~Order~
        +addLine(OrderLine) void
        +removeLine(lineId) void
        +updateShipping(method) void
        +calculateTotal() Money
        +applyPromotion(code) DiscountResult
        +registerEvent(event) void
    }

    class OrderLine {
        <<Entity>>
        -String orderLineId
        -String productId
        -String skuCode
        -int quantity
        -int allocatedQuantity
        -int pickedQuantity
        -int shippedQuantity
        -Money unitPrice
        -Money lineTotal
        -LineStatus status
        -List~LineAttribute~ attributes
        +allocate(quantity) void
        +pick(quantity) void
        +ship(quantity) void
        +cancel() void
        +updateQuantity(quantity) void
        +calculateLineTotal() Money
        +validateQuantity() boolean
    }

    class Customer {
        <<Entity>>
        -String customerId
        -String name
        -String email
        -CustomerType type
        -CustomerTier tier
        -List~Address~ addresses
        -PaymentMethod defaultPayment
        -CreditLimit creditLimit
        -List~String~ orderHistory
        +validateCredit(amount) boolean
        +getPriorityLevel() Priority
        +getShippingAddress() Address
        +addAddress(address) void
        +updateTier(tier) void
    }

    class Address {
        <<Value Object>>
        -String line1
        -String line2
        -String city
        -String state
        -String postalCode
        -String country
        -GeoLocation coordinates
        +validate() boolean
        +format() String
        +calculateDistance(other) Distance
    }

    class ShippingMethod {
        <<Value Object>>
        -String carrierId
        -String serviceType
        -DeliverySpeed speed
        -Money cost
        -EstimatedDelivery estimatedDelivery
        +calculateCost(weight, distance) Money
        +estimateDelivery(origin, destination) DateTime
    }

    class PaymentInfo {
        <<Value Object>>
        -PaymentType type
        -String paymentMethodId
        -Money amount
        -PaymentStatus status
        -String transactionId
        +process() PaymentResult
        +validate() boolean
        +refund(amount) RefundResult
    }

    class OrderValidation {
        <<Domain Service>>
        +validateOrder(order) ValidationResult
        +validateInventory(order) boolean
        +validateCredit(customer, amount) boolean
        +validateShipping(address) boolean
        +validateBusinessRules(order) List~ValidationError~
    }

    class OrderPrioritizer {
        <<Domain Service>>
        +calculatePriority(order) Priority
        +applyRules(order, rules) Priority
        +considerCustomerTier(customer) int
        +considerShippingSpeed(method) int
        +considerOrderValue(amount) int
    }

    Order "1" --> "*" OrderLine : contains
    Order "1" --> "1" Customer : placed by
    Order "1" --> "2" Address : ships to/bills to
    Order "1" --> "1" ShippingMethod : uses
    Order "1" --> "1" PaymentInfo : paid with
    OrderValidation ..> Order : validates
    OrderPrioritizer ..> Order : prioritizes
```

## Order State Machine

```mermaid
classDiagram
    class OrderStatus {
        <<Enumeration>>
        DRAFT
        PENDING_VALIDATION
        VALIDATED
        PENDING_ALLOCATION
        ALLOCATED
        PENDING_PICK
        PICKING
        PICKED
        PENDING_PACK
        PACKING
        PACKED
        PENDING_SHIP
        SHIPPED
        DELIVERED
        CANCELLED
        RETURNED
    }

    class OrderStateMachine {
        <<State Machine>>
        -OrderStatus currentState
        -List~StateTransition~ transitions
        -List~StateRule~ rules
        +transition(event) OrderStatus
        +canTransition(toState) boolean
        +getValidTransitions() List~OrderStatus~
        +onEnterState(state) void
        +onExitState(state) void
    }

    class StateTransition {
        <<Value Object>>
        -OrderStatus fromState
        -OrderStatus toState
        -OrderEvent event
        -List~Condition~ conditions
        +isValid(order) boolean
        +execute(order) void
    }

    class OrderEvent {
        <<Enumeration>>
        VALIDATE
        ALLOCATE
        START_PICK
        COMPLETE_PICK
        START_PACK
        COMPLETE_PACK
        SHIP
        DELIVER
        CANCEL
        RETURN
    }

    OrderStateMachine "1" --> "1" OrderStatus : current
    OrderStateMachine "1" --> "*" StateTransition : manages
    StateTransition "1" --> "2" OrderStatus : from/to
    StateTransition "1" --> "1" OrderEvent : triggered by
```

## Command and Query Handlers

```mermaid
classDiagram
    class CreateOrderCommand {
        <<Command>>
        -String customerId
        -List~OrderLineDto~ lines
        -AddressDto shippingAddress
        -AddressDto billingAddress
        -String shippingMethodId
        +validate() ValidationResult
    }

    class CreateOrderHandler {
        <<Command Handler>>
        -OrderRepository repository
        -OrderValidator validator
        -EventBus eventBus
        +handle(command) OrderId
        -createOrder(command) Order
        -validateOrder(order) void
        -saveOrder(order) void
        -publishEvents(events) void
    }

    class AllocateOrderCommand {
        <<Command>>
        -String orderId
        -AllocationStrategy strategy
        +validate() ValidationResult
    }

    class AllocateOrderHandler {
        <<Command Handler>>
        -OrderRepository orderRepo
        -InventoryService inventoryService
        -EventBus eventBus
        +handle(command) AllocationResult
        -loadOrder(orderId) Order
        -allocateInventory(order) void
        -updateOrder(order) void
    }

    class GetOrderQuery {
        <<Query>>
        -String orderId
        -boolean includeHistory
    }

    class GetOrderHandler {
        <<Query Handler>>
        -OrderReadModel readModel
        +handle(query) OrderDto
        -loadOrder(orderId) OrderProjection
        -includeHistory(order) void
    }

    class SearchOrdersQuery {
        <<Query>>
        -OrderSearchCriteria criteria
        -Pagination pagination
        -Sorting sorting
    }

    class SearchOrdersHandler {
        <<Query Handler>>
        -OrderSearchService searchService
        +handle(query) PagedResult~OrderSummary~
        -buildSearchQuery(criteria) SearchQuery
        -executePaginatedSearch(query) PagedResult
    }

    CreateOrderHandler ..> CreateOrderCommand : handles
    AllocateOrderHandler ..> AllocateOrderCommand : handles
    GetOrderHandler ..> GetOrderQuery : handles
    SearchOrdersHandler ..> SearchOrdersQuery : handles
```

## Repository and Infrastructure

```mermaid
classDiagram
    class OrderRepository {
        <<Repository>>
        +save(order) void
        +findById(orderId) Order
        +findByCustomer(customerId) List~Order~
        +findByStatus(status) List~Order~
        +findByDateRange(start, end) List~Order~
        +update(order) void
        +delete(orderId) void
    }

    class OrderRepositoryImpl {
        <<Repository Implementation>>
        -JpaOrderRepository jpaRepo
        -OrderMapper mapper
        +save(order) void
        +findById(orderId) Order
        -toDomain(entity) Order
        -toEntity(domain) OrderEntity
    }

    class OrderEntity {
        <<JPA Entity>>
        -Long id
        -String orderId
        -String customerId
        -String status
        -String orderData
        -Timestamp createdAt
        -Timestamp updatedAt
    }

    class OrderEventStore {
        <<Event Store>>
        -EventStoreDb eventStore
        +append(orderId, events) void
        +getEvents(orderId) List~DomainEvent~
        +getEventsAfter(orderId, version) List~DomainEvent~
        +getSnapshot(orderId) OrderSnapshot
        +saveSnapshot(orderId, snapshot) void
    }

    class OrderProjection {
        <<Read Model>>
        -String orderId
        -OrderSummary summary
        -List~OrderLineView~ lines
        -CustomerView customer
        -Timeline timeline
        +update(event) void
        +rebuild(events) void
    }

    OrderRepository <|.. OrderRepositoryImpl : implements
    OrderRepositoryImpl ..> OrderEntity : persists
    OrderEventStore ..> Order : stores events
    OrderProjection ..> Order : projects
```

## Domain Events

```mermaid
classDiagram
    class DomainEvent {
        <<Abstract>>
        -String eventId
        -String aggregateId
        -DateTime occurredAt
        -int version
        +getEventType() String
    }

    class OrderCreatedEvent {
        <<Event>>
        -String orderId
        -String customerId
        -List~OrderLineData~ lines
        -Money totalAmount
        +getEventType() String
    }

    class OrderValidatedEvent {
        <<Event>>
        -String orderId
        -ValidationResult result
        +getEventType() String
    }

    class OrderAllocatedEvent {
        <<Event>>
        -String orderId
        -List~AllocationData~ allocations
        +getEventType() String
    }

    class OrderShippedEvent {
        <<Event>>
        -String orderId
        -String trackingNumber
        -String carrier
        -DateTime shippedAt
        +getEventType() String
    }

    class OrderCancelledEvent {
        <<Event>>
        -String orderId
        -String reason
        -String cancelledBy
        +getEventType() String
    }

    class OrderEventPublisher {
        <<Publisher>>
        -KafkaProducer producer
        -EventSerializer serializer
        +publish(event) void
        +publishBatch(events) void
        -createCloudEvent(event) CloudEvent
    }

    class OrderEventHandler {
        <<Event Handler>>
        -OrderProjectionUpdater projectionUpdater
        -NotificationService notificationService
        +handle(event) void
        -updateProjection(event) void
        -sendNotification(event) void
    }

    DomainEvent <|-- OrderCreatedEvent
    DomainEvent <|-- OrderValidatedEvent
    DomainEvent <|-- OrderAllocatedEvent
    DomainEvent <|-- OrderShippedEvent
    DomainEvent <|-- OrderCancelledEvent
    OrderEventPublisher ..> DomainEvent : publishes
    OrderEventHandler ..> DomainEvent : handles
```

## Integration Services

```mermaid
classDiagram
    class OrderIntegrationService {
        <<Integration Service>>
        -InventoryClient inventoryClient
        -ShippingClient shippingClient
        -PaymentClient paymentClient
        -NotificationClient notificationClient
        +checkInventory(order) InventoryStatus
        +reserveInventory(order) ReservationResult
        +calculateShipping(order) ShippingQuote
        +processPayment(payment) PaymentResult
        +sendOrderConfirmation(order) void
    }

    class InventoryClient {
        <<HTTP Client>>
        -RestTemplate restTemplate
        -String baseUrl
        -CircuitBreaker circuitBreaker
        +checkAvailability(items) AvailabilityResponse
        +reserve(items) ReservationResponse
        +release(reservationId) void
        -handleError(error) void
    }

    class ShippingClient {
        <<HTTP Client>>
        -WebClient webClient
        -RetryPolicy retryPolicy
        +getRates(shipment) List~Rate~
        +createShipment(order) Shipment
        +trackShipment(trackingNumber) TrackingInfo
    }

    class OrderApiController {
        <<REST Controller>>
        -CreateOrderHandler createHandler
        -GetOrderHandler getHandler
        -SearchOrdersHandler searchHandler
        +createOrder(request) ResponseEntity
        +getOrder(orderId) ResponseEntity
        +searchOrders(criteria) ResponseEntity
        +updateOrder(orderId, request) ResponseEntity
        +cancelOrder(orderId) ResponseEntity
    }

    class OrderKafkaListener {
        <<Kafka Listener>>
        -OrderEventHandler eventHandler
        -DeadLetterHandler deadLetterHandler
        +onInventoryAllocated(event) void
        +onShipmentCreated(event) void
        +onPaymentProcessed(event) void
        -processEvent(event) void
        -handleError(event, error) void
    }

    OrderIntegrationService --> InventoryClient : uses
    OrderIntegrationService --> ShippingClient : uses
    OrderApiController ..> OrderIntegrationService : uses
    OrderKafkaListener ..> OrderEventHandler : delegates to
```

## Business Rules and Policies

```mermaid
classDiagram
    class OrderBusinessRules {
        <<Policy>>
        +MIN_ORDER_AMOUNT: Money
        +MAX_ORDER_LINES: int
        +CANCELLATION_CUTOFF_HOURS: int
        +validateMinimumAmount(order) boolean
        +validateMaxLines(order) boolean
        +canCancelOrder(order) boolean
        +requiresApproval(order) boolean
    }

    class PriorityPolicy {
        <<Policy>>
        -List~PriorityRule~ rules
        +calculatePriority(order, customer) Priority
        +applyExpressPriority(shipping) int
        +applyCustomerTierPriority(tier) int
        +applyOrderValuePriority(amount) int
    }

    class AllocationStrategy {
        <<Strategy Interface>>
        +allocate(order, inventory) AllocationResult
    }

    class FIFOAllocation {
        <<Strategy>>
        +allocate(order, inventory) AllocationResult
        -sortByDate(inventory) List~InventoryItem~
    }

    class NearestLocationAllocation {
        <<Strategy>>
        +allocate(order, inventory) AllocationResult
        -findNearestLocations(address) List~Location~
    }

    class PriorityBasedAllocation {
        <<Strategy>>
        +allocate(order, inventory) AllocationResult
        -sortByPriority(orders) List~Order~
    }

    AllocationStrategy <|.. FIFOAllocation
    AllocationStrategy <|.. NearestLocationAllocation
    AllocationStrategy <|.. PriorityBasedAllocation
```