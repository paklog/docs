# Pack & Ship Service - Domain-Driven Design

## Bounded Context: Packing Station & Shipping Operations

The Pack & Ship Service manages packing station operations, carton optimization, shipping label generation, and carrier integration for outbound shipments.

## Domain Model

### Aggregates

#### Package (Aggregate Root)
**Purpose**: Represents a packed shipment ready for carrier pickup

**Properties**:
```java
public class Package {
    private PackageId packageId;
    private OrderId orderId;
    private PackageStatus status;
    private CartonType cartonType;
    private List<PackedItem> items;
    private PackageDimensions actualDimensions;
    private Weight actualWeight;
    private ShippingLabel label;
    private Carrier carrier;
    private TrackingNumber trackingNumber;
    private PackingStation station;
    private QualityChecks qualityChecks;
    private PackageMetrics metrics;
}
```

**Invariants**:
- Weight must match actual measured weight
- All order items must be packed
- Cannot ship without label
- Dimensions must not exceed carrier limits
- Must pass quality checks before sealing

**State Transitions**:
```
CREATED -> PACKING -> SEALED -> LABELED -> SHIPPED
    |         |          |
    |         |          +-> QUALITY_HOLD
    |         |
    |         +-> CANCELLED
    |
    +-> REJECTED
```

#### PackingStation (Entity)
**Purpose**: Physical packing workstation management

**Properties**:
```java
public class PackingStation {
    private StationId stationId;
    private StationType type;
    private StationStatus status;
    private PackerInfo currentPacker;
    private List<Equipment> availableEquipment;
    private Queue<PackingTask> taskQueue;
    private StationConfiguration configuration;
    private PerformanceMetrics metrics;
}
```

#### ShippingLabel (Entity)
**Purpose**: Carrier-specific shipping label generation

**Properties**:
```java
public class ShippingLabel {
    private LabelId labelId;
    private Carrier carrier;
    private TrackingNumber trackingNumber;
    private byte[] labelImage;
    private LabelFormat format;
    private ShippingMethod method;
    private ServiceLevel serviceLevel;
    private CostBreakdown costs;
}
```

### Value Objects

#### PackedItem
```java
public class PackedItem {
    private SKU sku;
    private Quantity quantity;
    private SerialNumbers serialNumbers;
    private PackingPosition position;
    private ItemCondition condition;
    private PackingMaterial protection;
}
```

#### CartonType
```java
public class CartonType {
    private String cartonId;
    private Dimensions internalDimensions;
    private Weight maxWeight;
    private CartonCategory category;
    private BigDecimal unitCost;
    private Boolean requiresPadding;
    private List<CompatibleItems> restrictions;
}
```

#### PackingMaterial
```java
public class PackingMaterial {
    private MaterialType type;
    private Quantity quantity;
    private BigDecimal cost;

    public enum MaterialType {
        BUBBLE_WRAP,
        PACKING_PEANUTS,
        AIR_PILLOWS,
        PAPER_FILL,
        FOAM_INSERT,
        CORRUGATED_DIVIDER
    }
}
```

#### QualityChecks
```java
public class QualityChecks {
    private Boolean itemVerification;
    private Boolean weightVerification;
    private Boolean sealIntegrity;
    private Boolean labelReadability;
    private Boolean fragilityCompliance;
    private List<QualityIssue> issues;
    private QualityScore score;
}
```

#### ShippingMethod
```java
public class ShippingMethod {
    private Carrier carrier;
    private ServiceLevel serviceLevel;
    private DeliverySpeed speed;
    private Boolean requiresSignature;
    private Insurance insurance;
    private SpecialHandling specialHandling;
}
```

### Domain Services

#### PackingOptimizationService
**Purpose**: Optimizes item arrangement in cartons

```java
public interface PackingOptimizationService {
    PackingPlan optimizePacking(List<Item> items, List<CartonType> available);
    CartonType selectOptimalCarton(List<Item> items);
    PackingInstructions generateInstructions(PackingPlan plan);
    void validatePackingConstraints(Package package);
}
```

**3D Bin Packing Algorithm**:
```java
public class BinPacking3D {
    public PackingPlan pack(List<Item> items, Carton carton) {
        items.sort(byVolumeDescending());
        List<PlacedItem> placedItems = new ArrayList<>();
        List<Space> availableSpaces = Arrays.asList(carton.getFullSpace());

        for (Item item : items) {
            Space bestSpace = findBestFitSpace(item, availableSpaces);
            if (bestSpace != null) {
                PlacedItem placed = placeItem(item, bestSpace);
                placedItems.add(placed);
                updateAvailableSpaces(availableSpaces, placed);
            }
        }

        return new PackingPlan(placedItems, carton);
    }

    private Space findBestFitSpace(Item item, List<Space> spaces) {
        return spaces.stream()
            .filter(space -> space.canFit(item))
            .min(Comparator.comparing(space -> space.getWastedVolume(item)))
            .orElse(null);
    }
}
```

#### LabelGenerationService
**Purpose**: Generates carrier-compliant shipping labels

```java
public interface LabelGenerationService {
    ShippingLabel generateLabel(Package package, Carrier carrier);
    TrackingNumber allocateTrackingNumber(Carrier carrier);
    byte[] renderLabel(ShippingLabel label, LabelFormat format);
    void cancelLabel(ShippingLabel label);
}
```

#### QualityControlService
**Purpose**: Ensures package quality standards

```java
public interface QualityControlService {
    QualityChecks performQualityCheck(Package package);
    Boolean validateWeight(Package package, Weight measured);
    void flagQualityIssue(Package package, QualityIssue issue);
    QualityScore calculateQualityScore(QualityChecks checks);
}
```

### Domain Events

#### Packing Events
```java
public class PackingStarted extends DomainEvent {
    private PackageId packageId;
    private OrderId orderId;
    private StationId stationId;
    private PackerId packerId;
}

public class ItemPacked extends DomainEvent {
    private PackageId packageId;
    private SKU sku;
    private Quantity quantity;
    private PackingPosition position;
}

public class PackageSealed extends DomainEvent {
    private PackageId packageId;
    private Weight actualWeight;
    private Dimensions actualDimensions;
    private LocalDateTime sealTime;
}

public class LabelGenerated extends DomainEvent {
    private PackageId packageId;
    private TrackingNumber trackingNumber;
    private Carrier carrier;
    private ShippingMethod method;
}

public class PackageShipped extends DomainEvent {
    private PackageId packageId;
    private TrackingNumber trackingNumber;
    private LocalDateTime shipTime;
    private Carrier carrier;
}

public class QualityCheckFailed extends DomainEvent {
    private PackageId packageId;
    private List<QualityIssue> issues;
    private QualityAction requiredAction;
}
```

### Repository Interfaces

```java
public interface PackageRepository {
    Package save(Package package);
    Optional<Package> findById(PackageId packageId);
    List<Package> findByOrder(OrderId orderId);
    List<Package> findByStatus(PackageStatus status);
    List<Package> findAwaitingShipment();
}

public interface PackingStationRepository {
    PackingStation save(PackingStation station);
    Optional<PackingStation> findById(StationId stationId);
    Optional<PackingStation> findAvailableStation(StationType type);
    List<PackingStation> findActiveStations();
}
```

## Integration Patterns

### Upstream Dependencies
- **Pick Execution**: Receives picked items
- **Order Management**: Gets order details
- **Cartonization**: Receives packing recommendations

### Downstream Dependencies
- **Shipment Transportation**: Sends shipment details
- **Inventory**: Updates shipped quantities

### Carrier Integration
```java
public interface CarrierIntegrationPort {
    RateQuote getShippingRate(Package package, ShippingMethod method);
    TrackingNumber createShipment(Package package);
    byte[] generateLabel(ShipmentRequest request);
    void voidShipment(TrackingNumber tracking);
    ManifestResult closeManifest(List<Package> packages);
}
```

## Business Rules

### Packing Rules
1. **Fragile Items**: Must be on top with extra padding
2. **Hazmat**: Requires special packaging and labels
3. **Weight Distribution**: Heavy items at bottom
4. **Orientation**: Respect "This Side Up" requirements
5. **Compatibility**: Don't pack incompatible items together

### Carton Selection Rules
1. **Size Optimization**: Smallest carton that fits
2. **Weight Limits**: Cannot exceed carrier limits
3. **Cost Optimization**: Balance carton vs shipping cost
4. **Sustainability**: Prefer eco-friendly options
5. **Protection**: Match protection to item fragility

### Quality Control Rules
1. **Weight Tolerance**: ±2% of calculated weight
2. **Item Verification**: 100% scan verification
3. **Seal Inspection**: Visual and pressure test
4. **Label Quality**: Barcode scan test required
5. **Photo Documentation**: Required for high-value items

### Shipping Rules
1. **Cutoff Times**: Must ship before carrier pickup
2. **Service Level**: Match customer selection
3. **Insurance**: Required for items > $500
4. **Signature**: Required for items > $250
5. **Manifest**: Close daily at carrier cutoff

## Performance Optimization

### Packing Optimization
- Pre-calculate common item combinations
- Cache carton recommendations
- Parallel packing for multi-package orders
- Batch label printing

### Station Management
- Dynamic station assignment
- Load balancing across stations
- Equipment pre-positioning
- Task pre-fetching

### Carrier Integration
- Batch rate shopping
- Label pre-generation
- Cached tracking numbers
- Async manifest closing

## Monitoring & Metrics

### Key Metrics
- Pack rate (packages/hour)
- First-pass quality rate
- Carton utilization (%)
- Label generation time
- Shipping cost per package
- Damage rate

### SLA Targets
- Packing time: < 3 minutes/package
- Label generation: < 2 seconds
- Quality check: < 30 seconds
- Carton selection: < 1 second
- Pack accuracy: > 99.9%