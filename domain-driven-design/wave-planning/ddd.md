# Wave Planning Service - Domain-Driven Design

## Bounded Context: Wave Planning & Optimization

The Wave Planning Service is responsible for intelligently grouping orders into executable waves based on multiple optimization strategies, carrier cutoffs, and operational constraints.

## Domain Model

### Aggregates

#### Wave (Aggregate Root)
**Purpose**: Represents a batch of orders grouped for efficient processing

**Properties**:
```java
public class Wave {
    private WaveId waveId;
    private WaveNumber waveNumber;
    private WaveStatus status;
    private WaveStrategy strategy;
    private List<OrderReference> orders;
    private PlannedTimeWindow timeWindow;
    private List<ResourceAssignment> assignedResources;
    private OptimizationMetrics metrics;
    private WaveConstraints constraints;
}
```

**Invariants**:
- A wave must contain at least one order
- Cannot exceed zone capacity constraints
- Must respect carrier cutoff times
- Cannot be modified after release
- Total volume cannot exceed available resources

**State Transitions**:
```
DRAFT -> PLANNED -> RELEASED -> IN_PROGRESS -> COMPLETED
   |                    |           |
   +--------------------+-----------+-> CANCELLED
```

#### WaveStrategy (Entity)
**Purpose**: Defines the rules and priorities for wave creation

**Properties**:
```java
public class WaveStrategy {
    private StrategyId strategyId;
    private StrategyType type; // ZONE_BASED, CARRIER_CUTOFF, PRIORITY, MULTI_STRATEGY
    private List<OptimizationRule> rules;
    private PriorityWeights weights;
    private CapacityLimits limits;
}
```

#### WavePlan (Entity)
**Purpose**: Execution plan for a wave with resource allocation

**Properties**:
```java
public class WavePlan {
    private PlanId planId;
    private List<TaskAllocation> taskAllocations;
    private RouteOptimization pickingRoutes;
    private EstimatedDuration duration;
    private ResourceRequirements resources;
}
```

### Value Objects

#### WaveId
- Unique identifier for waves
- Format: "WAVE-YYYYMMDD-XXXXX"

#### WaveNumber
- Human-readable wave identifier
- Sequential numbering per day

#### PlannedTimeWindow
```java
public class PlannedTimeWindow {
    private LocalDateTime plannedStart;
    private LocalDateTime plannedEnd;
    private LocalDateTime carrierCutoff;
    private Duration bufferTime;
}
```

#### OptimizationMetrics
```java
public class OptimizationMetrics {
    private Integer orderCount;
    private Integer lineCount;
    private BigDecimal totalVolume;
    private BigDecimal totalWeight;
    private Double pickDensity;
    private Double zoneUtilization;
    private EstimatedDuration processingTime;
}
```

#### WaveConstraints
```java
public class WaveConstraints {
    private Integer maxOrders;
    private Integer maxLines;
    private Integer maxPickers;
    private BigDecimal maxVolume;
    private List<ZoneCapacity> zoneCapacities;
}
```

#### StrategyType
```java
public enum StrategyType {
    ZONE_BASED,          // Group by warehouse zones
    CARRIER_CUTOFF,      // Group by carrier deadlines
    PRIORITY_BASED,      // Group by order priority
    CUSTOMER_BASED,      // Group by customer
    MULTI_STRATEGY,      // Combination of strategies
    CONTINUOUS_FLOW      // Waveless processing
}
```

#### WaveStatus
```java
public enum WaveStatus {
    DRAFT,
    PLANNED,
    RELEASED,
    IN_PROGRESS,
    COMPLETED,
    CANCELLED,
    ON_HOLD
}
```

### Domain Services

#### WaveOptimizationService
**Purpose**: Applies optimization algorithms to create efficient waves

```java
public interface WaveOptimizationService {
    Wave optimizeWave(List<Order> orders, WaveStrategy strategy);
    WavePlan createExecutionPlan(Wave wave);
    OptimizationMetrics calculateMetrics(Wave wave);
    List<Wave> rebalanceWaves(List<Wave> waves);
}
```

**Algorithms**:
- Bin packing for volume optimization
- Time-window optimization for carrier cutoffs
- Zone balancing for picker efficiency
- Priority scoring for order sequencing

#### WaveReleaseService
**Purpose**: Validates and releases waves for execution

```java
public interface WaveReleaseService {
    ValidationResult validateWave(Wave wave);
    Wave releaseWave(Wave wave);
    void notifyDownstreamSystems(Wave wave);
    boolean checkResourceAvailability(Wave wave);
}
```

#### CarrierCutoffService
**Purpose**: Manages carrier pickup schedules and deadlines

```java
public interface CarrierCutoffService {
    List<CarrierCutoff> getUpcomingCutoffs(LocalDate date);
    Duration getRequiredProcessingTime(Carrier carrier);
    boolean willMeetCutoff(Wave wave, CarrierCutoff cutoff);
}
```

### Domain Events

#### Wave Lifecycle Events
```java
public class WavePlanned extends DomainEvent {
    private WaveId waveId;
    private Integer orderCount;
    private LocalDateTime plannedStart;
    private WaveStrategy strategy;
}

public class WaveOptimized extends DomainEvent {
    private WaveId waveId;
    private OptimizationMetrics beforeMetrics;
    private OptimizationMetrics afterMetrics;
}

public class WaveReleased extends DomainEvent {
    private WaveId waveId;
    private LocalDateTime releaseTime;
    private List<String> assignedResources;
}

public class WaveStarted extends DomainEvent {
    private WaveId waveId;
    private LocalDateTime actualStart;
}

public class WaveCompleted extends DomainEvent {
    private WaveId waveId;
    private LocalDateTime completionTime;
    private CompletionMetrics metrics;
}

public class WaveCancelled extends DomainEvent {
    private WaveId waveId;
    private CancellationReason reason;
    private List<String> affectedOrders;
}
```

### Repository Interfaces

```java
public interface WaveRepository {
    Wave save(Wave wave);
    Optional<Wave> findById(WaveId waveId);
    List<Wave> findByStatus(WaveStatus status);
    List<Wave> findByDateRange(LocalDate start, LocalDate end);
    List<Wave> findPendingWaves();
}

public interface WaveStrategyRepository {
    WaveStrategy save(WaveStrategy strategy);
    Optional<WaveStrategy> findById(StrategyId strategyId);
    List<WaveStrategy> findActiveStrategies();
}
```

## Integration Patterns

### Upstream Dependencies
- **Order Management**: Receives orders for wave planning
- **Inventory**: Checks stock availability
- **Predictive Analytics**: Receives volume forecasts

### Downstream Dependencies
- **Task Execution**: Sends wave tasks for execution
- **Pick Execution**: Provides pick lists and routes
- **Workload Planning**: Provides resource requirements

### Events Published
- WavePlanned
- WaveOptimized
- WaveReleased
- WaveStarted
- WaveCompleted
- WaveCancelled

### Events Subscribed
- OrderCreated (from Order Management)
- OrderPriorityChanged (from Order Management)
- InventoryAllocated (from Inventory)
- ForecastGenerated (from Predictive Analytics)

## Business Rules

### Wave Creation Rules
1. **Minimum Wave Size**: At least 10 orders or 50 lines
2. **Maximum Wave Size**: No more than 200 orders or 1000 lines
3. **Zone Capacity**: Cannot exceed 80% of zone picking capacity
4. **Time Window**: Must complete 30 minutes before carrier cutoff
5. **Priority Mixing**: High priority orders get dedicated waves

### Optimization Rules
1. **Pick Density**: Maximize items per location visit
2. **Zone Balancing**: Distribute work evenly across zones
3. **Carrier Grouping**: Group orders by carrier when possible
4. **Customer Consolidation**: Keep same-customer orders together

### Release Rules
1. **Resource Check**: Sufficient pickers must be available
2. **Equipment Check**: Required equipment must be ready
3. **Inventory Verification**: All items must be allocated
4. **System Health**: All downstream systems must be operational

## Anti-Corruption Layer

### External System Integration
```java
public class ExternalWMSAdapter implements WaveImportPort {
    public List<Order> importOrders(ExternalOrderFormat external) {
        // Transform external format to domain model
        return orderTransformer.transform(external);
    }
}
```

## Performance Optimization

### Caching Strategy
- Cache active wave strategies
- Cache carrier cutoff schedules
- Cache zone capacity limits

### Event Sourcing
- Store wave planning decisions for replay
- Maintain audit trail of optimizations
- Enable what-if analysis with historical data

## Testing Strategy

### Unit Tests
- Wave creation with various strategies
- Optimization algorithm validation
- Business rule enforcement
- State transition validation

### Integration Tests
- End-to-end wave planning flow
- Event publishing verification
- External system integration

### Performance Tests
- Large wave optimization (1000+ orders)
- Concurrent wave planning
- Real-time reoptimization

## Monitoring & Metrics

### Key Metrics
- Wave planning time
- Optimization effectiveness
- Carrier cutoff adherence
- Resource utilization
- Wave completion rate

### SLA Targets
- Wave planning: < 30 seconds for 100 orders
- Optimization: < 5 seconds per wave
- Release processing: < 2 seconds
- Event publishing: < 100ms