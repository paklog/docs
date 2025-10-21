# PakLog Domain Model Diagrams

## Table of Contents
1. [Domain Bounded Contexts](#domain-bounded-contexts)
2. [Wave Planning Domain Model](#wave-planning-domain-model)
3. [Task Execution Domain Model](#task-execution-domain-model)
4. [Pick Execution Domain Model](#pick-execution-domain-model)
5. [Location Master Domain Model](#location-master-domain-model)
6. [Pack & Ship Domain Model](#pack--ship-domain-model)
7. [Physical Tracking Domain Model](#physical-tracking-domain-model)
8. [Entity Relationships](#entity-relationships)
9. [Value Objects](#value-objects)
10. [Domain Events](#domain-events)

---

## Domain Bounded Contexts

Overview of Domain-Driven Design bounded contexts and their relationships.

```mermaid
graph TB
    subgraph "WMS Domain"
        WP[Wave Planning Context]
        LM[Location Master Context]
        WL[Workload Planning Context]
    end

    subgraph "WES Domain"
        TE[Task Execution Context]
        PE[Pick Execution Context]
        PS[Pack & Ship Context]
        PT[Physical Tracking Context]
    end

    subgraph "Core Domain"
        INV[Inventory Context]
        ORD[Order Context]
    end

    WP --> TE
    TE --> PE
    PE --> PS
    PS --> PT
    WP --> LM
    TE --> LM
    PE --> PT
    WL --> TE
    INV --> WP
    ORD --> WP
    PT --> INV
```

---

## Wave Planning Domain Model

```mermaid
classDiagram
    class Wave {
        -String waveId
        -String warehouseId
        -WaveType type
        -WaveStrategy strategy
        -WaveStatus status
        -LocalDateTime plannedRelease
        -LocalDateTime actualRelease
        -Integer priority
        -List~Order~ orders
        -WaveMetrics metrics
        +create() Wave
        +addOrder(Order) void
        +removeOrder(String) void
        +optimize() void
        +release() void
        +cancel(String) void
        +complete() void
        +calculateMetrics() WaveMetrics
        +validate() boolean
    }

    class Order {
        -String orderId
        -String customerId
        -OrderType type
        -OrderPriority priority
        -LocalDateTime orderDate
        -LocalDateTime requiredDate
        -Address shippingAddress
        -List~OrderLine~ orderLines
        -OrderStatus status
        -ShippingMethod shippingMethod
        +validate() boolean
        +allocateInventory() void
        +calculateWeight() BigDecimal
        +calculateVolume() BigDecimal
    }

    class OrderLine {
        -String lineId
        -String productId
        -String description
        -Integer quantity
        -Integer allocatedQuantity
        -String uom
        -BigDecimal weight
        -BigDecimal volume
        -LineStatus status
        +allocate(int) void
        +pick(int) void
        +cancel() void
    }

    class WaveStrategy {
        <<enumeration>>
        TIME_BASED
        ORDER_COUNT_BASED
        VOLUME_BASED
        PRIORITY_BASED
        ZONE_BASED
        CARRIER_BASED
    }

    class WaveStatus {
        <<enumeration>>
        DRAFT
        PLANNED
        RELEASED
        IN_PROGRESS
        COMPLETED
        CANCELLED
    }

    class WaveMetrics {
        -Integer totalOrders
        -Integer totalLines
        -Integer totalUnits
        -BigDecimal totalWeight
        -BigDecimal totalVolume
        -Double fillRate
        -LocalDateTime estimatedCompletion
        -Integer estimatedPickers
    }

    class WaveOptimizer {
        -OptimizationStrategy strategy
        +optimize(Wave) Wave
        +calculatePickDensity(Wave) Double
        +balanceWorkload(Wave) void
        +minimizeTravelDistance(Wave) void
        +prioritizeBySLA(Wave) void
    }

    class WaveRepository {
        <<interface>>
        +save(Wave) Wave
        +findById(String) Optional~Wave~
        +findByStatus(WaveStatus) List~Wave~
        +findPlannedWaves() List~Wave~
    }

    class WaveService {
        -WaveRepository repository
        -WaveOptimizer optimizer
        -EventPublisher eventPublisher
        +createWave(CreateWaveRequest) Wave
        +releaseWave(String) Wave
        +cancelWave(String, String) void
        +optimizeWave(String) Wave
        +getWaveMetrics(String) WaveMetrics
    }

    Wave "1" --> "*" Order : contains
    Order "1" --> "*" OrderLine : has
    Wave --> WaveStatus : has
    Wave --> WaveStrategy : uses
    Wave --> WaveMetrics : tracks
    WaveService --> WaveRepository : uses
    WaveService --> WaveOptimizer : uses
    WaveOptimizer --> Wave : optimizes
```

---

## Task Execution Domain Model

```mermaid
classDiagram
    class Task {
        -String taskId
        -String waveId
        -TaskType type
        -TaskPriority priority
        -TaskStatus status
        -String assignedTo
        -LocalDateTime createdAt
        -LocalDateTime startedAt
        -LocalDateTime completedAt
        -Location location
        -List~TaskItem~ items
        -TaskMetrics metrics
        +create() Task
        +assign(String) void
        +start() void
        +complete() void
        +pause() void
        +resume() void
        +cancel(String) void
        +addItem(TaskItem) void
        +calculatePriority() Integer
        +estimateDuration() Duration
    }

    class TaskItem {
        -String itemId
        -String productId
        -Integer quantity
        -Integer completedQuantity
        -String locationId
        -ItemStatus status
        +pick(int) void
        +complete() void
        +reportShortage(int) void
    }

    class TaskType {
        <<enumeration>>
        PICKING
        PUTAWAY
        REPLENISHMENT
        CYCLE_COUNT
        MOVE
    }

    class TaskPriority {
        <<enumeration>>
        CRITICAL
        HIGH
        MEDIUM
        LOW
    }

    class TaskStatus {
        <<enumeration>>
        CREATED
        QUEUED
        ASSIGNED
        IN_PROGRESS
        PAUSED
        COMPLETED
        CANCELLED
    }

    class TaskQueue {
        -String queueId
        -QueueType type
        -List~Task~ tasks
        -QueueStrategy strategy
        +enqueue(Task) void
        +dequeue() Task
        +peek() Task
        +reorder() void
        +size() Integer
        +clear() void
    }

    class TaskScheduler {
        -List~TaskQueue~ queues
        -SchedulingStrategy strategy
        +schedule(Task) void
        +getNextTask(String) Task
        +reschedule(Task) void
        +optimizeSchedule() void
        +balanceQueues() void
    }

    class TaskAssignmentEngine {
        -AssignmentStrategy strategy
        -WorkloadService workloadService
        +assignTask(Task, List~Operator~) String
        +findBestOperator(Task) Operator
        +reassignTask(Task) void
        +balanceAssignments() void
    }

    class Operator {
        -String operatorId
        -String name
        -OperatorStatus status
        -List~String~ skills
        -Location currentLocation
        -Integer activeTaskCount
        -Performance performance
        +isAvailable() boolean
        +hasSkill(String) boolean
        +distanceTo(Location) Double
    }

    class TaskRepository {
        <<interface>>
        +save(Task) Task
        +findById(String) Optional~Task~
        +findByWaveId(String) List~Task~
        +findByAssignedTo(String) List~Task~
        +findPendingTasks() List~Task~
    }

    class TaskService {
        -TaskRepository repository
        -TaskScheduler scheduler
        -TaskAssignmentEngine assignmentEngine
        -EventPublisher eventPublisher
        +createTask(CreateTaskRequest) Task
        +assignTask(String) Task
        +startTask(String) void
        +completeTask(String) void
        +getNextTask(String) Task
    }

    Task "1" --> "*" TaskItem : contains
    Task --> TaskType : is
    Task --> TaskPriority : has
    Task --> TaskStatus : has
    TaskQueue "1" --> "*" Task : holds
    TaskScheduler "1" --> "*" TaskQueue : manages
    TaskAssignmentEngine --> Operator : assigns to
    TaskService --> TaskRepository : uses
    TaskService --> TaskScheduler : uses
    TaskService --> TaskAssignmentEngine : uses
```

---

## Pick Execution Domain Model

```mermaid
classDiagram
    class PickSession {
        -String sessionId
        -String operatorId
        -String waveId
        -SessionType type
        -SessionStatus status
        -LocalDateTime startTime
        -LocalDateTime endTime
        -List~PickTask~ pickTasks
        -PickPath optimizedPath
        -PickMetrics metrics
        +create() PickSession
        +start() void
        +addPick(PickTask) void
        +completePick(String) void
        +reportShortage(String, int) void
        +pause() void
        +resume() void
        +complete() void
        +optimizePath() void
    }

    class PickTask {
        -String pickId
        -String taskId
        -String locationId
        -String productId
        -Integer quantity
        -Integer pickedQuantity
        -PickStatus status
        -LocalDateTime pickTime
        -List~PickException~ exceptions
        +pick(int) void
        +confirmLocation() void
        +confirmItem() void
        +reportException(PickException) void
    }

    class PickPath {
        -List~PathNode~ nodes
        -Double totalDistance
        -Duration estimatedTime
        -PathStrategy strategy
        +optimize() void
        +getNext() PathNode
        +recalculate() void
    }

    class PathNode {
        -String locationId
        -Location coordinates
        -Integer sequence
        -List~PickTask~ tasks
        -Double distanceToNext
        +getItems() List~String~
        +getTotalQuantity() Integer
    }

    class PickOptimizer {
        -TSPSolver tspSolver
        -TwoOptSolver twoOptSolver
        +optimizePath(List~PickTask~) PickPath
        +calculateDistance(Location, Location) Double
        +estimateTravelTime(PickPath) Duration
    }

    class PickException {
        -String exceptionId
        -ExceptionType type
        -String reason
        -LocalDateTime timestamp
        -Resolution resolution
    }

    class ExceptionType {
        <<enumeration>>
        ITEM_NOT_FOUND
        WRONG_QUANTITY
        DAMAGED_ITEM
        LOCATION_EMPTY
        BARCODE_UNREADABLE
    }

    class PickStatus {
        <<enumeration>>
        PENDING
        IN_PROGRESS
        PICKED
        CONFIRMED
        SHORT
        EXCEPTION
    }

    class BatchPicking {
        -String batchId
        -List~PickSession~ sessions
        -BatchStrategy strategy
        -Container container
        +addSession(PickSession) void
        +optimizeBatch() void
        +split() List~PickSession~
    }

    class ZonePicking {
        -String zoneId
        -List~PickSession~ sessions
        -Zone zone
        +filterByZone(List~PickTask~) List~PickTask~
        +handoff() void
    }

    PickSession "1" --> "*" PickTask : contains
    PickSession --> PickPath : follows
    PickPath "1" --> "*" PathNode : consists of
    PathNode "1" --> "*" PickTask : groups
    PickTask --> PickStatus : has
    PickTask "1" --> "*" PickException : may have
    PickException --> ExceptionType : is
    PickOptimizer --> PickPath : creates
    BatchPicking "1" --> "*" PickSession : batches
    ZonePicking "1" --> "*" PickSession : zones
```

---

## Location Master Domain Model

```mermaid
classDiagram
    class LocationMaster {
        -String locationId
        -String warehouseId
        -String name
        -LocationType type
        -String parentLocationId
        -Integer hierarchyLevel
        -String zone
        -LocationStatus status
        -Dimensions dimensions
        -Capacity capacity
        -Restrictions restrictions
        -SlottingClass slottingClass
        -Integer pickPathSequence
        -Coordinates coordinates
        -Map~String,String~ attributes
        +create() LocationMaster
        +block(String) void
        +unblock() void
        +reserve(String) void
        +releaseReservation() void
        +markAsFull() void
        +markAsAvailable() void
        +configureDimensions(Dimensions) void
        +configureCapacity(Capacity) void
        +setSlottingClass(SlottingClass) void
        +validateHierarchy() boolean
    }

    class LocationType {
        <<enumeration>>
        WAREHOUSE
        ZONE
        AISLE
        BAY
        LEVEL
        BIN
        STAGING
        DOCK
    }

    class LocationStatus {
        <<enumeration>>
        ACTIVE
        BLOCKED
        RESERVED
        FULL
        MAINTENANCE
        DECOMMISSIONED
    }

    class Dimensions {
        -BigDecimal length
        -BigDecimal width
        -BigDecimal height
        -String unitOfMeasure
        +getVolume() BigDecimal
        +canFit(Dimensions) boolean
    }

    class Capacity {
        -Integer maxItems
        -BigDecimal maxWeight
        -BigDecimal maxVolume
        -String weightUom
        -String volumeUom
        -Integer currentItems
        -BigDecimal currentWeight
        -BigDecimal currentVolume
        +hasCapacity(int, BigDecimal, BigDecimal) boolean
        +utilize(int, BigDecimal, BigDecimal) void
        +release(int, BigDecimal, BigDecimal) void
        +getUtilization() Double
    }

    class Restrictions {
        -Boolean hazmatAllowed
        -Boolean foodGradeOnly
        -Boolean climateControlled
        -TemperatureRange temperatureRange
        -List~String~ allowedCategories
        -List~String~ prohibitedCategories
        +canStore(Product) boolean
        +addRestriction(String) void
    }

    class SlottingClass {
        <<enumeration>>
        FAST_MOVER
        MEDIUM_MOVER
        SLOW_MOVER
        VERY_SLOW_MOVER
        SEASONAL
        PROMOTIONAL
    }

    class Coordinates {
        -Double x
        -Double y
        -Double z
        -String aisle
        -String bay
        -String level
        -String position
        +distanceTo(Coordinates) Double
        +getPhysicalAddress() String
    }

    class SlottingOptimizer {
        -OptimizationCriteria criteria
        +optimizeSlotting(List~LocationMaster~) void
        +suggestLocation(Product) LocationMaster
        +rebalanceZone(String) void
        +identifyGoldenZone() List~LocationMaster~
    }

    class LocationHierarchy {
        -LocationMaster root
        -Map~String, List~LocationMaster~~ children
        +addLocation(LocationMaster) void
        +getChildren(String) List~LocationMaster~
        +getPath(String) String
        +validateStructure() boolean
    }

    LocationMaster --> LocationType : is
    LocationMaster --> LocationStatus : has
    LocationMaster --> Dimensions : has
    LocationMaster --> Capacity : manages
    LocationMaster --> Restrictions : enforces
    LocationMaster --> SlottingClass : classified as
    LocationMaster --> Coordinates : located at
    LocationHierarchy "1" --> "*" LocationMaster : organizes
    SlottingOptimizer --> LocationMaster : optimizes
```

---

## Pack & Ship Domain Model

```mermaid
classDiagram
    class PackingSession {
        -String sessionId
        -String orderId
        -String operatorId
        -SessionStatus status
        -LocalDateTime startTime
        -LocalDateTime endTime
        -List~PackItem~ items
        -Carton carton
        -PackingList packingList
        -QualityCheck qualityCheck
        -ShippingLabel label
        +create() PackingSession
        +addItem(PackItem) void
        +selectCarton() Carton
        +performQualityCheck() QualityCheck
        +generateLabel() ShippingLabel
        +complete() void
    }

    class PackItem {
        -String itemId
        -String productId
        -Integer quantity
        -ItemCondition condition
        -Boolean fragile
        -Boolean requiresPadding
        -Dimensions dimensions
        -BigDecimal weight
        +inspect() ItemCondition
        +pack() void
    }

    class Carton {
        -String cartonId
        -CartonType type
        -Dimensions dimensions
        -BigDecimal maxWeight
        -BigDecimal tareWeight
        -List~PackItem~ packedItems
        -PackingMaterial materials
        +canFit(PackItem) boolean
        +addItem(PackItem) void
        +calculateDimensionalWeight() BigDecimal
        +seal() void
    }

    class CartonSelector {
        -List~CartonType~ availableTypes
        -SelectionStrategy strategy
        +selectOptimalCarton(List~PackItem~) Carton
        +calculateFillRate(Carton) Double
        +suggestAlternatives(Carton) List~Carton~
    }

    class QualityCheck {
        -String checkId
        -CheckType type
        -CheckStatus status
        -List~QualityCheckPoint~ checkPoints
        -String performedBy
        -LocalDateTime checkTime
        -String notes
        +perform() CheckStatus
        +addCheckPoint(QualityCheckPoint) void
        +fail(String) void
        +pass() void
    }

    class ShippingLabel {
        -String trackingNumber
        -Carrier carrier
        -ServiceType service
        -Address fromAddress
        -Address toAddress
        -BigDecimal weight
        -Dimensions dimensions
        -String barcode
        -byte[] labelData
        +generate() byte[]
        +print() void
        +void cancel()
    }

    class ShipmentManifest {
        -String manifestId
        -Carrier carrier
        -LocalDate shipDate
        -List~Shipment~ shipments
        -ManifestStatus status
        +addShipment(Shipment) void
        +close() void
        +transmit() void
        +print() byte[]
    }

    class Carrier {
        -String carrierId
        -String name
        -List~ServiceType~ services
        -Integration integration
        +getRates(RateRequest) List~Rate~
        +bookShipment(ShipmentRequest) String
        +trackShipment(String) TrackingInfo
        +printLabel(String) byte[]
    }

    class DockScheduler {
        -List~DockDoor~ doors
        -List~Appointment~ appointments
        +schedulePickup(Shipment) Appointment
        +assignDoor(Shipment) DockDoor
        +optimizeSchedule() void
    }

    PackingSession "1" --> "*" PackItem : packs
    PackingSession --> Carton : uses
    PackingSession --> QualityCheck : performs
    PackingSession --> ShippingLabel : generates
    Carton "1" --> "*" PackItem : contains
    CartonSelector --> Carton : selects
    ShipmentManifest "1" --> "*" PackingSession : includes
    ShipmentManifest --> Carrier : for
    Carrier --> ShippingLabel : creates
    DockScheduler --> ShipmentManifest : schedules
```

---

## Physical Tracking Domain Model

```mermaid
classDiagram
    class LicensePlate {
        -String lpId
        -String sscc
        -LPType type
        -LPStatus status
        -Location currentLocation
        -List~InventoryItem~ contents
        -LocalDateTime createdAt
        -LocalDateTime lastMoved
        -Map~String,String~ attributes
        +create() LicensePlate
        +addItem(InventoryItem) void
        +removeItem(String) void
        +move(Location) void
        +nest(LicensePlate) void
        +consolidate(List~LicensePlate~) void
        +split() List~LicensePlate~
        +close() void
    }

    class InventoryItem {
        -String itemId
        -String productId
        -String lotNumber
        -String serialNumber
        -Integer quantity
        -ItemStatus status
        -LocalDateTime expiryDate
        -LocalDateTime receivedDate
        -Map~String,String~ attributes
        +adjust(int) void
        +transfer(LicensePlate) void
        +quarantine() void
        +release() void
    }

    class InventoryTransaction {
        -String transactionId
        -TransactionType type
        -String itemId
        -String fromLocation
        -String toLocation
        -Integer quantity
        -String reason
        -String performedBy
        -LocalDateTime timestamp
        +execute() void
        +reverse() void
    }

    class TransactionType {
        <<enumeration>>
        RECEIPT
        PUTAWAY
        PICK
        MOVE
        ADJUSTMENT
        CYCLE_COUNT
        RETURN
        SCRAP
    }

    class MovementTracker {
        -List~Movement~ movements
        +trackMovement(LicensePlate, Location, Location) void
        +getMovementHistory(String) List~Movement~
        +calculateDistance(String) Double
        +getHeatmap() HeatmapData
    }

    class Movement {
        -String movementId
        -String lpId
        -Location fromLocation
        -Location toLocation
        -LocalDateTime timestamp
        -String movedBy
        -MovementType type
        -String reason
    }

    class CycleCount {
        -String countId
        -CountType type
        -Location location
        -List~CountLine~ countLines
        -CountStatus status
        -LocalDateTime scheduledDate
        -LocalDateTime countedDate
        -String countedBy
        -Double accuracy
        +addCountLine(CountLine) void
        +submitCount() void
        +approve() void
        +createAdjustments() List~InventoryTransaction~
    }

    class CountLine {
        -String productId
        -Integer expectedQty
        -Integer countedQty
        -Integer variance
        -String lpId
        -CountLineStatus status
        +calculateVariance() Integer
        +requiresRecount() boolean
    }

    class InventorySnapshot {
        -LocalDateTime timestamp
        -Map~String, InventoryLevel~ levels
        -Map~String, LocationUtilization~ utilization
        -InventoryMetrics metrics
        +capture() void
        +compare(InventorySnapshot) InventoryDelta
        +export() byte[]
    }

    LicensePlate "1" --> "*" InventoryItem : contains
    InventoryItem --> InventoryTransaction : creates
    InventoryTransaction --> TransactionType : is
    MovementTracker "1" --> "*" Movement : tracks
    Movement --> LicensePlate : moves
    CycleCount "1" --> "*" CountLine : has
    CountLine --> InventoryItem : counts
    InventorySnapshot --> InventoryItem : snapshots
```

---

## Entity Relationships

Complete entity relationship diagram across all services.

```mermaid
erDiagram
    WAVE ||--o{ ORDER : contains
    ORDER ||--o{ ORDER_LINE : has
    WAVE ||--o{ TASK : generates
    TASK ||--o{ TASK_ITEM : includes
    TASK ||--|| PICK_SESSION : creates
    PICK_SESSION ||--o{ PICK_TASK : executes
    PICK_TASK }o--|| LOCATION : at
    LOCATION }o--|| LOCATION : "parent of"
    ORDER_LINE ||--|| PACK_ITEM : becomes
    PACK_SESSION ||--o{ PACK_ITEM : packs
    PACK_SESSION ||--|| CARTON : uses
    PACK_SESSION ||--|| SHIPPING_LABEL : generates
    LICENSE_PLATE ||--o{ INVENTORY_ITEM : contains
    INVENTORY_ITEM }o--|| LOCATION : "stored at"
    INVENTORY_ITEM }o--|| PRODUCT : "instance of"
    CYCLE_COUNT ||--o{ COUNT_LINE : verifies
    COUNT_LINE }o--|| INVENTORY_ITEM : counts

    WAVE {
        string wave_id PK
        string warehouse_id FK
        string wave_type
        string status
        timestamp planned_release
        timestamp actual_release
        integer priority
    }

    ORDER {
        string order_id PK
        string wave_id FK
        string customer_id
        string order_type
        string status
        timestamp order_date
        timestamp required_date
    }

    TASK {
        string task_id PK
        string wave_id FK
        string task_type
        string status
        string assigned_to FK
        timestamp created_at
        timestamp completed_at
    }

    LOCATION {
        string location_id PK
        string warehouse_id FK
        string parent_id FK
        string location_type
        string zone
        string status
        decimal capacity
    }

    LICENSE_PLATE {
        string lp_id PK
        string sscc
        string location_id FK
        string status
        timestamp created_at
        timestamp last_moved
    }

    INVENTORY_ITEM {
        string item_id PK
        string product_id FK
        string lp_id FK
        string lot_number
        integer quantity
        string status
        timestamp expiry_date
    }
```

---

## Value Objects

Shared value objects across domains.

```mermaid
classDiagram
    class Money {
        -BigDecimal amount
        -Currency currency
        +add(Money) Money
        +subtract(Money) Money
        +multiply(BigDecimal) Money
        +equals(Money) boolean
    }

    class Address {
        -String line1
        -String line2
        -String city
        -String state
        -String postalCode
        -String country
        +format() String
        +validate() boolean
    }

    class Weight {
        -BigDecimal value
        -WeightUnit unit
        +convertTo(WeightUnit) Weight
        +add(Weight) Weight
        +compareTo(Weight) int
    }

    class Volume {
        -BigDecimal value
        -VolumeUnit unit
        +convertTo(VolumeUnit) Volume
        +add(Volume) Volume
        +fromDimensions(Dimensions) Volume
    }

    class Temperature {
        -BigDecimal value
        -TemperatureUnit unit
        +convertTo(TemperatureUnit) Temperature
        +inRange(TemperatureRange) boolean
    }

    class DateTimeRange {
        -LocalDateTime start
        -LocalDateTime end
        +contains(LocalDateTime) boolean
        +overlaps(DateTimeRange) boolean
        +duration() Duration
    }

    class Barcode {
        -String value
        -BarcodeType type
        +validate() boolean
        +encode() byte[]
        +decode(byte[]) String
    }

    class Percentage {
        -BigDecimal value
        +of(BigDecimal) BigDecimal
        +add(Percentage) Percentage
        +complement() Percentage
    }
```

---

## Domain Events

Event-driven architecture with domain events.

```mermaid
classDiagram
    class DomainEvent {
        <<abstract>>
        -String eventId
        -String aggregateId
        -LocalDateTime occurredAt
        -String eventType
        -Integer version
        +toCloudEvent() CloudEvent
    }

    class WaveEvent {
        <<abstract>>
        -String waveId
        -String warehouseId
    }

    class WaveCreated {
        -WaveDetails details
    }

    class WaveReleased {
        -List~String~ orderIds
        -Integer taskCount
    }

    class WaveCompleted {
        -WaveMetrics metrics
        -Duration duration
    }

    class TaskEvent {
        <<abstract>>
        -String taskId
        -String waveId
    }

    class TaskCreated {
        -TaskDetails details
        -Location location
    }

    class TaskAssigned {
        -String operatorId
        -LocalDateTime assignedAt
    }

    class TaskCompleted {
        -TaskMetrics metrics
        -List~TaskItem~ items
    }

    class InventoryEvent {
        <<abstract>>
        -String itemId
        -String locationId
    }

    class InventoryMoved {
        -String fromLocation
        -String toLocation
        -Integer quantity
    }

    class InventoryAdjusted {
        -Integer oldQuantity
        -Integer newQuantity
        -String reason
    }

    class LocationEvent {
        <<abstract>>
        -String locationId
    }

    class LocationBlocked {
        -String reason
        -String blockedBy
    }

    class LocationCapacityChanged {
        -Capacity oldCapacity
        -Capacity newCapacity
    }

    DomainEvent <|-- WaveEvent
    DomainEvent <|-- TaskEvent
    DomainEvent <|-- InventoryEvent
    DomainEvent <|-- LocationEvent

    WaveEvent <|-- WaveCreated
    WaveEvent <|-- WaveReleased
    WaveEvent <|-- WaveCompleted

    TaskEvent <|-- TaskCreated
    TaskEvent <|-- TaskAssigned
    TaskEvent <|-- TaskCompleted

    InventoryEvent <|-- InventoryMoved
    InventoryEvent <|-- InventoryAdjusted

    LocationEvent <|-- LocationBlocked
    LocationEvent <|-- LocationCapacityChanged
```