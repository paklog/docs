# Pick Execution Service - Domain-Driven Design

## Bounded Context: Mobile Picking & Path Optimization

The Pick Execution Service manages the actual picking process with TSP (Traveling Salesman Problem) path optimization, batch picking support, real-time exception handling, and mobile device integration.

## Domain Model

### Aggregates

#### PickList (Aggregate Root)
**Purpose**: Represents a collection of items to be picked with optimized routing

**Properties**:
```java
public class PickList {
    private PickListId pickListId;
    private PickerId pickerId;
    private PickListStatus status;
    private PickStrategy strategy;
    private List<PickItem> items;
    private PickRoute optimizedRoute;
    private PickMetrics metrics;
    private List<PickException> exceptions;
    private DeviceInfo deviceInfo;
    private TimeTracking timeTracking;
}
```

**Invariants**:
- Must have at least one item to pick
- Route must visit all pick locations
- Cannot pick more than requested quantity
- Short picks require supervisor approval
- Must scan location before picking

**State Transitions**:
```
CREATED -> ASSIGNED -> IN_PROGRESS -> COMPLETED
    |          |            |
    |          |            +-> PARTIAL_COMPLETE
    |          |            |
    |          |            +-> EXCEPTION
    |          |
    +----------+-------------> CANCELLED
```

#### PickRoute (Entity)
**Purpose**: Optimized path through warehouse using TSP algorithms

**Properties**:
```java
public class PickRoute {
    private RouteId routeId;
    private List<RouteStop> stops;
    private OptimizationAlgorithm algorithm;
    private BigDecimal totalDistance;
    private Duration estimatedTime;
    private RouteMetrics metrics;
    private List<RouteSegment> segments;
}
```

#### PickBatch (Entity)
**Purpose**: Groups multiple orders for batch picking

**Properties**:
```java
public class PickBatch {
    private BatchId batchId;
    private List<PickList> pickLists;
    private BatchStrategy strategy;
    private ConsolidationPoint consolidationPoint;
    private SortInstructions sortInstructions;
}
```

### Value Objects

#### PickItem
```java
public class PickItem {
    private ItemId itemId;
    private SKU sku;
    private Location location;
    private Quantity requestedQuantity;
    private Quantity pickedQuantity;
    private PickConfirmation confirmation;
    private List<SerialNumber> serialNumbers;
    private LotNumber lotNumber;
}
```

#### PickRoute
```java
public class PickRoute {
    private List<RouteStop> stops;
    private BigDecimal totalDistance;
    private Duration estimatedDuration;
    private OptimizationMetrics metrics;

    public static PickRoute optimize(List<Location> locations) {
        // TSP optimization using 2-opt algorithm
        return new TwoOptAlgorithm().optimize(locations);
    }
}
```

#### RouteStop
```java
public class RouteStop {
    private Integer sequence;
    private Location location;
    private List<PickItem> items;
    private StopType type; // PICK, CONSOLIDATION, CHECKPOINT
    private Duration estimatedTime;
    private NavigationInstructions instructions;
}
```

#### PickConfirmation
```java
public class PickConfirmation {
    private ConfirmationType type; // SCAN, MANUAL, VOICE, VISION
    private String confirmationData;
    private LocalDateTime confirmedAt;
    private GPSCoordinates coordinates;
    private PhotoCapture photo;
}
```

#### PickException
```java
public class PickException {
    private ExceptionType type;
    private String description;
    private ResolutionAction resolution;
    private SupervisorApproval approval;
}

public enum ExceptionType {
    SHORT_PICK,
    DAMAGED_ITEM,
    WRONG_ITEM,
    LOCATION_EMPTY,
    ITEM_NOT_FOUND,
    BARCODE_UNREADABLE
}
```

#### OptimizationAlgorithm
```java
public enum OptimizationAlgorithm {
    NEAREST_NEIGHBOR,    // Simple greedy algorithm
    TWO_OPT,            // Local search optimization
    GENETIC_ALGORITHM,   // For large pick lists
    SIMULATED_ANNEALING, // For complex constraints
    ANT_COLONY,         // For dynamic environments
    S_SHAPE,            // Traditional warehouse pattern
    RETURN_PATTERN      // Optimized return routing
}
```

### Domain Services

#### PathOptimizationService
**Purpose**: Implements TSP algorithms for route optimization

```java
public interface PathOptimizationService {
    PickRoute optimizePath(List<Location> locations, OptimizationAlgorithm algorithm);
    PickRoute reoptimizePath(PickRoute current, List<Location> remaining);
    BigDecimal calculateDistance(Location from, Location to);
    Duration estimateTravelTime(PickRoute route, WalkingSpeed speed);
}
```

**TSP 2-Opt Algorithm Implementation**:
```java
public class TwoOptAlgorithm {
    public PickRoute optimize(List<Location> locations) {
        PickRoute currentRoute = createInitialRoute(locations);
        boolean improved = true;

        while (improved) {
            improved = false;
            for (int i = 1; i < locations.size() - 2; i++) {
                for (int j = i + 1; j < locations.size(); j++) {
                    if (j - i == 1) continue;

                    PickRoute newRoute = swap2Opt(currentRoute, i, j);
                    if (newRoute.getTotalDistance() < currentRoute.getTotalDistance()) {
                        currentRoute = newRoute;
                        improved = true;
                    }
                }
            }
        }
        return currentRoute;
    }
}
```

#### BatchPickingService
**Purpose**: Manages multi-order batch picking

```java
public interface BatchPickingService {
    PickBatch createBatch(List<PickList> pickLists, BatchStrategy strategy);
    ConsolidationInstructions getConsolidationInstructions(PickBatch batch);
    SortInstructions getSortInstructions(PickBatch batch);
    void splitBatch(PickBatch batch, SplitReason reason);
}
```

#### PickValidationService
**Purpose**: Validates picks and handles exceptions

```java
public interface PickValidationService {
    ValidationResult validatePick(PickItem item, ScanData scanData);
    PickException handleShortPick(PickItem item, Quantity available);
    SupervisorApproval requestApproval(PickException exception);
    void recordPickConfirmation(PickItem item, ConfirmationData data);
}
```

### Domain Events

#### Pick Execution Events
```java
public class PickListCreated extends DomainEvent {
    private PickListId pickListId;
    private Integer itemCount;
    private OptimizationAlgorithm algorithm;
    private BigDecimal estimatedDistance;
}

public class PickStarted extends DomainEvent {
    private PickListId pickListId;
    private PickerId pickerId;
    private Location startLocation;
    private LocalDateTime startTime;
}

public class ItemPicked extends DomainEvent {
    private PickListId pickListId;
    private ItemId itemId;
    private SKU sku;
    private Quantity quantity;
    private Location location;
    private ConfirmationType confirmation;
}

public class PickShortage extends DomainEvent {
    private PickListId pickListId;
    private ItemId itemId;
    private Quantity requested;
    private Quantity available;
    private ShortageReason reason;
}

public class PickCompleted extends DomainEvent {
    private PickListId pickListId;
    private LocalDateTime completionTime;
    private PickMetrics metrics;
    private Integer exceptionCount;
}

public class PickRouteOptimized extends DomainEvent {
    private PickListId pickListId;
    private BigDecimal originalDistance;
    private BigDecimal optimizedDistance;
    private BigDecimal savingsPercentage;
}
```

### Repository Interfaces

```java
public interface PickListRepository {
    PickList save(PickList pickList);
    Optional<PickList> findById(PickListId pickListId);
    List<PickList> findByPicker(PickerId pickerId);
    List<PickList> findByStatus(PickListStatus status);
    List<PickList> findPendingPicks();
}

public interface PickRouteRepository {
    PickRoute save(PickRoute route);
    Optional<PickRoute> findByPickList(PickListId pickListId);
    List<PickRoute> findOptimizationCandidates();
}
```

## Integration Patterns

### Upstream Dependencies
- **Task Execution**: Receives pick tasks
- **Wave Planning**: Receives wave pick lists
- **Inventory**: Validates stock availability

### Downstream Dependencies
- **Pack & Ship**: Sends completed picks
- **Physical Tracking**: Updates container movements
- **Inventory**: Updates picked quantities

### Mobile Device Integration
```java
public interface MobileDevicePort {
    void sendPickList(DeviceId deviceId, PickList pickList);
    ScanData receiveScan(DeviceId deviceId);
    void displayNavigation(DeviceId deviceId, NavigationInstructions instructions);
    void requestConfirmation(DeviceId deviceId, ConfirmationRequest request);
}
```

## Business Rules

### Path Optimization Rules
1. **Maximum Distance**: Optimize if route > 500 meters
2. **Algorithm Selection**:
   - < 10 stops: Nearest Neighbor
   - 10-50 stops: 2-Opt
   - > 50 stops: Genetic Algorithm
3. **Congestion Avoidance**: Avoid high-traffic zones during peak hours
4. **Priority Stops**: High-priority items picked first
5. **Battery Consideration**: Route based on device battery level

### Picking Rules
1. **FIFO/FEFO**: Respect inventory rotation rules
2. **Location Verification**: Must scan location before picking
3. **Quantity Limits**: Cannot exceed requested quantity
4. **Damage Check**: Visual inspection required
5. **Serial Tracking**: Capture serials for tracked items

### Exception Handling Rules
1. **Short Pick Threshold**: < 90% requires approval
2. **Substitution**: Allow approved substitutions
3. **Damage Reporting**: Photo required for damaged items
4. **Skip Location**: Max 3 skips before escalation
5. **Time Limits**: 5 minutes max per location

## Performance Optimization

### Route Caching
```java
public class RouteCache {
    private final Cache<String, PickRoute> routeCache;

    public PickRoute getCachedRoute(List<Location> locations) {
        String key = generateKey(locations);
        return routeCache.get(key, () -> optimizeRoute(locations));
    }
}
```

### Real-time Optimization
- Dynamic re-routing based on congestion
- Skip optimization for < 5 locations
- Parallel route calculation for batches
- Pre-calculate common routes

### Mobile Performance
- Offline mode support
- Local route caching
- Progressive data loading
- Compressed data transmission

## Monitoring & Metrics

### Key Metrics
- Pick rate (lines/hour)
- Pick accuracy (%)
- Travel distance saved (%)
- Exception rate
- Average pick time per item
- Route optimization effectiveness

### SLA Targets
- Pick accuracy: > 99.5%
- Route optimization: < 2 seconds
- Pick confirmation: < 500ms
- Exception resolution: < 5 minutes
- Pick rate: > 150 lines/hour