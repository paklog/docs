# Warehouse Operations Service - Domain Architecture & Business Capabilities

## Service Overview

The Warehouse Operations Service manages all warehouse fulfillment activities from order release through packing completion. It orchestrates wave planning, pick list generation, picking execution, quality control, put wall operations, packing, and work assignment across multiple sub-domains in a complex, event-driven architecture.

**Architecture Pattern**: Hexagonal Architecture with Multi-Domain DDD
**Technology Stack**: Spring Boot, Spring Data MongoDB, Spring Kafka, CloudEvents
**Integration Pattern**: Event-Driven Architecture with Multiple Bounded Contexts

---

## Multi-Domain Architecture

### Overview

The Warehouse Operations service is unique in the PakLog ecosystem as it encompasses **multiple bounded contexts** within a single deployment unit. This design reflects the complexity and interconnected nature of warehouse operations.

### Bounded Contexts within Warehouse Operations

1. **Wave Planning Context** - Order batching and wave management
2. **Picking Context** - Pick list generation and execution
3. **Quality Context** - Quality inspection and control
4. **Packing Context** - Order packing operations
5. **Put Wall Context** - Batch picking sortation
6. **Location Context** - Warehouse location management
7. **License Plate Context** - Unit load tracking
8. **Work Management Context** - Work assignment and tracking
9. **Workload Context** - Capacity planning and load balancing
10. **Shared Kernel** - Common domain concepts

---

## Bounded Context: Wave Planning

### Context Boundaries

**Responsibilities (What's IN)**:
- Plan order waves for batch picking optimization
- Apply wave planning strategies (time, carrier, zone, priority)
- Release waves for picking
- Track wave execution progress
- Close completed waves

**External Dependencies (What's OUT)**:
- Order details (Order Management context - external)
- Inventory allocation verification (Inventory context - external)
- Pick list generation (Picking context - internal)

### Ubiquitous Language (Wave Planning)

- **Wave**: Batch of orders grouped for picking optimization
- **Wave Strategy**: Method for grouping orders (time-based, carrier-based, zone-based, etc.)
- **Wave Release**: Making wave available for picking
- **Wave Capacity**: Maximum orders/lines per wave
- **Carrier Cutoff**: Deadline for carrier pickup

### Domain Model (Wave Planning)

#### Wave Aggregate

```java
@AggregateRoot
public class Wave {
    private String waveId;
    private WaveStatus status;
    private List<String> orderIds;
    private WavePriority priority;
    private WaveStrategy strategy;
    private LocalDateTime plannedReleaseTime;
    private LocalDateTime actualReleaseTime;
    private LocalDateTime completedAt;
    private String assignedZone;
    private WaveMetrics metrics;

    // Business methods
    public void release();
    public void addOrder(String orderId);
    public void markInProgress();
    public void markCompleted();
    public void close();
    public boolean hasCapacity(int additionalOrders);

    // Invariants
    private void ensureNotAlreadyReleased();
    private void ensureWithinCapacity();
    private void ensureAllOrdersAllocated();
}
```

**Wave Status**: `PLANNED → RELEASED → IN_PROGRESS → COMPLETED → CLOSED`

**Domain Events**:
- `WavePlannedEvent`
- `WaveReleasedEvent`
- `WaveCompletedEvent`

---

## Bounded Context: Picking

### Context Boundaries

**Responsibilities (What's IN)**:
- Generate pick lists from released waves
- Assign pick lists to pickers
- Execute picking with mobile app guidance
- Track pick progress and completion
- Handle short picks and exceptions
- Optimize pick paths

**External Dependencies (What's OUT)**:
- Wave information (Wave Planning context - internal)
- Inventory transactions (Inventory context - external)
- Location information (Location context - internal)

### Ubiquitous Language (Picking)

- **Pick List**: Set of pick instructions for a picker
- **Pick Instruction**: Single item to be picked (SKU, quantity, location)
- **Pick Path**: Optimized sequence of pick instructions
- **Short Pick**: Picking less than requested quantity
- **Discrete Picking**: One order per pick list
- **Batch Picking**: Multiple orders in one pick list
- **Zone Picking**: Picking limited to specific warehouse zone

### Domain Model (Picking)

#### PickList Aggregate

```java
@AggregateRoot
public class PickList {
    private String pickListId;
    private String waveId;
    private List<String> orderIds;
    private List<PickInstruction> instructions;
    private PickListStatus status;
    private String assignedPickerId;
    private LocalDateTime assignedAt;
    private LocalDateTime startedAt;
    private LocalDateTime completedAt;
    private PickStrategy strategy;

    // Business methods
    public void assignTo(String pickerId);
    public void start();
    public void recordPick(String instructionId, int quantityPicked);
    public void complete();
    public void optimizePickPath(LocationGraph graph);

    // Invariants
    private void ensureCanBeAssigned();
    private void ensureAllInstructionsCompleted();
}
```

**PickList Status**: `PENDING → ASSIGNED → IN_PROGRESS → COMPLETED`

#### PickInstruction Entity

```java
@Entity
public class PickInstruction {
    private String instructionId;
    private String sku;
    private int quantityToPick;
    private int quantityPicked;
    private String location;
    private int sequence;
    private InstructionStatus status;

    public void pick(int quantity);
    public void markShortPick(int actualQuantity, String reason);
    public boolean isComplete();
}
```

**Domain Events**:
- `PickListGeneratedEvent`
- `PickListAssignedEvent`
- `ItemPickedEvent`
- `PickListCompletedEvent`

---

## Bounded Context: Quality

### Context Boundaries

**Responsibilities (What's IN)**:
- Perform quality inspections at configurable checkpoints
- Manage quality holds
- Track defects and root causes
- Execute inspection workflows
- Maintain inspection history

**External Dependencies (What's OUT)**:
- Item information (Product Catalog context - external)
- Inventory holds (Inventory context - external)

### Ubiquitous Language (Quality)

- **Quality Inspection**: Verification of product quality and order accuracy
- **Quality Hold**: Inventory held pending quality resolution
- **Defect**: Quality issue found during inspection
- **Inspection Point**: Stage where inspection occurs (receiving, pre-pack, random)
- **Disposition**: Resolution for defective items (return, discard, sell-as-is)

### Domain Model (Quality)

#### QualityInspection Aggregate

```java
@AggregateRoot
public class QualityInspection {
    private String inspectionId;
    private String orderId;
    private InspectionType type;
    private InspectionStatus status;
    private List<InspectionItem> items;
    private String inspectorId;
    private LocalDateTime inspectedAt;
    private List<DefectRecord> defects;
    private InspectionResult result;

    // Business methods
    public void start(String inspectorId);
    public void inspectItem(String sku, boolean passed);
    public void recordDefect(DefectRecord defect);
    public void complete(InspectionResult result);
    public void createHold(String sku);
}
```

**Domain Events**:
- `QualityInspectionCompletedEvent`
- `QualityHoldCreatedEvent`
- `DefectRecordedEvent`

---

## Bounded Context: Packing

### Context Boundaries

**Responsibilities (What's IN)**:
- Pack orders into cartons
- Verify all items included
- Generate shipping labels
- Weigh packages
- Record packing completion

**External Dependencies (What's OUT)**:
- Carton recommendations (Cartonization context - external)
- Shipping label generation (Shipment context - external)
- Item information (Product Catalog context - external)

### Ubiquitous Language (Packing)

- **Packing Station**: Workstation where packing occurs
- **Carton Selection**: Choosing appropriate box size
- **Void Fill**: Materials to fill empty space in carton
- **Package Weight Verification**: Confirming expected vs. actual weight
- **Pack Verification**: Scanning all items before closing carton

### Domain Model (Packing)

#### PackingWorkOrder Aggregate

```java
@AggregateRoot
public class PackingWorkOrder {
    private String workOrderId;
    private String orderId;
    private List<String> items;
    private String recommendedCartonType;
    private PackingStatus status;
    private String packerId;
    private List<String> scannedItems;
    private Weight actualWeight;
    private LocalDateTime completedAt;

    // Business methods
    public void start(String packerId);
    public void scanItem(String sku);
    public void selectCarton(String cartonType);
    public void weighPackage(Weight weight);
    public void complete();

    // Invariants
    private void ensureAllItemsScanned();
    private void ensureWeightWithinTolerance();
}
```

**Domain Events**:
- `PackingStartedEvent`
- `PackingCompletedEvent`
- `ItemPackedEvent`

---

## Bounded Context: Put Wall

### Context Boundaries

**Responsibilities (What's IN)**:
- Assign orders to put wall slots
- Sort batch-picked items to order slots
- Track put wall slot status
- Detect order completion at put wall

**External Dependencies (What's OUT)**:
- Batch picked items (Picking context - internal)
- Order details (Order Management context - external)

### Ubiquitous Language (Put Wall)

- **Put Wall**: Sortation station with numbered slots
- **Put Wall Slot**: Individual location for one order
- **Sort Operation**: Placing item in correct order slot
- **Slot Assignment**: Mapping order to put wall slot

### Domain Model (Put Wall)

#### PutWall Aggregate

```java
@AggregateRoot
public class PutWall {
    private String putWallId;
    private int numberOfSlots;
    private List<PutWallSlot> slots;
    private String zone;

    // Business methods
    public PutWallSlot assignOrder(String orderId);
    public void sortItem(String slotId, String sku, int quantity);
    public void releaseSlot(String slotId);
}
```

#### PutWallSlot Entity

```java
@Entity
public class PutWallSlot {
    private String slotId;
    private int slotNumber;
    private String assignedOrderId;
    private SlotStatus status;
    private List<SlotItem> items;

    public void addItem(String sku, int quantity);
    public boolean isComplete();
    public void release();
}
```

---

## Bounded Context: Location

### Context Boundaries

**Responsibilities (What's IN)**:
- Manage warehouse location hierarchy
- Track location attributes and capacity
- Optimize product slotting
- Manage location status (active, blocked, maintenance)

**External Dependencies (What's OUT)**:
- Inventory by location (Inventory context - external)

### Ubiquitous Language (Location)

- **Location Hierarchy**: Warehouse → Zone → Aisle → Bin
- **Slotting**: Product placement optimization
- **Pick Face**: Primary picking location
- **Reserve Location**: Bulk storage location
- **Velocity**: Pick frequency (A, B, C classification)

### Domain Model (Location)

#### WarehouseLocation Aggregate

```java
@AggregateRoot
public class WarehouseLocation {
    private String locationId;
    private String warehouseId;
    private String zone;
    private String aisle;
    private String bin;
    private LocationType type; // PICK, RESERVE, STAGE
    private LocationStatus status;
    private Capacity capacity;
    private List<String> restrictions;

    // Business methods
    public void block(String reason);
    public void activate();
    public boolean canStore(String sku, int quantity);
    public boolean isInZone(String zoneId);
}
```

---

## Bounded Context: License Plate

### Context Boundaries

**Responsibilities (What's IN)**:
- Create and manage license plates (LPs)
- Track LP contents
- Track LP movements
- Support nested LPs (pallets containing cases)

**External Dependencies (What's OUT)**:
- Inventory on LP (Inventory context - external)

### Ubiquitous Language (License Plate)

- **License Plate (LP)**: Container tracking identifier
- **LP Contents**: Items and quantities on LP
- **LP Nesting**: LP hierarchy (pallet contains cases)
- **LP Movement**: Transfer of LP between locations

### Domain Model (License Plate)

#### LicensePlate Aggregate

```java
@AggregateRoot
public class LicensePlate {
    private String licensePlateId;
    private LicensePlateType type; // PALLET, CASE, CARTON
    private List<LPItem> contents;
    private String currentLocation;
    private LPStatus status;
    private String parentLicensePlateId; // For nesting

    // Business methods
    public void addItem(String sku, int quantity);
    public void moveTo(String newLocation);
    public void close();
    public void open();
}
```

---

## Bounded Context: Work Management

### Context Boundaries

**Responsibilities (What's IN)**:
- Manage work queues by type
- Assign work to associates
- Track work completion
- Monitor work aging and SLAs

**External Dependencies (What's OUT)**:
- Associate information (HR systems - external)

### Ubiquitous Language (Work Management)

- **Work Item**: Unit of work to be performed
- **Work Queue**: Collection of pending work items
- **Work Type**: Category of work (PICK, PACK, QC, PUTAWAY, REPLENISH, COUNT)
- **Work Assignment**: Linking work to an associate
- **Work Aging**: Time work item has been in queue

### Domain Model (Work Management)

#### WorkItem Aggregate

```java
@AggregateRoot
public class WorkItem {
    private String workItemId;
    private WorkType type;
    private Priority priority;
    private WorkStatus status;
    private String assignedTo;
    private LocalDateTime createdAt;
    private LocalDateTime assignedAt;
    private LocalDateTime completedAt;
    private String referenceId; // Pick list ID, order ID, etc.

    // Business methods
    public void assignTo(String associateId);
    public void start();
    public void complete();
    public Duration getAge();
    public boolean isOverdue(Duration sla);
}
```

---

## Bounded Context: Workload

### Context Boundaries

**Responsibilities (What's IN)**:
- Plan labor capacity
- Balance workload across associates
- Track productivity metrics
- Identify bottlenecks

**External Dependencies (What's OUT)**:
- Work items (Work Management context - internal)

### Ubiquitous Language (Workload)

- **Capacity**: Available labor hours
- **Workload**: Amount of work to be performed
- **Productivity**: Work completed per time unit
- **Load Balancing**: Distributing work evenly

---

## Shared Kernel (Common Concepts)

### Shared Across All Contexts

**Common Value Objects**:

```java
@ValueObject
public class WarehouseId {
    private String warehouseCode;
    private String warehouseName;
}

@ValueObject
public class AssociateId {
    private String employeeId;
    private String name;
}

@ValueObject
public enum Priority {
    CRITICAL(0),
    HIGH(1),
    NORMAL(2),
    LOW(3);

    private final int level;
}
```

---

## Application Layer (Cross-Context)

### Orchestration Services

#### WarehouseFulfillmentOrchestrator

```java
@ApplicationService
public class WarehouseFulfillmentOrchestrator {

    public void processReleasedOrder(FulfillmentOrderReleasedEvent event) {
        // 1. Trigger wave planning
        // 2. When wave released → generate pick lists
        // 3. Assign pick lists to pickers
        // 4. When picking complete → route to put wall or packing
        // 5. When packing complete → publish event
    }
}
```

---

## Business Capabilities (Aggregated Across Contexts)

### L1: Warehouse Fulfillment Operations

Comprehensive management of warehouse fulfillment from order release to packing completion.

---

### L2: Wave Planning & Management

#### L3.1: Wave Creation & Planning
- Apply planning strategies
- Capacity-based wave sizing
- Priority-based wave ordering

#### L3.2: Wave Release Management
- Validate inventory allocation
- Trigger pick list generation
- Schedule wave execution

#### L3.3: Wave Execution Tracking
- Monitor progress
- Calculate completion percentage
- Track metrics

#### L3.4: Wave Optimization Strategies
- Time-based waves
- Carrier-based waves
- Zone-based waves
- Priority-based waves
- Item affinity waves

---

### L2: Pick List Management & Execution

#### L3.5: Pick List Generation
- Create from released waves
- Support discrete, batch, zone picking
- Optimize pick sequences

#### L3.6: Pick List Assignment
- Assign to available pickers
- Load balancing
- Skill-based assignment

#### L3.7: Pick Execution & Confirmation
- Mobile-guided picking
- Barcode verification
- Location verification
- Short pick handling

#### L3.8: Pick Path Optimization
- Minimize travel distance
- One-way aisle support
- Vertical slotting

---

### L2: Quality Control & Inspection

#### L3.9: Quality Inspection Workflow
- Configurable inspection points
- Checklist-based inspections
- Pass/fail/hold decisions

#### L3.10: Defect Management
- Defect categorization
- Root cause tracking
- Vendor quality scorecards

#### L3.11: Quality Hold Management
- Create and manage holds
- Approval workflows
- Disposition tracking

---

### L2: Put Wall & Sorting Operations

#### L3.12: Put Wall Assignment
- Order-to-slot mapping
- Slot availability tracking

#### L3.13: Item Sorting to Put Wall
- Barcode-guided sorting
- Order completion detection

---

### L2: Packing Operations

#### L3.14: Packing Station Workflow
- System-guided packing
- Carton selection
- Item verification
- Label generation

#### L3.15: Carton Selection & Materials Management
- Follow cartonization recommendations
- Track material usage
- Cost allocation

#### L3.16: Package Weight Verification
- Verify against expected weight
- Tolerance-based checking
- Exception handling

---

### L2: Location Management

#### L3.17: Location Hierarchy Management
- Define warehouse structure
- Manage location attributes
- Track location status

#### L3.18: Slotting Optimization
- Velocity-based slotting
- ABC classification
- Affinity slotting

---

### L2: Work Assignment & Management

#### L3.19: Work Queue Management
- Manage queues by type
- Priority-based ordering
- SLA monitoring

#### L3.20: Labor Productivity Tracking
- Real-time dashboards
- Performance metrics
- Gamification

---

### L2: License Plate Management

#### L3.21: LP Creation & Assignment
- Generate unique LPs
- Track contents
- Support nesting

---

### L2: Mobile Application Support

#### L3.22: Mobile Picking Application
- Task assignment
- Turn-by-turn navigation
- Barcode scanning
- Exception reporting

---

## Integration Patterns

### Context Mapping (External)

#### Order Management (Upstream - Customer/Supplier)
- **Type**: Customer/Supplier
- **Integration**: Event-driven
- **Contract**: Warehouse consumes order release events

#### Inventory (Partner - Partnership)
- **Type**: Partnership
- **Integration**: Event-driven (bi-directional)
- **Collaboration**: Inventory transactions flow both ways

#### Product Catalog (Upstream - Conformist)
- **Type**: Conformist
- **Integration**: REST API queries

#### Cartonization (Upstream - Customer/Supplier)
- **Type**: Customer/Supplier
- **Integration**: Event-driven
- **Contract**: Consume packing solutions

#### Shipment (Downstream - Customer/Supplier)
- **Type**: Customer/Supplier
- **Integration**: Event-driven
- **Contract**: Publish packing completion events

---

## Event Schemas

### WaveReleasedEvent

```json
{
  "specversion": "1.0",
  "type": "com.paklog.warehouse.wave.released",
  "source": "warehouse-operations-service",
  "id": "evt-wave-123",
  "time": "2025-10-18T10:00:00Z",
  "data": {
    "waveId": "WAVE-12345",
    "orderIds": ["ORD-001", "ORD-002", "ORD-003"],
    "priority": "NORMAL",
    "strategy": "ZONE_BASED",
    "assignedZone": "Z01",
    "releasedAt": "2025-10-18T10:00:00Z"
  }
}
```

### PickListCompletedEvent

```json
{
  "specversion": "1.0",
  "type": "com.paklog.warehouse.picklist.completed",
  "source": "warehouse-operations-service",
  "id": "evt-picklist-456",
  "time": "2025-10-18T11:30:00Z",
  "data": {
    "pickListId": "PL-67890",
    "waveId": "WAVE-12345",
    "orderIds": ["ORD-001"],
    "pickerId": "picker-123",
    "completedAt": "2025-10-18T11:30:00Z",
    "totalPicks": 15,
    "shortPicks": 0
  }
}
```

### PackingCompletedEvent

```json
{
  "specversion": "1.0",
  "type": "com.paklog.warehouse.packing.completed",
  "source": "warehouse-operations-service",
  "id": "evt-packing-789",
  "time": "2025-10-18T12:00:00Z",
  "data": {
    "orderId": "ORD-001",
    "packerId": "packer-456",
    "packages": [
      {
        "packageId": "PKG-001",
        "cartonType": "SMALL-BOX-001",
        "weight": {"value": 5.2, "unit": "POUNDS"}
      }
    ],
    "completedAt": "2025-10-18T12:00:00Z"
  }
}
```

---

## Quality Attributes

### Complexity Management
- **Multiple Contexts**: Clear boundaries between sub-domains
- **Shared Kernel**: Minimal shared concepts
- **Event Choreography**: Loose coupling via events

### Performance
- **Throughput**: 10,000+ orders per day
- **Pick Rate**: 100-150 picks per hour per picker
- **Pack Rate**: 30-40 packs per hour per packer

### Scalability
- **Horizontal**: Stateless service design
- **Event Partitioning**: Kafka partitions by warehouse
- **Database**: MongoDB sharding by warehouse

---

## Summary

The Warehouse Operations Service is the most complex service in PakLog:

- **Multi-Domain Architecture**: 10 bounded contexts within one service
- **Rich Domain Models**: Each context has its own aggregates and events
- **Event-Driven Choreography**: Contexts coordinate via events
- **Clean Boundaries**: Clear responsibilities per context
- **Operational Excellence**: High throughput and productivity

Business Impact: 10,000+ orders/day, >99.9% accuracy, 100-150 picks/hour, >85% labor utilization, 2-4 hour cycle time from wave release to pack complete.
