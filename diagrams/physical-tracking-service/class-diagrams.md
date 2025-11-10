# Physical Tracking Service - Class Diagrams

## Domain Model Overview

```mermaid
classDiagram
    class LicensePlate {
        <<Aggregate Root>>
        -String licensePlateId
        -LPType type
        -LPStatus status
        -String parentLPId
        -List~LPContent~ contents
        -Location currentLocation
        -Container container
        -DateTime createdAt
        -DateTime lastMovedAt
        -List~Movement~ movementHistory
        -LPAttributes attributes
        +create(type) void
        +addContent(item, quantity) void
        +removeContent(item, quantity) void
        +moveTo(location) Movement
        +nest(parentLP) void
        +unnest() void
        +consolidate(otherLP) void
        +split(criteria) List~LicensePlate~
        +close() void
        +validate() ValidationResult
    }

    class LPContent {
        <<Entity>>
        -String contentId
        -String itemId
        -String skuCode
        -int quantity
        -LotNumber lotNumber
        -SerialNumber serialNumber
        -ExpirationDate expirationDate
        -ContentStatus status
        +adjust(quantity) void
        +transfer(targetLP, quantity) void
        +validate() boolean
    }

    class Movement {
        <<Entity>>
        -String movementId
        -String licensePlateId
        -Location fromLocation
        -Location toLocation
        -MovementType type
        -MovementStatus status
        -String performedBy
        -DateTime startTime
        -DateTime endTime
        -MovementReason reason
        -List~MovementDetail~ details
        +execute() void
        +complete() void
        +cancel(reason) void
        +validate() boolean
    }

    class Location {
        <<Value Object>>
        -String locationId
        -String warehouseId
        -String zone
        -String aisle
        -String bay
        -String level
        -String position
        -LocationType type
        -Coordinates coordinates
        -LocationStatus status
        +getFullPath() String
        +isAvailable() boolean
        +calculateDistance(other) Distance
    }

    class PhysicalInventory {
        <<Entity>>
        -String inventoryId
        -String locationId
        -Map~String, Integer~ itemQuantities
        -List~LicensePlate~ licensePlates
        -DateTime lastUpdated
        -InventoryStatus status
        +addLP(licensePlate) void
        +removeLP(licensePlateId) void
        +updateQuantity(item, quantity) void
        +reconcile(expected) ReconciliationResult
    }

    LicensePlate "1" --> "*" LPContent : contains
    LicensePlate "1" --> "*" Movement : tracks
    LicensePlate "1" --> "1" Location : at
    Movement "1" --> "2" Location : from/to
    PhysicalInventory "1" --> "*" LicensePlate : tracks
```

## RTLS Integration

```mermaid
classDiagram
    class RTLSIntegrationService {
        <<Integration Service>>
        -RTLSProvider provider
        -TagManager tagManager
        -PositionCalculator calculator
        +trackAsset(tagId) Position
        +trackMultiple(tagIds) Map~String, Position~
        +registerTag(tag, asset) void
        +updatePosition(tagId, position) void
        +getMovementHistory(tagId, period) List~Movement~
        -triangulatePosition(signals) Position
    }

    class RFIDTag {
        <<Entity>>
        -String tagId
        -TagType type
        -String assignedTo
        -TagStatus status
        -BatteryLevel battery
        -SignalStrength signal
        -DateTime lastSeen
        -Position lastPosition
        +activate() void
        +deactivate() void
        +assignTo(assetId) void
        +updatePosition(position) void
    }

    class PositionTracker {
        <<Domain Service>>
        -Map~String, Position~ currentPositions
        -GeofenceManager geofences
        -MovementDetector detector
        +updatePosition(assetId, position) void
        +detectMovement(assetId) Movement
        +checkGeofence(position) GeofenceEvent
        +predictPath(assetId) PredictedPath
        -calculateVelocity(positions) Velocity
    }

    class GeofenceManager {
        <<Service>>
        -List~Geofence~ geofences
        +createGeofence(boundary, rules) Geofence
        +checkViolation(position) Violation
        +getActiveGeofences(location) List~Geofence~
        +updateRules(geofenceId, rules) void
    }

    class IndoorPositioningSystem {
        <<Service>>
        -List~Beacon~ beacons
        -SignalProcessor processor
        -MapService mapService
        +calculatePosition(signals) Position
        +calibrate(knownPositions) void
        +getFloorMap(floor) FloorMap
        -processSignals(signals) ProcessedData
    }

    RTLSIntegrationService --> RFIDTag : manages
    RTLSIntegrationService --> PositionTracker : updates
    PositionTracker --> GeofenceManager : uses
    RTLSIntegrationService --> IndoorPositioningSystem : uses
```

## Movement Orchestration

```mermaid
classDiagram
    class MovementOrchestrator {
        <<Domain Service>>
        -MovementValidator validator
        -PathOptimizer optimizer
        -ConflictResolver resolver
        +orchestrateMovement(request) Movement
        +planBulkMovement(items) MovementPlan
        +optimizeRoute(movements) OptimalRoute
        -validateMovement(from, to) ValidationResult
        -checkConflicts(movement) List~Conflict~
        -resolveConflicts(conflicts) Resolution
    }

    class MovementValidator {
        <<Service>>
        -List~ValidationRule~ rules
        -CapacityChecker capacity
        -PermissionChecker permissions
        +validate(movement) ValidationResult
        -checkLocationAvailability(location) boolean
        -checkCapacityLimits(location, items) boolean
        -checkPermissions(user, movement) boolean
    }

    class TransferManager {
        <<Domain Service>>
        -TransferStrategy strategy
        -InventoryUpdater updater
        +transfer(from, to, items) TransferResult
        +bulkTransfer(transfers) BulkResult
        +crossDock(inbound, outbound) void
        -selectStrategy(transfer) TransferStrategy
        -updateInventory(transfer) void
    }

    class ConsolidationService {
        <<Domain Service>>
        -ConsolidationRules rules
        -MergeStrategy strategy
        +consolidate(licensePlates) LicensePlate
        +deconsolidate(licensePlate) List~LicensePlate~
        +optimize(licensePlates) ConsolidationPlan
        -canConsolidate(lps) boolean
        -mergeContents(contents) List~LPContent~
    }

    MovementOrchestrator --> MovementValidator : uses
    MovementOrchestrator --> TransferManager : delegates
    TransferManager --> ConsolidationService : may use
```

## Location State Management

```mermaid
classDiagram
    class LocationStateManager {
        <<Domain Service>>
        -Map~String, LocationState~ states
        -StateTransitionValidator validator
        -EventPublisher publisher
        +updateState(locationId, newState) void
        +getState(locationId) LocationState
        +blockLocation(locationId, reason) void
        +unblockLocation(locationId) void
        +reserveLocation(locationId, duration) Reservation
        -validateTransition(from, to) boolean
        -publishStateChange(location, oldState, newState) void
    }

    class LocationState {
        <<Entity>>
        -String locationId
        -OccupancyStatus occupancy
        -int currentCapacity
        -int maxCapacity
        -List~String~ licensePlates
        -LocationStatus status
        -BlockReason blockReason
        -DateTime lastActivity
        -Temperature temperature
        -Humidity humidity
        +occupy(licensePlate) void
        +vacate(licensePlate) void
        +updateEnvironment(temp, humidity) void
        +isFull() boolean
    }

    class CapacityTracker {
        <<Service>>
        -Map~String, Capacity~ capacities
        +checkAvailability(location) boolean
        +calculateUtilization(location) Percentage
        +findAvailableLocation(criteria) Location
        +reserveCapacity(location, amount) void
        +releaseCapacity(location, amount) void
    }

    class LocationHierarchy {
        <<Entity>>
        -TreeStructure hierarchy
        -Map~String, LocationNode~ nodes
        +getParent(location) Location
        +getChildren(location) List~Location~
        +getPath(from, to) List~Location~
        +aggregateCapacity(location) Capacity
    }

    LocationStateManager --> LocationState : manages
    LocationStateManager --> CapacityTracker : uses
    LocationStateManager --> LocationHierarchy : navigates
```

## Audit and Tracking

```mermaid
classDiagram
    class AuditTrailService {
        <<Service>>
        -AuditRepository repository
        -EventSerializer serializer
        +recordMovement(movement) void
        +recordStateChange(change) void
        +getHistory(entityId, period) List~AuditEntry~
        +generateAuditReport(criteria) Report
        -createAuditEntry(event) AuditEntry
    }

    class AuditEntry {
        <<Entity>>
        -String auditId
        -String entityId
        -EntityType entityType
        -ActionType action
        -String performedBy
        -DateTime performedAt
        -Map~String, Object~ beforeState
        -Map~String, Object~ afterState
        -String reason
        +toJson() String
        +getDiff() List~Change~
    }

    class TrackingHistory {
        <<Entity>>
        -String trackingId
        -String licensePlateId
        -List~TrackingPoint~ points
        -DateTime startTime
        -DateTime endTime
        -Distance totalDistance
        -List~Stop~ stops
        +addPoint(point) void
        +calculateDistance() Distance
        +identifyStops(threshold) List~Stop~
    }

    class ChainOfCustody {
        <<Entity>>
        -String custodyId
        -String itemId
        -List~CustodyTransfer~ transfers
        -String currentCustodian
        -CustodyStatus status
        +transfer(from, to, reason) void
        +verify(custodian) boolean
        +getChain() List~CustodyRecord~
    }

    AuditTrailService --> AuditEntry : creates
    AuditTrailService --> TrackingHistory : maintains
    TrackingHistory --> ChainOfCustody : ensures
```

## Domain Events

```mermaid
classDiagram
    class PhysicalTrackingEvent {
        <<Abstract Event>>
        -String eventId
        -String entityId
        -DateTime occurredAt
        +getEventType() String
    }

    class LicensePlateCreatedEvent {
        <<Event>>
        -String licensePlateId
        -LPType type
        -Location location
        +getEventType() String
    }

    class MovementCompletedEvent {
        <<Event>>
        -String movementId
        -String licensePlateId
        -Location from
        -Location to
        -Duration duration
        +getEventType() String
    }

    class LocationStateChangedEvent {
        <<Event>>
        -String locationId
        -LocationState oldState
        -LocationState newState
        -String reason
        +getEventType() String
    }

    class InventoryAdjustedEvent {
        <<Event>>
        -String locationId
        -String itemId
        -int oldQuantity
        -int newQuantity
        -AdjustmentReason reason
        +getEventType() String
    }

    class GeofenceViolationEvent {
        <<Event>>
        -String assetId
        -String geofenceId
        -ViolationType type
        -Position position
        +getEventType() String
    }

    PhysicalTrackingEvent <|-- LicensePlateCreatedEvent
    PhysicalTrackingEvent <|-- MovementCompletedEvent
    PhysicalTrackingEvent <|-- LocationStateChangedEvent
    PhysicalTrackingEvent <|-- InventoryAdjustedEvent
    PhysicalTrackingEvent <|-- GeofenceViolationEvent
```

## Integration Services

```mermaid
classDiagram
    class PhysicalTrackingAPI {
        <<API Controller>>
        -LicensePlateService lpService
        -MovementService movementService
        -LocationService locationService
        +createLP(request) Response
        +moveLP(lpId, request) Response
        +getLocation(lpId) Response
        +trackMovement(movementId) Response
    }

    class WarehouseMapService {
        <<Service>>
        -MapRepository maps
        -VisualizationEngine engine
        +getWarehouseMap(warehouseId) Map
        +visualizeMovements(period) Visualization
        +generateHeatMap(metric) HeatMap
        +show3DView(warehouseId) Model3D
    }

    class SensorIntegrationService {
        <<Integration Service>>
        -List~SensorAdapter~ sensors
        -DataProcessor processor
        +collectSensorData() SensorData
        +processEnvironmental(data) Environmental
        +detectAnomalies(data) List~Anomaly~
        +calibrateSensors() CalibrationResult
    }

    PhysicalTrackingAPI --> WarehouseMapService : uses
    PhysicalTrackingAPI --> SensorIntegrationService : integrates
```