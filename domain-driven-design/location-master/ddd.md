# Location Master Service - Domain-Driven Design

## Bounded Context: Warehouse Location Configuration & Slotting

The Location Master Service manages the warehouse location hierarchy, configuration, ABC velocity-based slotting optimization, capacity tracking, and golden zone management for optimal picking efficiency.

## Domain Model

### Aggregates

#### Location (Aggregate Root)
**Purpose**: Represents a physical storage location in the warehouse

**Properties**:
```java
public class Location {
    private LocationId locationId;
    private LocationCode code;
    private LocationType type;
    private LocationStatus status;
    private Zone zone;
    private Dimensions dimensions;
    private Capacity capacity;
    private LocationAttributes attributes;
    private SlottingProfile slottingProfile;
    private VelocityClass velocityClass;
    private List<LocationRestriction> restrictions;
    private AccessibilityInfo accessibility;
    private LocationMetrics metrics;
}
```

**Invariants**:
- Location code must be unique within warehouse
- Cannot exceed physical capacity limits
- Must belong to exactly one zone
- Velocity class must match slotting profile
- Cannot violate location restrictions

**State Transitions**:
```
CREATED -> AVAILABLE -> OCCUPIED -> FULL
    |          |           |
    |          |           +-> PARTIALLY_OCCUPIED
    |          |           |
    |          |           +-> RESERVED
    |          |
    |          +-> BLOCKED -> AVAILABLE
    |
    +-> DEACTIVATED
```

#### Zone (Entity)
**Purpose**: Logical grouping of locations with common characteristics

**Properties**:
```java
public class Zone {
    private ZoneId zoneId;
    private String name;
    private ZoneType type;
    private List<Location> locations;
    private ZoneConfiguration configuration;
    private PickingStrategy pickingStrategy;
    private StorageStrategy storageStrategy;
    private TemperatureRange temperatureRange;
    private SecurityLevel securityLevel;
    private ZoneMetrics metrics;
}
```

#### SlottingStrategy (Entity)
**Purpose**: Rules and algorithms for product placement optimization

**Properties**:
```java
public class SlottingStrategy {
    private StrategyId strategyId;
    private StrategyType type;
    private VelocityAnalysis velocityAnalysis;
    private CubicMovementCalculation cubicMovement;
    private AffinityMatrix affinityMatrix;
    private SeasonalAdjustments seasonalFactors;
    private GoldenZoneAllocation goldenZone;
    private OptimizationConstraints constraints;
}
```

### Value Objects

#### LocationCode
```java
public class LocationCode {
    private String warehouse;
    private String zone;
    private String aisle;
    private String bay;
    private String level;
    private String position;

    public String getFullCode() {
        return String.format("%s-%s-%s-%s-%s-%s",
            warehouse, zone, aisle, bay, level, position);
    }

    public Integer getPickSequence() {
        // Calculate optimal pick sequence based on layout
        return (aisle * 1000) + (bay * 100) + (level * 10) + position;
    }

    public BigDecimal distanceFrom(LocationCode other) {
        // Manhattan distance calculation
        Integer aisleDiff = Math.abs(this.aisle - other.aisle);
        Integer bayDiff = Math.abs(this.bay - other.bay);
        Integer levelDiff = Math.abs(this.level - other.level);

        return BigDecimal.valueOf(
            (aisleDiff * AISLE_WIDTH) +
            (bayDiff * BAY_DEPTH) +
            (levelDiff * LEVEL_HEIGHT)
        );
    }
}
```

#### VelocityClass
```java
public class VelocityClass {
    private Classification classification;
    private BigDecimal turnoverRate;
    private Integer pickFrequency;
    private BigDecimal cubicMovement;

    public enum Classification {
        A_FAST_MOVER,    // Top 20% of picks, 80% of volume
        B_MEDIUM_MOVER,  // Next 30% of picks, 15% of volume
        C_SLOW_MOVER,    // Next 50% of picks, 5% of volume
        D_VERY_SLOW      // Dead stock, < 1% of volume
    }

    public static VelocityClass calculate(MovementHistory history) {
        BigDecimal turnover = history.calculateTurnoverRate();
        Integer picks = history.getPickCount();
        BigDecimal cubic = history.getCubicMovement();

        // Pareto analysis (80/20 rule)
        if (picks > FAST_MOVER_THRESHOLD) {
            return new VelocityClass(A_FAST_MOVER, turnover, picks, cubic);
        } else if (picks > MEDIUM_MOVER_THRESHOLD) {
            return new VelocityClass(B_MEDIUM_MOVER, turnover, picks, cubic);
        } else if (picks > SLOW_MOVER_THRESHOLD) {
            return new VelocityClass(C_SLOW_MOVER, turnover, picks, cubic);
        } else {
            return new VelocityClass(D_VERY_SLOW, turnover, picks, cubic);
        }
    }
}
```

#### Capacity
```java
public class Capacity {
    private Volume volumeCapacity;
    private Weight weightCapacity;
    private Integer unitCapacity;
    private Volume currentVolume;
    private Weight currentWeight;
    private Integer currentUnits;

    public BigDecimal getUtilizationPercentage() {
        BigDecimal volumeUtil = currentVolume.divide(volumeCapacity);
        BigDecimal weightUtil = currentWeight.divide(weightCapacity);
        BigDecimal unitUtil = BigDecimal.valueOf(currentUnits)
            .divide(BigDecimal.valueOf(unitCapacity));

        return Collections.max(Arrays.asList(volumeUtil, weightUtil, unitUtil));
    }

    public boolean canAccommodate(Item item, Quantity quantity) {
        Volume requiredVolume = item.getVolume().multiply(quantity);
        Weight requiredWeight = item.getWeight().multiply(quantity);

        return currentVolume.add(requiredVolume).isLessThan(volumeCapacity)
            && currentWeight.add(requiredWeight).isLessThan(weightCapacity)
            && currentUnits + quantity.getValue() <= unitCapacity;
    }
}
```

#### GoldenZone
```java
public class GoldenZone {
    private HeightRange ergonomicHeight; // 30" to 60" from floor
    private List<LocationCode> locations;
    private AllocationStrategy strategy;

    public boolean isInGoldenZone(LocationCode location) {
        Integer level = location.getLevel();
        return level >= ergonomicHeight.getMin()
            && level <= ergonomicHeight.getMax();
    }

    public List<LocationCode> allocateToGoldenZone(List<SKU> fastMovers) {
        // Allocate fastest movers to most ergonomic positions
        return locations.stream()
            .sorted(byErgonomicScore())
            .limit(fastMovers.size())
            .collect(Collectors.toList());
    }
}
```

### Domain Services

#### SlottingOptimizationService
**Purpose**: Optimizes product placement using ABC analysis

```java
public interface SlottingOptimizationService {
    SlottingPlan optimizeSlotting(List<SKU> skus, List<Location> locations);
    VelocityClass calculateVelocity(SKU sku, MovementHistory history);
    AffinityScore calculateAffinity(SKU sku1, SKU sku2);
    CubicMovement calculateCubicMovement(SKU sku, Period period);
    List<LocationRecommendation> recommendLocations(SKU sku);
}
```

**ABC Slotting Algorithm**:
```java
public class ABCSlottingAlgorithm {
    public SlottingPlan optimize(List<SKUMovement> movements, List<Location> locations) {
        // Step 1: Calculate velocity for each SKU
        Map<SKU, VelocityClass> velocityMap = movements.stream()
            .collect(Collectors.toMap(
                SKUMovement::getSku,
                m -> VelocityClass.calculate(m.getHistory())
            ));

        // Step 2: Sort locations by desirability (golden zone first)
        List<Location> sortedLocations = locations.stream()
            .sorted(Comparator.comparing(this::getLocationScore).reversed())
            .collect(Collectors.toList());

        // Step 3: Assign fast movers to best locations
        SlottingPlan plan = new SlottingPlan();

        velocityMap.entrySet().stream()
            .sorted(Map.Entry.comparingByValue())
            .forEach(entry -> {
                Location bestLocation = findBestLocation(
                    entry.getKey(),
                    entry.getValue(),
                    sortedLocations
                );
                plan.assign(entry.getKey(), bestLocation);
                sortedLocations.remove(bestLocation);
            });

        return plan;
    }

    private Double getLocationScore(Location location) {
        Double score = 0.0;

        // Golden zone bonus
        if (location.isInGoldenZone()) score += 50.0;

        // Proximity to shipping
        score += (100.0 - location.distanceToShipping());

        // Accessibility score
        score += location.getAccessibilityScore() * 10.0;

        return score;
    }
}
```

#### CapacityManagementService
**Purpose**: Manages location capacity and utilization

```java
public interface CapacityManagementService {
    boolean checkCapacity(Location location, Item item, Quantity quantity);
    void reserveCapacity(Location location, Capacity required);
    void releaseCapacity(Location location, Capacity toRelease);
    List<Location> findAvailableLocations(Capacity required);
    UtilizationReport generateUtilizationReport(Zone zone);
}
```

#### LocationConfigurationService
**Purpose**: Manages location setup and configuration

```java
public interface LocationConfigurationService {
    Location createLocation(LocationCode code, LocationType type);
    void configureLocationAttributes(Location location, LocationAttributes attributes);
    void setLocationRestrictions(Location location, List<LocationRestriction> restrictions);
    void assignToZone(Location location, Zone zone);
    void deactivateLocation(Location location, DeactivationReason reason);
}
```

### Domain Events

#### Location Events
```java
public class LocationCreated extends DomainEvent {
    private LocationId locationId;
    private LocationCode code;
    private LocationType type;
    private Zone zone;
}

public class LocationConfigured extends DomainEvent {
    private LocationId locationId;
    private LocationAttributes attributes;
    private List<LocationRestriction> restrictions;
}

public class SlottingOptimized extends DomainEvent {
    private List<SlottingChange> changes;
    private OptimizationMetrics beforeMetrics;
    private OptimizationMetrics afterMetrics;
    private BigDecimal expectedImprovement;
}

public class LocationCapacityExceeded extends DomainEvent {
    private LocationId locationId;
    private Capacity current;
    private Capacity attempted;
}

public class VelocityClassChanged extends DomainEvent {
    private SKU sku;
    private VelocityClass previousClass;
    private VelocityClass newClass;
    private LocationCode recommendedLocation;
}

public class ZoneReconfigured extends DomainEvent {
    private ZoneId zoneId;
    private ZoneConfiguration previousConfig;
    private ZoneConfiguration newConfig;
}
```

### Repository Interfaces

```java
public interface LocationRepository {
    Location save(Location location);
    Optional<Location> findById(LocationId locationId);
    Optional<Location> findByCode(LocationCode code);
    List<Location> findByZone(Zone zone);
    List<Location> findByType(LocationType type);
    List<Location> findAvailable(Capacity required);
    List<Location> findInGoldenZone();
}

public interface ZoneRepository {
    Zone save(Zone zone);
    Optional<Zone> findById(ZoneId zoneId);
    List<Zone> findByType(ZoneType type);
    List<Zone> findAll();
}
```

## Integration Patterns

### Upstream Dependencies
- **Physical Tracking**: Provides location occupancy
- **Inventory**: Provides stock levels per location

### Downstream Dependencies
- All services use location master data

### Events Published
- LocationCreated
- LocationConfigured
- SlottingOptimized
- VelocityClassChanged

### Events Subscribed
- InventoryMoved (from Inventory)
- PickCompleted (from Pick Execution)
- PutAwayCompleted (from Task Execution)

## Business Rules

### Location Configuration Rules
1. **Naming Convention**: Follow warehouse-zone-aisle-bay-level-position
2. **Unique Codes**: No duplicate location codes
3. **Zone Assignment**: Every location must belong to a zone
4. **Capacity Limits**: Cannot exceed physical dimensions
5. **Type Restrictions**: Certain types have specific requirements

### Slotting Rules
1. **ABC Classification**:
   - A items: Golden zone, nearest to shipping
   - B items: Secondary picking areas
   - C items: Upper levels, back areas
   - D items: Deep storage, consider removal
2. **Cubic Movement**: High cubic movement items need larger locations
3. **Affinity**: Frequently picked together items should be near
4. **Weight**: Heavy items on lower levels
5. **Seasonality**: Adjust for seasonal patterns

### Capacity Rules
1. **Utilization Target**: 85% for optimal efficiency
2. **Honeycombing Prevention**: Minimum 65% utilization
3. **Reserve Capacity**: Keep 10% locations empty for flexibility
4. **Weight Limits**: Floor locations: 5000 lbs, upper: 500 lbs
5. **Stacking**: Maximum 3 high for stability

### Golden Zone Rules
1. **Height Range**: 30" to 60" from floor
2. **Priority**: Fastest 20% of SKUs
3. **Ergonomics**: Minimize bending and reaching
4. **Rotation**: Review monthly for changes
5. **Accessibility**: ADA compliant paths

## Performance Optimization

### Caching Strategy
- Cache location hierarchy
- Cache zone configurations
- Cache velocity classifications
- Cache golden zone allocations

### Batch Processing
- Batch slotting optimization (nightly)
- Batch velocity recalculation (weekly)
- Batch capacity updates

### Indexing
- Index by location code
- Index by zone
- Index by velocity class
- Spatial index for proximity queries

## Monitoring & Metrics

### Key Metrics
- Location utilization (%)
- Golden zone efficiency
- Pick path optimization savings
- Slotting compliance rate
- Capacity violations
- Dead location percentage

### SLA Targets
- Location lookup: < 10ms
- Capacity check: < 50ms
- Slotting optimization: < 5 minutes for 10,000 SKUs
- Zone query: < 100ms
- Configuration update: < 500ms