# Inventory Service - Class Diagrams

## Domain Model Overview

```mermaid
classDiagram
    class InventoryItem {
        <<Aggregate Root>>
        -String inventoryId
        -String skuCode
        -String productId
        -Location location
        -int quantityOnHand
        -int quantityAvailable
        -int quantityAllocated
        -int quantityInTransit
        -int quantityDamaged
        -InventoryStatus status
        -List~Reservation~ reservations
        -List~Movement~ movements
        -DateTime lastCycleCount
        -DateTime lastMovement
        +reserve(quantity, orderId) Reservation
        +release(reservationId) void
        +adjust(quantity, reason) Adjustment
        +move(toLocation, quantity) Movement
        +damage(quantity, reason) void
        +cycleCount(actualQuantity) CycleCountResult
        +calculateAvailable() int
        +isAvailable(quantity) boolean
        +getAging() Duration
    }

    class Reservation {
        <<Entity>>
        -String reservationId
        -String orderId
        -String customerId
        -int quantity
        -ReservationType type
        -DateTime reservedAt
        -DateTime expiresAt
        -ReservationStatus status
        +extend(duration) void
        +partial(quantity) void
        +cancel() void
        +confirm() void
        +isExpired() boolean
    }

    class InventoryLocation {
        <<Value Object>>
        -String warehouseId
        -String zoneId
        -String aisleId
        -String bayId
        -String shelfId
        -String binId
        -LocationType type
        +getFullPath() String
        +isPickLocation() boolean
        +isReserveLocation() boolean
    }

    class Movement {
        <<Entity>>
        -String movementId
        -InventoryLocation fromLocation
        -InventoryLocation toLocation
        -int quantity
        -MovementType type
        -MovementStatus status
        -String performedBy
        -DateTime startedAt
        -DateTime completedAt
        +complete() void
        +cancel() void
        +validate() boolean
    }

    class Adjustment {
        <<Entity>>
        -String adjustmentId
        -int quantityAdjusted
        -AdjustmentType type
        -AdjustmentReason reason
        -String authorizedBy
        -String comments
        -DateTime adjustedAt
        +approve() void
        +reject() void
    }

    class StockLevel {
        <<Value Object>>
        -int minQuantity
        -int maxQuantity
        -int reorderPoint
        -int reorderQuantity
        -int safetyStock
        +needsReorder() boolean
        +calculateReorderQuantity() int
    }

    InventoryItem "1" --> "*" Reservation : manages
    InventoryItem "1" --> "1" InventoryLocation : stored at
    InventoryItem "1" --> "*" Movement : tracks
    InventoryItem "1" --> "*" Adjustment : records
    InventoryItem "1" --> "1" StockLevel : maintains
```

## Inventory Tracking and Valuation

```mermaid
classDiagram
    class InventoryValuation {
        <<Domain Service>>
        -ValuationMethod method
        +calculateValue(items) Money
        +calculateFIFO(items) Money
        +calculateLIFO(items) Money
        +calculateWeightedAverage(items) Money
        +getInventoryValue(warehouse) Money
    }

    class InventoryLot {
        <<Entity>>
        -String lotNumber
        -String skuCode
        -int quantity
        -Money unitCost
        -DateTime receivedDate
        -DateTime expirationDate
        -String batchNumber
        -String serialNumber
        -LotStatus status
        +age() Duration
        +isExpired() boolean
        +isExpiringSoon(days) boolean
        +split(quantity) InventoryLot
    }

    class InventoryTransaction {
        <<Entity>>
        -String transactionId
        -TransactionType type
        -String skuCode
        -int quantity
        -Money unitCost
        -Money totalCost
        -String referenceId
        -DateTime transactionDate
        -String userId
        +reverse() InventoryTransaction
        +validate() boolean
    }

    class ABCAnalysis {
        <<Domain Service>>
        -double aPercentage
        -double bPercentage
        -double cPercentage
        +classify(items) ABCClassification
        +calculateVelocity(item) Velocity
        +getAItems() List~InventoryItem~
        +getBItems() List~InventoryItem~
        +getCItems() List~InventoryItem~
    }

    class CycleCount {
        <<Entity>>
        -String cycleCountId
        -List~CountTask~ tasks
        -CycleCountType type
        -CountStatus status
        -DateTime scheduledDate
        -DateTime startedAt
        -DateTime completedAt
        -List~Discrepancy~ discrepancies
        +addTask(location, items) void
        +recordCount(taskId, count) void
        +complete() CycleCountResult
        +calculateAccuracy() double
    }

    InventoryValuation ..> InventoryLot : values
    InventoryItem "1" --> "*" InventoryLot : contains
    InventoryItem "1" --> "*" InventoryTransaction : records
    ABCAnalysis ..> InventoryItem : classifies
    CycleCount "1" --> "*" InventoryItem : counts
```

## Allocation and Reservation System

```mermaid
classDiagram
    class AllocationEngine {
        <<Domain Service>>
        -AllocationStrategy strategy
        -RuleEngine ruleEngine
        +allocate(order) AllocationResult
        +allocateBatch(orders) BatchAllocationResult
        +deallocate(allocationId) void
        +reallocate(allocationId) void
        -checkAvailability(items) boolean
        -applyRules(allocation) void
        -optimizeAllocation(items) void
    }

    class ReservationManager {
        <<Domain Service>>
        -ReservationRepository repository
        -ExpirationPolicy policy
        +createReservation(request) Reservation
        +extendReservation(id, duration) void
        +cancelReservation(id) void
        +confirmReservation(id) void
        +expireReservations() List~Reservation~
        -validateReservation(request) boolean
        -checkConflicts(request) boolean
    }

    class AllocationStrategy {
        <<Strategy Interface>>
        +allocate(request) AllocationResult
    }

    class FEFOAllocation {
        <<Strategy>>
        +allocate(request) AllocationResult
        -sortByExpiration(lots) List~InventoryLot~
    }

    class ZoneBasedAllocation {
        <<Strategy>>
        +allocate(request) AllocationResult
        -prioritizeZones(zones) List~Zone~
    }

    class CrossDockAllocation {
        <<Strategy>>
        +allocate(request) AllocationResult
        -checkInboundSchedule() List~InboundItem~
    }

    class AllocationResult {
        <<Value Object>>
        -String allocationId
        -List~AllocatedItem~ items
        -AllocationStatus status
        -List~AllocationIssue~ issues
        +isFullyAllocated() boolean
        +getShortages() List~Shortage~
    }

    AllocationEngine --> AllocationStrategy : uses
    AllocationStrategy <|.. FEFOAllocation
    AllocationStrategy <|.. ZoneBasedAllocation
    AllocationStrategy <|.. CrossDockAllocation
    AllocationEngine ..> AllocationResult : returns
    ReservationManager --> Reservation : manages
```

## Command and Query Handlers

```mermaid
classDiagram
    class AdjustInventoryCommand {
        <<Command>>
        -String skuCode
        -String locationId
        -int quantity
        -AdjustmentReason reason
        -String comments
        +validate() ValidationResult
    }

    class AdjustInventoryHandler {
        <<Command Handler>>
        -InventoryRepository repository
        -AuditService auditService
        -EventBus eventBus
        +handle(command) AdjustmentResult
        -loadInventory(sku, location) InventoryItem
        -createAdjustment(command) Adjustment
        -publishEvent(adjustment) void
    }

    class ReserveInventoryCommand {
        <<Command>>
        -String orderId
        -List~ReservationRequest~ items
        -Duration reservationDuration
        +validate() ValidationResult
    }

    class ReserveInventoryHandler {
        <<Command Handler>>
        -ReservationManager manager
        -InventoryRepository repository
        -EventBus eventBus
        +handle(command) ReservationResult
        -checkAvailability(items) boolean
        -createReservations(command) List~Reservation~
    }

    class GetInventoryQuery {
        <<Query>>
        -String skuCode
        -String locationId
        -boolean includeReservations
    }

    class GetInventoryHandler {
        <<Query Handler>>
        -InventoryReadModel readModel
        +handle(query) InventoryDto
        -loadInventory(sku, location) InventoryProjection
        -enrichWithReservations(inventory) void
    }

    class InventoryAvailabilityQuery {
        <<Query>>
        -List~String~ skuCodes
        -String warehouseId
    }

    class InventoryAvailabilityHandler {
        <<Query Handler>>
        -AvailabilityService service
        +handle(query) AvailabilityResult
        -checkRealTimeAvailability(skus) Map~String, Integer~
        -considerInbound(skus) Map~String, Integer~
    }

    AdjustInventoryHandler ..> AdjustInventoryCommand : handles
    ReserveInventoryHandler ..> ReserveInventoryCommand : handles
    GetInventoryHandler ..> GetInventoryQuery : handles
    InventoryAvailabilityHandler ..> InventoryAvailabilityQuery : handles
```

## Repository and Persistence

```mermaid
classDiagram
    class InventoryRepository {
        <<Repository>>
        +save(inventory) void
        +findBySku(sku) List~InventoryItem~
        +findByLocation(location) List~InventoryItem~
        +findBySkuAndLocation(sku, location) InventoryItem
        +findLowStock() List~InventoryItem~
        +update(inventory) void
        +delete(inventoryId) void
    }

    class ReservationRepository {
        <<Repository>>
        +save(reservation) void
        +findById(id) Reservation
        +findByOrder(orderId) List~Reservation~
        +findExpired() List~Reservation~
        +findActive() List~Reservation~
        +update(reservation) void
        +delete(id) void
    }

    class InventoryEventStore {
        <<Event Store>>
        +append(inventoryId, events) void
        +getEvents(inventoryId) List~InventoryEvent~
        +getSnapshot(inventoryId) InventorySnapshot
        +saveSnapshot(snapshot) void
        +replayEvents(from, to) List~InventoryEvent~
    }

    class InventoryProjection {
        <<Read Model>>
        -String skuCode
        -Map~String, Integer~ locationQuantities
        -int totalOnHand
        -int totalAvailable
        -int totalReserved
        -List~ReservationView~ activeReservations
        +update(event) void
        +getAvailableByLocation(location) int
    }

    class InventoryCache {
        <<Cache>>
        -RedisTemplate redis
        -Duration ttl
        +get(key) InventoryItem
        +put(key, item) void
        +evict(key) void
        +getAvailability(sku) int
        +updateAvailability(sku, quantity) void
    }

    InventoryRepository ..> InventoryItem : persists
    ReservationRepository ..> Reservation : persists
    InventoryEventStore ..> InventoryItem : stores events
    InventoryProjection ..> InventoryItem : projects
    InventoryCache ..> InventoryItem : caches
```

## Domain Events

```mermaid
classDiagram
    class InventoryEvent {
        <<Abstract>>
        -String eventId
        -String inventoryId
        -String skuCode
        -DateTime occurredAt
        +getEventType() String
    }

    class InventoryAdjustedEvent {
        <<Event>>
        -int quantityAdjusted
        -AdjustmentReason reason
        -String adjustedBy
        +getEventType() String
    }

    class InventoryReservedEvent {
        <<Event>>
        -String reservationId
        -String orderId
        -int quantity
        -DateTime expiresAt
        +getEventType() String
    }

    class InventoryMovedEvent {
        <<Event>>
        -String movementId
        -InventoryLocation fromLocation
        -InventoryLocation toLocation
        -int quantity
        +getEventType() String
    }

    class StockLowEvent {
        <<Event>>
        -String skuCode
        -int currentQuantity
        -int reorderPoint
        -int suggestedReorder
        +getEventType() String
    }

    class CycleCountCompletedEvent {
        <<Event>>
        -String cycleCountId
        -List~CountDiscrepancy~ discrepancies
        -double accuracy
        +getEventType() String
    }

    class InventoryEventPublisher {
        <<Publisher>>
        -KafkaProducer producer
        +publish(event) void
        +publishBatch(events) void
        -toCloudEvent(event) CloudEvent
    }

    InventoryEvent <|-- InventoryAdjustedEvent
    InventoryEvent <|-- InventoryReservedEvent
    InventoryEvent <|-- InventoryMovedEvent
    InventoryEvent <|-- StockLowEvent
    InventoryEvent <|-- CycleCountCompletedEvent
    InventoryEventPublisher ..> InventoryEvent : publishes
```

## Integration and External Services

```mermaid
classDiagram
    class InventoryIntegrationService {
        <<Integration Service>>
        -ERPClient erpClient
        -WMSClient wmsClient
        -SupplierPortalClient supplierClient
        +syncWithERP() SyncResult
        +updateFromWMS(update) void
        +checkSupplierInventory(sku) SupplierStock
        +requestReplenishment(items) ReplenishmentOrder
    }

    class ReplenishmentService {
        <<Domain Service>>
        -ReplenishmentStrategy strategy
        -ForecastingService forecasting
        -SupplierService suppliers
        +calculateReplenishment() List~ReplenishmentOrder~
        +createPurchaseOrder(items) PurchaseOrder
        +scheduleDelivery(order) DeliverySchedule
        -forecastDemand(sku) DemandForecast
        -selectSupplier(sku) Supplier
    }

    class InventoryAnalyticsService {
        <<Analytics Service>>
        -MetricsCollector metrics
        -ReportGenerator reports
        +calculateTurnover(period) TurnoverRate
        +getSlowMovingItems() List~SlowMover~
        +getStockoutRisk() List~StockoutRisk~
        +generateInventoryReport(criteria) Report
        +calculateCarryingCost() Money
    }

    class InventoryAlertService {
        <<Alert Service>>
        -AlertRules rules
        -NotificationService notifications
        +checkStockLevels() List~Alert~
        +checkExpiration() List~Alert~
        +checkAging() List~Alert~
        +sendAlert(alert) void
        -evaluateRules(inventory) List~Alert~
    }

    InventoryIntegrationService --> ReplenishmentService : triggers
    ReplenishmentService ..> InventoryItem : replenishes
    InventoryAnalyticsService ..> InventoryItem : analyzes
    InventoryAlertService ..> InventoryItem : monitors
```