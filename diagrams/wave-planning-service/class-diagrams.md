# Wave Planning Service - Class Diagrams

## Domain Model Overview

```mermaid
classDiagram
    class Wave {
        <<Aggregate Root>>
        -String waveId
        -String warehouseId
        -WaveType type
        -WaveStatus status
        -Priority priority
        -WaveStrategy strategy
        -List~Order~ orders
        -List~WaveRule~ rules
        -DateTime plannedReleaseTime
        -DateTime actualReleaseTime
        -DateTime cutoffTime
        -WaveMetrics metrics
        -Capacity capacity
        +addOrder(order) void
        +removeOrder(orderId) void
        +plan() WavePlan
        +optimize() void
        +release() void
        +cancel(reason) void
        +validate() ValidationResult
        +calculateCapacity() Capacity
        +applyStrategy(strategy) void
        +evaluatePerformance() WaveMetrics
    }

    class WaveStrategy {
        <<Value Object>>
        -StrategyType type
        -List~StrategyRule~ rules
        -OptimizationGoal goal
        -List~Constraint~ constraints
        +apply(wave) WavePlan
        +evaluate(wave) Score
        +optimize(orders) List~Order~
    }

    class WavePlan {
        <<Entity>>
        -String planId
        -List~PlannedPick~ picks
        -List~Zone~ zones
        -EstimatedMetrics estimates
        -ResourceRequirements resources
        -DateTime estimatedCompletion
        +optimize() void
        +simulate() SimulationResult
        +allocateResources() void
        +calculatePath() PickPath
    }

    class WaveRule {
        <<Value Object>>
        -RuleType type
        -String expression
        -Priority priority
        -List~Condition~ conditions
        -List~Action~ actions
        +evaluate(wave) boolean
        +apply(wave) void
        +validate() boolean
    }

    class CarrierCutoff {
        <<Entity>>
        -String carrierId
        -String carrierName
        -ServiceLevel serviceLevel
        -Time cutoffTime
        -List~DayOfWeek~ applicableDays
        -TimeZone timezone
        +isApplicable(date) boolean
        +getNextCutoff() DateTime
        +minutesUntilCutoff() int
    }

    class WaveTemplate {
        <<Entity>>
        -String templateId
        -String name
        -WaveType type
        -List~WaveRule~ defaultRules
        -WaveStrategy defaultStrategy
        -Schedule schedule
        -boolean active
        +createWave() Wave
        +validate() boolean
        +updateSchedule(schedule) void
    }

    Wave "1" --> "1" WaveStrategy : uses
    Wave "1" --> "*" WaveRule : applies
    Wave "1" --> "1" WavePlan : generates
    Wave "1" --> "*" CarrierCutoff : considers
    WaveTemplate "1" --> "*" Wave : creates
```

## Wave Optimization Engine

```mermaid
classDiagram
    class WaveOptimizer {
        <<Domain Service>>
        -OptimizationAlgorithm algorithm
        -CostCalculator costCalculator
        -ConstraintValidator validator
        +optimize(wave) OptimizedWave
        +optimizeBatch(waves) List~OptimizedWave~
        -calculateCost(wave) Cost
        -applyConstraints(wave) void
        -balanceWorkload(wave) void
    }

    class OptimizationAlgorithm {
        <<Strategy Interface>>
        +optimize(input) OptimizationResult
    }

    class GeneticAlgorithm {
        <<Strategy>>
        -int populationSize
        -double mutationRate
        -int generations
        +optimize(input) OptimizationResult
        -createPopulation() Population
        -crossover(parent1, parent2) Individual
        -mutate(individual) void
        -fitness(individual) double
    }

    class SimulatedAnnealing {
        <<Strategy>>
        -double initialTemp
        -double coolingRate
        -int iterations
        +optimize(input) OptimizationResult
        -generateNeighbor(solution) Solution
        -acceptanceProbability(energy, newEnergy, temp) double
    }

    class GreedyAlgorithm {
        <<Strategy>>
        -SortingCriteria criteria
        +optimize(input) OptimizationResult
        -sortOrders(orders) List~Order~
        -assignToWaves(orders) List~Wave~
    }

    class WorkloadBalancer {
        <<Domain Service>>
        -CapacityCalculator calculator
        -ResourceAllocator allocator
        +balance(waves) BalancedWaves
        +calculateWorkload(wave) Workload
        +distributeEvenly(orders, waves) void
        +levelLoad(waves) void
    }

    class PickPathOptimizer {
        <<Domain Service>>
        -WarehouseGraph graph
        -PathAlgorithm algorithm
        +optimizePath(picks) OptimalPath
        +calculateDistance(path) Distance
        +minimizeTravelTime(picks) PickSequence
        -buildGraph(warehouse) Graph
        -solveTSP(locations) List~Location~
    }

    WaveOptimizer --> OptimizationAlgorithm : uses
    OptimizationAlgorithm <|.. GeneticAlgorithm
    OptimizationAlgorithm <|.. SimulatedAnnealing
    OptimizationAlgorithm <|.. GreedyAlgorithm
    WaveOptimizer --> WorkloadBalancer : uses
    WaveOptimizer --> PickPathOptimizer : uses
```

## Wave Release Management

```mermaid
classDiagram
    class WaveReleaseManager {
        <<Domain Service>>
        -ReleaseValidator validator
        -InventoryChecker inventory
        -CapacityChecker capacity
        -EventPublisher publisher
        +releaseWave(waveId) ReleaseResult
        +releaseBatch(waveIds) BatchReleaseResult
        +scheduleRelease(waveId, time) void
        -validateRelease(wave) ValidationResult
        -checkInventory(wave) InventoryStatus
        -checkCapacity(wave) CapacityStatus
        -publishReleaseEvent(wave) void
    }

    class ReleaseValidator {
        <<Service>>
        -List~ValidationRule~ rules
        +validate(wave) ValidationResult
        -checkCompleteness(wave) boolean
        -checkConflicts(wave) List~Conflict~
        -checkDependencies(wave) boolean
    }

    class WaveScheduler {
        <<Domain Service>>
        -SchedulingStrategy strategy
        -Calendar calendar
        -CarrierSchedule carriers
        +scheduleWaves(date) Schedule
        +getNextWaveTime() DateTime
        +reschedule(waveId, newTime) void
        -considerCarrierCutoffs() List~Cutoff~
        -optimizeSchedule(waves) Schedule
    }

    class AutoWaveCreator {
        <<Domain Service>>
        -WaveTemplate template
        -OrderSelector selector
        -WaveBuilder builder
        +createWaves() List~Wave~
        +selectOrders() List~Order~
        +groupOrders(orders) Map~Criteria, List~Order~~
        -applyTemplate(orders) Wave
        -validateAutoWave(wave) boolean
    }

    class WaveMonitor {
        <<Service>>
        -MetricsCollector metrics
        -AlertService alerts
        +monitorProgress(waveId) Progress
        +detectDelays() List~Delay~
        +calculateSLA() SLAMetrics
        +triggerAlert(condition) void
    }

    WaveReleaseManager --> ReleaseValidator : uses
    WaveReleaseManager --> WaveScheduler : coordinates with
    WaveScheduler --> AutoWaveCreator : triggers
    WaveReleaseManager --> WaveMonitor : notifies
```

## Command and Query Handlers

```mermaid
classDiagram
    class CreateWaveCommand {
        <<Command>>
        -String warehouseId
        -WaveType type
        -List~String~ orderIds
        -WaveStrategy strategy
        -DateTime plannedRelease
        +validate() ValidationResult
    }

    class CreateWaveHandler {
        <<Command Handler>>
        -WaveRepository repository
        -WaveBuilder builder
        -EventBus eventBus
        +handle(command) WaveId
        -buildWave(command) Wave
        -validateOrders(orderIds) void
        -saveWave(wave) void
    }

    class ReleaseWaveCommand {
        <<Command>>
        -String waveId
        -boolean forceRelease
        +validate() ValidationResult
    }

    class ReleaseWaveHandler {
        <<Command Handler>>
        -WaveReleaseManager releaseManager
        -WaveRepository repository
        -EventBus eventBus
        +handle(command) ReleaseResult
        -loadWave(waveId) Wave
        -performRelease(wave) void
        -publishEvents(wave) void
    }

    class OptimizeWaveCommand {
        <<Command>>
        -String waveId
        -OptimizationGoal goal
        -List~Constraint~ constraints
        +validate() ValidationResult
    }

    class OptimizeWaveHandler {
        <<Command Handler>>
        -WaveOptimizer optimizer
        -WaveRepository repository
        +handle(command) OptimizationResult
        -loadWave(waveId) Wave
        -applyOptimization(wave, result) void
    }

    class GetWaveQuery {
        <<Query>>
        -String waveId
        -boolean includeDetails
        -boolean includeMetrics
    }

    class GetWaveHandler {
        <<Query Handler>>
        -WaveReadModel readModel
        +handle(query) WaveDto
        -loadWave(waveId) WaveProjection
        -enrichWithDetails(wave) void
        -addMetrics(wave) void
    }

    CreateWaveHandler ..> CreateWaveCommand : handles
    ReleaseWaveHandler ..> ReleaseWaveCommand : handles
    OptimizeWaveHandler ..> OptimizeWaveCommand : handles
    GetWaveHandler ..> GetWaveQuery : handles
```

## Wave State Machine

```mermaid
classDiagram
    class WaveStatus {
        <<Enumeration>>
        DRAFT
        PLANNED
        OPTIMIZED
        PENDING_RELEASE
        RELEASING
        RELEASED
        IN_PROGRESS
        COMPLETED
        CANCELLED
        FAILED
    }

    class WaveStateMachine {
        <<State Machine>>
        -WaveStatus currentState
        -Map~StateTransition, List~Action~~ transitions
        +transition(event) WaveStatus
        +canTransition(toState) boolean
        +getAvailableTransitions() List~WaveStatus~
        -executeActions(transition) void
        -validateTransition(from, to) boolean
    }

    class WaveEvent {
        <<Enumeration>>
        CREATE
        PLAN
        OPTIMIZE
        SCHEDULE_RELEASE
        RELEASE
        START_EXECUTION
        COMPLETE
        CANCEL
        FAIL
        RETRY
    }

    class StateTransition {
        <<Value Object>>
        -WaveStatus fromState
        -WaveStatus toState
        -WaveEvent triggerEvent
        -List~Condition~ guards
        +isValid(wave) boolean
        +execute(wave) void
    }

    WaveStateMachine "1" --> "1" WaveStatus : current
    WaveStateMachine "1" --> "*" StateTransition : manages
    StateTransition "1" --> "2" WaveStatus : from/to
    StateTransition "1" --> "1" WaveEvent : triggered by
```

## Domain Events

```mermaid
classDiagram
    class WaveEvent {
        <<Abstract Event>>
        -String eventId
        -String waveId
        -DateTime occurredAt
        -String userId
        +getEventType() String
    }

    class WaveCreatedEvent {
        <<Event>>
        -String warehouseId
        -WaveType type
        -int orderCount
        +getEventType() String
    }

    class WavePlannedEvent {
        <<Event>>
        -WavePlan plan
        -EstimatedMetrics estimates
        +getEventType() String
    }

    class WaveReleasedEvent {
        <<Event>>
        -List~String~ orderIds
        -List~String~ taskIds
        -DateTime releaseTime
        +getEventType() String
    }

    class WaveCompletedEvent {
        <<Event>>
        -WaveMetrics actualMetrics
        -Duration executionTime
        -CompletionStatus status
        +getEventType() String
    }

    class WaveOptimizedEvent {
        <<Event>>
        -OptimizationResult result
        -double improvementPercentage
        +getEventType() String
    }

    class WaveEventPublisher {
        <<Publisher>>
        -KafkaProducer producer
        -CloudEventBuilder builder
        +publish(event) void
        +publishBatch(events) void
        -toCloudEvent(event) CloudEvent
    }

    WaveEvent <|-- WaveCreatedEvent
    WaveEvent <|-- WavePlannedEvent
    WaveEvent <|-- WaveReleasedEvent
    WaveEvent <|-- WaveCompletedEvent
    WaveEvent <|-- WaveOptimizedEvent
    WaveEventPublisher ..> WaveEvent : publishes
```

## Integration Services

```mermaid
classDiagram
    class WaveIntegrationService {
        <<Integration Service>>
        -OrderServiceClient orderClient
        -InventoryServiceClient inventoryClient
        -TaskServiceClient taskClient
        -WorkloadServiceClient workloadClient
        +fetchOrders(criteria) List~Order~
        +checkInventory(items) InventoryStatus
        +createTasks(wave) List~Task~
        +getCapacity() CapacityInfo
    }

    class CarrierIntegrationService {
        <<Integration Service>>
        -Map~String, CarrierAdapter~ adapters
        +getCarrierCutoffs() List~CarrierCutoff~
        +updateCutoffTimes(carrier) void
        +getServiceLevels(carrier) List~ServiceLevel~
        +validateShipment(carrier, shipment) boolean
    }

    class WaveAnalyticsService {
        <<Analytics Service>>
        -DataWarehouseClient dwClient
        -MLPredictionService mlService
        +analyzePerformance(waveId) PerformanceReport
        +predictExecutionTime(wave) Duration
        +recommendStrategy(criteria) WaveStrategy
        +generateKPIs(period) KPIReport
    }

    class WaveNotificationService {
        <<Notification Service>>
        -NotificationTemplates templates
        -ChannelManager channels
        +notifyWaveRelease(wave) void
        +notifyDelay(wave, delay) void
        +notifyCompletion(wave) void
        +sendAlert(alert) void
        -selectChannel(recipient) Channel
    }

    WaveIntegrationService --> Wave : enriches
    CarrierIntegrationService --> CarrierCutoff : manages
    WaveAnalyticsService --> Wave : analyzes
    WaveNotificationService --> Wave : monitors
```

## Business Rules and Strategies

```mermaid
classDiagram
    class WaveBusinessRules {
        <<Policy>>
        +MAX_ORDERS_PER_WAVE: int
        +MIN_ORDERS_FOR_WAVE: int
        +MAX_WAVE_DURATION: Duration
        +RELEASE_BUFFER_TIME: Duration
        +validateWaveSize(wave) boolean
        +validateReleaseTime(wave) boolean
        +checkCapacityLimits(wave) boolean
        +enforceCarrierCutoffs(wave) boolean
    }

    class WaveSelectionStrategy {
        <<Strategy Interface>>
        +selectOrders(available) List~Order~
    }

    class PriorityBasedSelection {
        <<Strategy>>
        +selectOrders(available) List~Order~
        -sortByPriority(orders) List~Order~
        -applyPriorityRules(order) int
    }

    class CarrierBasedSelection {
        <<Strategy>>
        +selectOrders(available) List~Order~
        -groupByCarrier(orders) Map~Carrier, List~Order~~
        -selectByNextCutoff(groups) List~Order~
    }

    class ZoneBasedSelection {
        <<Strategy>>
        +selectOrders(available) List~Order~
        -groupByZone(orders) Map~Zone, List~Order~~
        -balanceAcrossZones(groups) List~Order~
    }

    WaveSelectionStrategy <|.. PriorityBasedSelection
    WaveSelectionStrategy <|.. CarrierBasedSelection
    WaveSelectionStrategy <|.. ZoneBasedSelection
```