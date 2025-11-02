# Physical Tracking Service - Domain-Driven Design

## Bounded Context: License Plate & Asset Tracking

The Physical Tracking Service provides real-time tracking of physical assets using license plates (LPNs), managing container movements, location updates, and maintaining the relationship between logical inventory and physical containers.

## Domain Model

### Aggregates

#### LicensePlate (Aggregate Root)
**Purpose**: Unique identifier for tracking physical containers/pallets

**Properties**:
```java
public class LicensePlate {
    private LicensePlateNumber lpn;
    private LPNStatus status;
    private ContainerType containerType;
    private Location currentLocation;
    private List<ContentItem> contents;
    private MovementHistory movementHistory;
    private Dimensions dimensions;
    private Weight currentWeight;
    private LPNHierarchy hierarchy;
    private TrackingMetadata metadata;
    private LPNConstraints constraints;
}
```

**Invariants**:
- LPN must be unique across the system
- Cannot exceed weight capacity
- Parent-child hierarchy must be consistent
- Location must be valid warehouse location
- Cannot be in two locations simultaneously

**State Transitions**:
```
CREATED -> EMPTY -> IN_USE -> MOVING -> AT_LOCATION -> IN_USE
    |        |         |          |           |
    |        |         |          |           +-> CONSOLIDATING
    |        |         |          |           |
    |        |         |          |           +-> SEALED
    |        |         |          |
    |        |         +-> LOST -> FOUND
    |        |
    |        +-> RETIRED
    |
    +-> CANCELLED
```

#### AssetLocation (Entity)
**Purpose**: Current and historical location of assets

**Properties**:
```java
public class AssetLocation {
    private LocationId locationId;
    private LicensePlateNumber lpn;
    private LocationType locationType;
    private Position position;
    private LocalDateTime arrivedAt;
    private LocalDateTime expectedDepartureAt;
    private LocationStatus status;
    private List<NearbyAssets> nearby;
}
```

#### MovementHistory (Entity)
**Purpose**: Complete movement audit trail

**Properties**:
```java
public class MovementHistory {
    private List<Movement> movements;
    private Statistics movementStats;
    private List<DwellTime> dwellTimes;
    private TravelDistance totalDistance;

    public Duration getAverageDwellTime(LocationType type) {
        return dwellTimes.stream()
            .filter(d -> d.getLocationType() == type)
            .map(DwellTime::getDuration)
            .reduce(Duration.ZERO, Duration::plus)
            .dividedBy(dwellTimes.size());
    }
}
```

### Value Objects

#### LicensePlateNumber
```java
public class LicensePlateNumber {
    private String value;
    private LPNFormat format;
    private LocalDateTime generatedAt;

    public static LicensePlateNumber generate(LPNFormat format) {
        return switch (format) {
            case SEQUENTIAL -> generateSequential();
            case RANDOM -> generateRandom();
            case SSCC -> generateSSCC(); // Serial Shipping Container Code
            case CUSTOM -> generateCustom();
        };
    }

    public boolean isValid() {
        return format.validate(value);
    }
}
```

#### Movement
```java
public class Movement {
    private MovementId movementId;
    private Location fromLocation;
    private Location toLocation;
    private LocalDateTime startTime;
    private LocalDateTime endTime;
    private MovementType type;
    private MovedBy movedBy;
    private TransportMethod method;

    public Duration getDuration() {
        return Duration.between(startTime, endTime);
    }

    public BigDecimal getDistance() {
        return fromLocation.distanceTo(toLocation);
    }
}
```

#### ContentItem
```java
public class ContentItem {
    private SKU sku;
    private Quantity quantity;
    private LotNumber lotNumber;
    private SerialNumbers serialNumbers;
    private ItemStatus status;
    private Weight weight;
    private LocalDateTime addedAt;
}
```

#### LPNHierarchy
```java
public class LPNHierarchy {
    private LicensePlateNumber parent;
    private List<LicensePlateNumber> children;
    private Integer nestingLevel;
    private HierarchyType type;

    public boolean canNest(LicensePlateNumber child) {
        return nestingLevel < MAX_NESTING_LEVEL
            && !wouldCreateCycle(child);
    }

    public Integer getTotalChildCount() {
        return children.size() + children.stream()
            .mapToInt(child -> getChildCount(child))
            .sum();
    }
}
```

#### ContainerType
```java
public class ContainerType {
    private String typeId;
    private String name;
    private ContainerCategory category;
    private Dimensions dimensions;
    private Weight tareWeight;
    private Weight maxWeight;
    private Boolean isReusable;
    private Boolean isNestable;
    private List<CompatibleTypes> compatibleWith;
}
```

### Domain Services

#### LPNGenerationService
**Purpose**: Generates and manages license plate numbers

```java
public interface LPNGenerationService {
    LicensePlateNumber generateLPN(LPNFormat format);
    List<LicensePlateNumber> generateBatch(Integer count, LPNFormat format);
    Boolean validateLPN(LicensePlateNumber lpn);
    void reserveLPN(LicensePlateNumber lpn);
    void releaseLPN(LicensePlateNumber lpn);
}
```

#### MovementTrackingService
**Purpose**: Tracks and records asset movements

```java
public interface MovementTrackingService {
    Movement recordMovement(LicensePlateNumber lpn, Location to);
    MovementHistory getMovementHistory(LicensePlateNumber lpn);
    List<Movement> getMovementsByLocation(Location location);
    DwellTimeAnalysis analyzeDwellTime(LicensePlateNumber lpn);
    void detectAnomalousMovements(Movement movement);
}
```

#### ConsolidationService
**Purpose**: Manages container consolidation and splitting

```java
public interface ConsolidationService {
    LicensePlate consolidate(List<LicensePlateNumber> source, LicensePlateNumber target);
    List<LicensePlate> split(LicensePlateNumber source, SplitStrategy strategy);
    void nestContainer(LicensePlateNumber parent, LicensePlateNumber child);
    void unnestContainer(LicensePlateNumber child);
    ValidationResult validateConsolidation(List<LicensePlate> sources);
}
```

#### RTLSIntegrationService
**Purpose**: Integrates with Real-Time Location System

```java
public interface RTLSIntegrationService {
    Position getCurrentPosition(LicensePlateNumber lpn);
    void subscribeToPositionUpdates(LicensePlateNumber lpn);
    List<Position> getPositionHistory(LicensePlateNumber lpn, TimeRange range);
    void calibratePosition(LicensePlateNumber lpn, Position actual);
}
```

### Domain Events

#### Tracking Events
```java
public class LicensePlateCreated extends DomainEvent {
    private LicensePlateNumber lpn;
    private ContainerType containerType;
    private Location initialLocation;
    private LocalDateTime createdAt;
}

public class AssetMoved extends DomainEvent {
    private LicensePlateNumber lpn;
    private Location fromLocation;
    private Location toLocation;
    private MovementType movementType;
    private LocalDateTime movedAt;
}

public class LocationUpdated extends DomainEvent {
    private LicensePlateNumber lpn;
    private Location newLocation;
    private Position exactPosition;
    private LocationSource source;
}

public class ContentAdded extends DomainEvent {
    private LicensePlateNumber lpn;
    private SKU sku;
    private Quantity quantity;
    private LocalDateTime addedAt;
}

public class ContainersConsolidated extends DomainEvent {
    private List<LicensePlateNumber> sourceLPNs;
    private LicensePlateNumber targetLPN;
    private ConsolidationReason reason;
}

public class ContainerSealed extends DomainEvent {
    private LicensePlateNumber lpn;
    private SealNumber sealNumber;
    private LocalDateTime sealedAt;
    private String sealedBy;
}

public class AssetLost extends DomainEvent {
    private LicensePlateNumber lpn;
    private Location lastKnownLocation;
    private LocalDateTime lastSeen;
}
```

### Repository Interfaces

```java
public interface LicensePlateRepository {
    LicensePlate save(LicensePlate licensePlate);
    Optional<LicensePlate> findByLPN(LicensePlateNumber lpn);
    List<LicensePlate> findByLocation(Location location);
    List<LicensePlate> findByStatus(LPNStatus status);
    List<LicensePlate> findBySKU(SKU sku);
    List<LicensePlate> findEmpty();
}

public interface MovementHistoryRepository {
    MovementHistory save(MovementHistory history);
    MovementHistory findByLPN(LicensePlateNumber lpn);
    List<Movement> findMovementsByTimeRange(TimeRange range);
    List<Movement> findMovementsByLocation(Location location);
}
```

## Integration Patterns

### Upstream Dependencies
- **Inventory Service**: Receives inventory movements
- **Pick Execution**: Updates on picks from LPNs
- **Receiving**: Creates LPNs for received goods

### Downstream Dependencies
- **Location Master**: Validates locations
- **Task Execution**: Provides LPN locations for tasks

### Hardware Integration
```java
public interface ScannerIntegrationPort {
    ScanEvent receiveScan(ScannerId scanner);
    void validateScan(LicensePlateNumber lpn, Location location);
    void triggerScanFeedback(ScannerId scanner, FeedbackType type);
}

public interface RFIDIntegrationPort {
    List<RFIDRead> bulkRead(RFIDReader reader);
    void writeTag(LicensePlateNumber lpn, RFIDTag tag);
    Position triangulatePosition(List<RFIDRead> reads);
}
```

## Business Rules

### LPN Generation Rules
1. **Uniqueness**: LPNs must be globally unique
2. **Format**: Follow configured format (e.g., "LPN-XXXXXXXX")
3. **Check Digit**: Include check digit for validation
4. **Reserved Ranges**: Certain ranges for specific purposes
5. **Reuse Policy**: Can reuse after 90 days of inactivity

### Movement Rules
1. **Valid Locations**: Destination must be valid location
2. **Capacity Check**: Location must have capacity
3. **Path Validation**: Movement path must be valid
4. **Time Constraints**: Movements must complete within SLA
5. **Authorization**: Certain movements require approval

### Consolidation Rules
1. **Compatibility**: Items must be compatible
2. **Weight Limit**: Cannot exceed container capacity
3. **Mixing Rules**: Cannot mix certain product types
4. **FIFO/FEFO**: Respect inventory rotation
5. **Nesting Limit**: Maximum 3 levels of nesting

### Tracking Rules
1. **Update Frequency**: Position updates every 10 seconds
2. **Dwell Alert**: Alert if stationary > 2 hours
3. **Lost Asset**: Mark lost if not seen > 24 hours
4. **Audit Trail**: All movements must be logged
5. **Reconciliation**: Daily physical vs logical reconciliation

## Performance Optimization

### Caching Strategy
```java
public class LPNLocationCache {
    private final Cache<LicensePlateNumber, Location> locationCache;

    public Location getLocation(LicensePlateNumber lpn) {
        return locationCache.get(lpn,
            () -> repository.findByLPN(lpn).map(LicensePlate::getCurrentLocation));
    }

    public void updateLocation(LicensePlateNumber lpn, Location location) {
        locationCache.put(lpn, location);
        // Async write to database
    }
}
```

### Batch Processing
- Batch movement updates
- Bulk LPN generation
- Batch RFID reads
- Aggregate position updates

### Event Streaming
- Real-time position streaming via WebSocket
- Event sourcing for movement history
- CDC for inventory synchronization

## Monitoring & Metrics

### Key Metrics
- Active LPN count
- Movement frequency
- Average dwell time
- Lost asset rate
- Consolidation rate
- Position accuracy

### SLA Targets
- LPN generation: < 100ms
- Movement recording: < 500ms
- Position update: < 1 second
- Location query: < 50ms
- History retrieval: < 2 seconds