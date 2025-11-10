# Pick Execution Service - Class Diagrams

## Domain Model Overview

```mermaid
classDiagram
    class PickSession {
        <<Aggregate Root>>
        -String sessionId
        -String pickerId
        -String waveId
        -PickStrategy strategy
        -SessionStatus status
        -List~PickList~ pickLists
        -PickPath optimizedPath
        -PickCart cart
        -DateTime startTime
        -DateTime endTime
        -PickMetrics metrics
        -List~PickConfirmation~ confirmations
        +start() void
        +pause(reason) void
        +resume() void
        +complete() void
        +addPickList(pickList) void
        +optimizePath() void
        +confirmPick(pickId, quantity) void
        +reportShortage(pickId, available) void
        +skipPick(pickId, reason) void
        +calculateProgress() Progress
    }

    class PickList {
        <<Entity>>
        -String pickListId
        -String orderId
        -List~PickLine~ lines
        -PickPriority priority
        -DateTime dueTime
        -PickListStatus status
        +addLine(line) void
        +removeLine(lineId) void
        +markPicked(lineId) void
        +calculateCompletion() Percentage
        +validate() boolean
    }

    class PickLine {
        <<Entity>>
        -String lineId
        -String skuCode
        -String productName
        -PickLocation location
        -int requestedQuantity
        -int pickedQuantity
        -String unitOfMeasure
        -PickLineStatus status
        -List~PickAttribute~ attributes
        +pick(quantity) void
        +partial(quantity) void
        +skip(reason) void
        +substitute(newSku) void
    }

    class PickLocation {
        <<Value Object>>
        -String locationId
        -String zone
        -String aisle
        -String bay
        -String shelf
        -String bin
        -LocationType type
        -Coordinates coordinates
        +getFullPath() String
        +calculateDistance(other) Distance
        +isInZone(zone) boolean
    }

    class PickPath {
        <<Entity>>
        -String pathId
        -List~PathSegment~ segments
        -double totalDistance
        -Duration estimatedTime
        -OptimizationMethod method
        +addSegment(segment) void
        +optimize() void
        +getNextLocation() PickLocation
        +recalculate() void
    }

    class PickStrategy {
        <<Enumeration>>
        DISCRETE
        BATCH
        ZONE
        WAVE
        CLUSTER
        CART_PICK
    }

    PickSession "1" --> "*" PickList : contains
    PickList "1" --> "*" PickLine : contains
    PickLine "1" --> "1" PickLocation : has
    PickSession "1" --> "1" PickPath : follows
    PickSession "1" --> "1" PickStrategy : uses
```

## Path Optimization Engine

```mermaid
classDiagram
    class PathOptimizationEngine {
        <<Domain Service>>
        -WarehouseLayout layout
        -OptimizationAlgorithm algorithm
        -CongestionAnalyzer congestion
        +optimizePath(picks) OptimalPath
        +optimizeBatchPath(sessions) List~OptimalPath~
        -calculateShortestPath(locations) Path
        -avoidCongestion(path) Path
        -considerZoneConstraints(path) Path
    }

    class OptimizationAlgorithm {
        <<Strategy Interface>>
        +optimize(locations) OptimalPath
    }

    class TSPAlgorithm {
        <<Strategy>>
        -HeuristicType heuristic
        +optimize(locations) OptimalPath
        -nearestNeighbor(locations) Path
        -twoOpt(path) Path
        -simulatedAnnealing(path) Path
    }

    class SShapeAlgorithm {
        <<Strategy>>
        +optimize(locations) OptimalPath
        -traverseAisles(locations) Path
        -minimizeBacktracking() void
    }

    class ReturnRouteAlgorithm {
        <<Strategy>>
        +optimize(locations) OptimalPath
        -createReturnPath(locations) Path
        -optimizeReturnTrip() void
    }

    class WarehouseLayout {
        <<Entity>>
        -String warehouseId
        -Graph~Location~ locationGraph
        -List~Zone~ zones
        -List~Aisle~ aisles
        -Map~String, Distance~ distanceMatrix
        +getDistance(from, to) Distance
        +getPath(from, to) List~Location~
        +getZoneLayout(zoneId) ZoneLayout
    }

    class CongestionAnalyzer {
        <<Service>>
        -HeatMap currentHeatMap
        -List~CongestionZone~ congestedAreas
        +analyzeCongestion() CongestionReport
        +predictCongestion(time) List~CongestionZone~
        +suggestAlternativePath(path) Path
    }

    PathOptimizationEngine --> OptimizationAlgorithm : uses
    OptimizationAlgorithm <|.. TSPAlgorithm
    OptimizationAlgorithm <|.. SShapeAlgorithm
    OptimizationAlgorithm <|.. ReturnRouteAlgorithm
    PathOptimizationEngine --> WarehouseLayout : uses
    PathOptimizationEngine --> CongestionAnalyzer : consults
```

## Batch and Zone Picking

```mermaid
classDiagram
    class BatchPickManager {
        <<Domain Service>>
        -BatchingStrategy strategy
        -int maxBatchSize
        -int maxOrders
        +createBatch(orders) PickBatch
        +optimizeBatch(batch) void
        +splitBatch(batch) List~PickBatch~
        -groupOrders(orders) List~OrderGroup~
        -assignToCart(batch) CartAssignment
    }

    class PickBatch {
        <<Entity>>
        -String batchId
        -List~Order~ orders
        -List~PickLocation~ locations
        -BatchStatus status
        -PickCart assignedCart
        -DateTime createdAt
        +addOrder(order) void
        +removeOrder(orderId) void
        +consolidateLocations() void
        +validate() boolean
    }

    class ZonePickCoordinator {
        <<Domain Service>>
        -Map~Zone, ZonePicker~ zonePickers
        -ZoneSequence sequence
        +coordinatePicking(wave) ZonePickPlan
        +assignToZones(picks) Map~Zone, List~Pick~~
        +sequenceZones(zones) List~Zone~
        -balanceZoneWorkload(assignments) void
    }

    class PutWallManager {
        <<Entity>>
        -String putWallId
        -List~PutWallSlot~ slots
        -Map~String, String~ orderSlotMapping
        -PutWallStatus status
        +assignSlot(orderId) SlotNumber
        +putItem(slotNumber, item) void
        +completeOrder(orderId) void
        +clearSlot(slotNumber) void
        +getAvailableSlots() List~PutWallSlot~
    }

    class PutWallSlot {
        <<Entity>>
        -int slotNumber
        -String assignedOrderId
        -List~Item~ items
        -SlotStatus status
        -Indicator lightIndicator
        +addItem(item) void
        +removeItem(itemId) void
        +complete() void
        +clear() void
        +illuminate() void
    }

    class ClusterPicking {
        <<Domain Service>>
        -ClusterStrategy strategy
        -int clusterSize
        +createClusters(orders) List~PickCluster~
        +optimizeCluster(cluster) void
        -groupByProximity(orders) List~OrderGroup~
        -assignToSections(cluster) void
    }

    BatchPickManager --> PickBatch : creates
    ZonePickCoordinator --> PickSession : coordinates
    PutWallManager "1" --> "*" PutWallSlot : manages
    ClusterPicking --> PickBatch : organizes
```

## Pick Confirmation and Validation

```mermaid
classDiagram
    class PickConfirmationService {
        <<Domain Service>>
        -BarcodeValidator barcodeValidator
        -QuantityValidator quantityValidator
        -LocationValidator locationValidator
        +confirmPick(confirmation) ConfirmationResult
        +validateBarcode(barcode, expected) boolean
        +validateQuantity(picked, requested) boolean
        +validateLocation(scanned, expected) boolean
    }

    class PickConfirmation {
        <<Value Object>>
        -String pickLineId
        -String scannedBarcode
        -String scannedLocation
        -int pickedQuantity
        -DateTime confirmedAt
        -String confirmedBy
        -ConfirmationMethod method
        +validate() boolean
    }

    class ShortageHandler {
        <<Domain Service>>
        -ShortagePolicy policy
        -SubstitutionService substitution
        +handleShortage(pick, available) ShortageResolution
        +suggestSubstitute(sku) List~Substitute~
        +allocatePartial(pick, available) PartialAllocation
        +reportShortage(shortage) void
    }

    class PickException {
        <<Entity>>
        -String exceptionId
        -String pickLineId
        -ExceptionType type
        -String description
        -Resolution resolution
        -DateTime reportedAt
        -String reportedBy
        +resolve(resolution) void
        +escalate() void
    }

    class PickAccuracyTracker {
        <<Service>>
        -Map~String, AccuracyMetrics~ operatorMetrics
        -double targetAccuracy
        +recordPick(pick, confirmation) void
        +calculateAccuracy(operatorId) double
        +identifyErrors(period) List~PickError~
        +generateAccuracyReport() Report
    }

    PickConfirmationService --> PickConfirmation : validates
    PickConfirmationService --> ShortageHandler : delegates
    ShortageHandler --> PickException : creates
    PickAccuracyTracker --> PickConfirmation : tracks
```

## Mobile Picking Interface

```mermaid
classDiagram
    class MobilePickingAPI {
        <<API Controller>>
        -PickSessionService sessionService
        -PathService pathService
        +startSession(pickerId) SessionDto
        +getNextPick(sessionId) PickInstructionDto
        +confirmPick(confirmation) ConfirmationResponse
        +reportIssue(issue) IssueResponse
        +completeSession(sessionId) CompletionResponse
    }

    class PickInstruction {
        <<DTO>>
        -String pickLineId
        -String skuCode
        -String productName
        -String productImage
        -LocationDto location
        -int quantity
        -String unitOfMeasure
        -NavigationDto navigation
        +toDisplay() DisplayInstruction
    }

    class VoicePickingService {
        <<Service>>
        -VoiceEngine engine
        -CommandParser parser
        +processVoiceCommand(audio) Command
        +generateVoicePrompt(instruction) AudioPrompt
        +confirmVoicePick(confirmation) VoiceResponse
    }

    class RFScannerIntegration {
        <<Integration Service>>
        -ScannerDriver driver
        -BarcodeDecoder decoder
        +processScan(scanData) ScanResult
        +validateScan(scan, expected) boolean
        +triggerScan() void
    }

    class ARNavigationService {
        <<Service>>
        -AREngine arEngine
        -IndoorPositioning positioning
        +generateARPath(from, to) ARNavigation
        +showPickLocation(location) ARMarker
        +updatePosition(position) void
    }

    MobilePickingAPI --> PickInstruction : returns
    MobilePickingAPI --> VoicePickingService : integrates
    MobilePickingAPI --> RFScannerIntegration : uses
    MobilePickingAPI --> ARNavigationService : enhances
```

## Performance and Analytics

```mermaid
classDiagram
    class PickPerformanceAnalyzer {
        <<Analytics Service>>
        -MetricsCollector collector
        -BenchmarkService benchmark
        +analyzePerformance(period) PerformanceReport
        +calculatePickRate(operator) PickRate
        +identifyBottlenecks() List~Bottleneck~
        +compareToTarget(actual, target) Variance
    }

    class PickMetrics {
        <<Entity>>
        -String sessionId
        -int totalPicks
        -int completedPicks
        -int shortPicks
        -Duration totalTime
        -double travelDistance
        -double accuracy
        -List~ErrorMetric~ errors
        +calculateProductivity() double
        +calculateUPH() double
        +getAveragePickTime() Duration
    }

    class HeatMapGenerator {
        <<Service>>
        -LocationTracker tracker
        -DensityCalculator calculator
        +generateHeatMap(period) HeatMap
        +identifyHotspots() List~Hotspot~
        +suggestReorganization() ReorgPlan
    }

    class PickForecastService {
        <<Service>>
        -MLModel model
        -HistoricalData history
        +forecastVolume(period) VolumeForcast
        +predictPeakTimes() List~PeakPeriod~
        +estimateResources(volume) ResourceRequirement
    }

    PickPerformanceAnalyzer --> PickMetrics : analyzes
    PickPerformanceAnalyzer --> HeatMapGenerator : uses
    PickPerformanceAnalyzer --> PickForecastService : consults
```

## Domain Events

```mermaid
classDiagram
    class PickEvent {
        <<Abstract Event>>
        -String eventId
        -String sessionId
        -String pickerId
        -DateTime occurredAt
        +getEventType() String
    }

    class PickSessionStartedEvent {
        <<Event>>
        -String waveId
        -int pickCount
        -PickStrategy strategy
        +getEventType() String
    }

    class PickConfirmedEvent {
        <<Event>>
        -String pickLineId
        -String skuCode
        -int quantity
        -PickLocation location
        +getEventType() String
    }

    class PickShortageEvent {
        <<Event>>
        -String pickLineId
        -int requested
        -int available
        -ShortageReason reason
        +getEventType() String
    }

    class PickSessionCompletedEvent {
        <<Event>>
        -PickMetrics metrics
        -Duration duration
        -CompletionStatus status
        +getEventType() String
    }

    class PathOptimizedEvent {
        <<Event>>
        -double originalDistance
        -double optimizedDistance
        -double improvement
        +getEventType() String
    }

    PickEvent <|-- PickSessionStartedEvent
    PickEvent <|-- PickConfirmedEvent
    PickEvent <|-- PickShortageEvent
    PickEvent <|-- PickSessionCompletedEvent
    PickEvent <|-- PathOptimizedEvent
```