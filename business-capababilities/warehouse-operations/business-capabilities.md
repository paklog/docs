# Warehouse Operations Service - Business Capabilities

**Service Overview**: The Warehouse Operations Service manages all warehouse fulfillment activities from order release through packing completion. It orchestrates wave planning, pick list generation, picking execution, quality control, put wall operations, packing, and work assignment across multiple sub-domains in a complex, event-driven architecture.

**Architecture**: Hexagonal Architecture with Multi-Domain DDD
**Technology Stack**: Spring Boot, Spring Data MongoDB, Spring Kafka, CloudEvents
**Domain Model**: Multiple bounded contexts (Wave, PickList, Quality, Location, Work, etc.)

---

## L1: Warehouse Fulfillment Operations

### L1.1: Description
Comprehensive management of warehouse fulfillment operations including order wave planning, pick list generation and execution, quality control, packing, and work assignment to optimize warehouse productivity and ensure accurate order fulfillment.

### L1.2: Strategic Value
- **Operational Efficiency**: Optimize warehouse labor and equipment utilization
- **Order Accuracy**: Ensure >99.9% picking and packing accuracy
- **Throughput**: Maximize orders processed per hour
- **Labor Productivity**: Optimize picker and packer productivity
- **Customer Satisfaction**: Fast, accurate fulfillment
- **Scalability**: Support peak volume periods (holidays, sales events)

---

## L2: Wave Planning & Management

### L2.1: Description
Plan and execute order waves to optimize batch picking operations, group similar orders, and balance workload across warehouse resources.

### L2.2: Business Value
- Reduce picker travel time through batch picking
- Balance workload across warehouse zones and pickers
- Prioritize urgent orders while maintaining efficiency
- Optimize resource utilization during peak and off-peak periods

### L2.3: Wave Planning Strategies

The system supports multiple wave planning strategies that can be combined:

1. **Time-Based Waves**: Group orders by cutoff times for carrier pickups
2. **Carrier-Based Waves**: Group orders by shipping carrier
3. **Zone-Based Waves**: Group orders by warehouse zone for pick efficiency
4. **Priority-Based Waves**: Prioritize rush/express orders
5. **Capacity-Based Waves**: Limit wave size based on available resources
6. **Item Affinity Waves**: Group orders with similar items

### L2.4: L3 Capabilities

#### L3.1.1: Wave Creation & Planning
**Description**: Create order waves using configurable planning strategies to optimize picking efficiency.

**Technical Implementation**:
- `Wave` aggregate as root entity
- `WavePlanningService` orchestrates wave creation
- Multiple planning strategy implementations
- Configurable wave parameters (size, timing, zone)
- MongoDB persistence with event publishing

**Business Rules**:
- Waves have maximum order count (configurable, e.g., 100 orders)
- Waves respect carrier cutoff times
- Priority orders always included in earliest waves
- Cannot add orders to released waves
- Waves must be released before picking can begin

**Domain Model**:
```java
@AggregateRoot
class Wave {
  private String waveId;
  private WaveStatus status; // PLANNED, RELEASED, IN_PROGRESS, COMPLETED, CLOSED
  private List<String> orderIds;
  private WavePriority priority;
  private LocalDateTime plannedReleaseTime;
  private LocalDateTime actualReleaseTime;
  private LocalDateTime completedAt;
  private WaveStrategy strategy;
  private String assignedZone;
}
```

**Wave Status Flow**:
`PLANNED` → `RELEASED` → `IN_PROGRESS` → `COMPLETED` → `CLOSED`

**Key Metrics**:
- Waves created per day
- Average orders per wave
- Wave planning time
- Wave size distribution

**Domain Events**:
- `WavePlannedEvent`
- `WaveReleasedEvent`

**Related Services**: Order Management (order details)

---

#### L3.1.2: Wave Release Management
**Description**: Release planned waves to trigger pick list generation and picking activities.

**Technical Implementation**:
- State transition from PLANNED to RELEASED
- Automatic pick list generation on release
- Inventory allocation verification before release
- Work assignment trigger

**Business Rules**:
- Only PLANNED waves can be released
- All orders must have inventory allocated
- Release time can be scheduled or immediate
- Released waves cannot be modified
- Triggers downstream picking workflow

**Key Metrics**:
- Time from plan to release
- Release success rate
- Orders released per hour

**Domain Events**:
- `WaveReleasedEvent` - Triggers pick list generation

**Related Services**:
- Inventory (allocation verification)
- Internal: PickList domain (pick list generation)

---

#### L3.1.3: Wave Execution Tracking
**Description**: Track wave progress through picking and packing stages.

**Technical Implementation**:
- Aggregate pick list status into wave progress
- Real-time progress monitoring
- Completion percentage calculation
- Estimated completion time

**Business Rules**:
- Wave IN_PROGRESS when first pick list starts
- Wave COMPLETED when all pick lists completed
- Wave CLOSED after final reconciliation
- Track partial completion for reporting

**Progress Metrics**:
- Lines picked vs. total lines
- Orders completed vs. total orders
- Time elapsed vs. estimated time
- Picker productivity

**Key Metrics**:
- Average wave completion time
- Wave efficiency (items per hour)
- In-progress wave count

**Related Services**: Analytics (operational dashboards)

---

#### L3.1.4: Wave Optimization Strategies
**Description**: Apply optimization algorithms to minimize picker travel time and maximize efficiency.

**Technical Implementation**:
- Item affinity analysis (frequently ordered together)
- Zone-based grouping
- Order consolidation
- Carrier cutoff optimization
- Machine learning for continuous improvement (future)

**Optimization Goals**:
1. **Minimize Travel**: Reduce picker walking distance
2. **Balance Load**: Distribute work evenly across pickers
3. **Meet SLAs**: Ensure carrier cutoffs met
4. **Maximize Throughput**: Process maximum orders per hour

**Business Rules**:
- Priority orders never delayed for optimization
- Zone constraints respected
- Equipment availability considered
- Picker skill levels matched to work

**Key Metrics**:
- Average picker travel distance per wave
- Orders per labor hour
- Wave efficiency improvement over baseline

**Related Services**: None (internal optimization)

---

## L2: Pick List Management & Execution

### L2.1: Description
Generate, assign, and execute pick lists for order fulfillment, supporting multiple picking strategies including discrete order picking, batch picking, and zone picking.

### L2.2: Business Value
- Optimize picking efficiency through intelligent pick sequencing
- Support multiple picking methodologies
- Real-time pick progress tracking
- Minimize picking errors through directed workflows

### L2.3: L3 Capabilities

#### L3.2.1: Pick List Generation
**Description**: Automatically generate pick lists from released waves with optimized pick sequences.

**Technical Implementation**:
- `PickList` aggregate created from wave orders
- `PickInstruction` entities for each line item
- Pick path optimization algorithms
- Support for discrete and batch picking

**Business Rules**:
- One pick list per picker (discrete) or multiple orders (batch)
- Pick instructions ordered by warehouse location
- Each instruction specifies SKU, quantity, location
- Cannot modify pick list after assignment
- Must be assigned to picker before execution

**Domain Model**:
```java
@AggregateRoot
class PickList {
  private String pickListId;
  private String waveId;
  private List<String> orderIds;
  private List<PickInstruction> instructions;
  private PickListStatus status; // PENDING, ASSIGNED, IN_PROGRESS, COMPLETED
  private String assignedPickerId;
  private LocalDateTime assignedAt;
  private LocalDateTime startedAt;
  private LocalDateTime completedAt;
}

@Entity
class PickInstruction {
  private String instructionId;
  private String sku;
  private int quantityToPick;
  private int quantityPicked;
  private String location;
  private int sequence;
  private InstructionStatus status; // PENDING, PICKED, SHORT_PICKED, SKIPPED
}
```

**Pick List Types**:
1. **Discrete**: One pick list per order
2. **Batch**: Multiple orders in single pick list
3. **Zone**: Pick lists scoped to warehouse zone

**Key Metrics**:
- Pick lists generated per wave
- Average instructions per pick list
- Pick list generation time

**Domain Events**:
- `PickListGeneratedEvent`

**Related Services**: None (internal generation)

---

#### L3.2.2: Pick List Assignment
**Description**: Assign pick lists to available pickers based on workload, skill, and location.

**Technical Implementation**:
- Assignment service matches pick lists to pickers
- Picker availability tracking
- Skill-based assignment (if applicable)
- Load balancing across pickers

**Business Rules**:
- Pickers can only have one active pick list at a time
- Assignment considers picker location proximity
- Priority pick lists assigned first
- Cannot reassign in-progress pick lists (without cancellation)

**Assignment Strategies**:
- **Round Robin**: Distribute evenly
- **Skill-Based**: Match picker expertise to work
- **Location-Based**: Assign to nearest picker
- **Performance-Based**: High performers get more work

**Key Metrics**:
- Average picker utilization
- Time from generation to assignment
- Assignment balance across pickers

**Domain Events**:
- `PickListAssignedEvent`

**Related Services**: Mobile app (picker notification)

---

#### L3.2.3: Pick Execution & Confirmation
**Description**: Support mobile-guided picking execution with real-time confirmation and exception handling.

**Technical Implementation**:
- Mobile app integration for pickers
- Barcode scanning for item verification
- Real-time pick confirmation
- Short pick and exception handling
- Location verification

**Business Rules**:
- Must scan item barcode to confirm pick
- Location verification required
- Partial picks (short picks) allowed with reason code
- Cannot skip items without manager approval
- All picks create inventory transactions

**Pick Verification**:
1. Navigate to location (guided by app)
2. Verify location barcode
3. Scan item barcode
4. Confirm quantity
5. Move to next pick

**Exception Types**:
- **Short Pick**: Insufficient quantity at location
- **Wrong Item**: Item at location doesn't match
- **Damaged Item**: Item damaged, cannot pick
- **Empty Location**: No item found at location

**Key Metrics**:
- Picks per hour per picker
- Pick accuracy rate (target: >99.9%)
- Short pick rate
- Location verification compliance

**Domain Events**:
- `ItemPickedEvent` - Published for each pick
- `PickListCompletedEvent` - All instructions completed

**Related Services**:
- Inventory (inventory transactions)
- Order Management (pick completion notifications)

---

#### L3.2.4: Pick Path Optimization
**Description**: Optimize the sequence of pick instructions to minimize travel time.

**Technical Implementation**:
- Warehouse layout model (aisles, bins)
- Traveling salesman problem (TSP) algorithm
- Zone-based sequencing
- Vertical slotting consideration

**Business Rules**:
- Sequence picks to minimize total distance
- Consider warehouse flow patterns (one-way aisles)
- Heavy items picked first (bottom of cart)
- Fragile items picked last (top of cart)

**Optimization Factors**:
- Physical distance between locations
- Aisle direction (one-way vs. two-way)
- Vertical position (avoid excessive reaching)
- Item characteristics (weight, fragility)

**Key Metrics**:
- Average travel distance per pick list
- Time savings vs. unoptimized path
- Picker feedback on path quality

**Related Services**: None (internal optimization)

---

## L2: Quality Control & Inspection

### L2.1: Description
Perform quality inspections at various stages of the fulfillment process to ensure product quality and order accuracy.

### L2.2: Business Value
- Prevent shipping of damaged or defective products
- Ensure order accuracy before packing
- Reduce customer returns and complaints
- Maintain brand reputation
- Support compliance requirements

### L2.3: L3 Capabilities

#### L3.3.1: Quality Inspection Workflow
**Description**: Execute quality control checks at configurable inspection points in the fulfillment process.

**Technical Implementation**:
- `QualityInspection` aggregate manages inspection process
- Configurable inspection points (post-pick, pre-pack, random)
- Checklist-based inspections
- Photographic evidence capture
- Pass/fail/hold decisions

**Inspection Points**:
1. **Receiving Inspection**: Inbound goods quality check
2. **Pick Verification**: Random pick accuracy check
3. **Pre-Pack Inspection**: Order accuracy before packing
4. **Random Sampling**: Statistical quality control
5. **Damage Inspection**: Damaged goods assessment

**Business Rules**:
- Failed inspections create quality holds
- Photographic evidence required for failures
- Inspection results recorded permanently
- Failed items cannot proceed to packing
- Inspector ID captured for accountability

**Domain Model**:
```java
@AggregateRoot
class QualityInspection {
  private String inspectionId;
  private String orderId;
  private InspectionType type;
  private InspectionStatus status; // PENDING, IN_PROGRESS, PASSED, FAILED, ON_HOLD
  private List<InspectionItem> items;
  private String inspectorId;
  private LocalDateTime inspectedAt;
  private List<DefectRecord> defects;
  private String resolution;
}

@Entity
class DefectRecord {
  private String defectType; // DAMAGE, WRONG_ITEM, QUANTITY_MISMATCH, etc.
  private String description;
  private String photoUrl;
  private DefectSeverity severity;
}
```

**Key Metrics**:
- Inspection pass rate (target: >98%)
- Average inspection time
- Defect rate by type
- Inspector productivity

**Domain Events**:
- `QualityInspectionCompletedEvent`
- `QualityHoldCreatedEvent`

**Related Services**: Inventory (damaged goods adjustments)

---

#### L3.3.2: Defect Management
**Description**: Track, categorize, and manage product defects found during quality inspections.

**Technical Implementation**:
- Defect categorization and severity assignment
- Root cause analysis tracking
- Defect trending and analytics
- Vendor quality scorecards

**Defect Types**:
- **Damage**: Physical damage (crushed, torn, broken)
- **Wrong Item**: Item mismatch vs. expected
- **Quantity Mismatch**: Quantity incorrect
- **Expiration**: Expired or near-expiry products
- **Labeling**: Incorrect or missing labels
- **Quality**: Product quality issues

**Defect Severity**:
- **CRITICAL**: Cannot ship, must replace/discard
- **MAJOR**: Significant issue, requires decision
- **MINOR**: Cosmetic issue, may ship with discount
- **OBSERVATION**: Note for future reference

**Business Rules**:
- Critical defects trigger immediate hold
- All defects photographically documented
- Defect trends trigger vendor escalation
- Disposal authority based on defect value

**Key Metrics**:
- Defects per 1000 units processed
- Defect cost impact
- Defect resolution time
- Vendor quality scores

**Related Services**: Vendor management (quality feedback)

---

#### L3.3.3: Quality Hold Management
**Description**: Manage inventory holds for items failing quality inspections pending resolution.

**Technical Implementation**:
- Quality hold status on inventory
- Hold reason code and documentation
- Approval workflow for hold release
- Disposition tracking (return, discard, sell-as-is)

**Business Rules**:
- Held inventory excluded from ATP
- Holds require manager approval to release
- Hold duration tracked and reported
- Disposition documented for audit

**Hold Dispositions**:
- **RETURN_TO_VENDOR**: Return defective goods
- **DISCARD**: Scrap/dispose of item
- **SELL_AS_IS**: Discount and sell
- **REWORK**: Repair/repackage and release
- **RELEASE**: No action, release hold

**Key Metrics**:
- Inventory on hold (value and units)
- Average hold duration
- Hold disposition breakdown
- Hold release approval time

**Related Services**:
- Inventory (hold status updates)
- Vendor management (returns)

---

## L2: Put Wall & Sorting Operations

### L2.1: Description
Manage put wall operations for batch picking, where picked items are sorted into individual orders at a put wall station.

### L2.2: Business Value
- Enable efficient batch picking (reduce travel time)
- Support high-throughput order sorting
- Optimize packing station workflow
- Balance picking vs. sorting labor

### L2.3: L3 Capabilities

#### L3.4.1: Put Wall Assignment
**Description**: Assign orders to put wall locations for sorting and consolidation.

**Technical Implementation**:
- Put wall slot assignment algorithm
- Order-to-slot mapping
- Real-time slot availability tracking
- Multi-order batching

**Business Rules**:
- One order per put wall slot
- Slots assigned sequentially
- Slot released when order complete
- Maximum slot hold time (configurable)

**Key Metrics**:
- Put wall utilization rate
- Average orders per batch
- Slot turnover rate

**Related Services**: None (internal workflow)

---

#### L3.4.2: Item Sorting to Put Wall
**Description**: Sort batch-picked items to individual order slots at put wall.

**Technical Implementation**:
- Barcode scanning for item and slot verification
- Real-time order completion detection
- Sorting error detection
- Mobile or fixed workstation support

**Business Rules**:
- Must scan item and slot for each sort
- Incorrect slot triggers alert
- Order complete when all items sorted
- Sorted orders queue for packing

**Sorting Process**:
1. Scan batch picked item
2. System displays destination slot
3. Place item in slot
4. Scan slot to confirm
5. Repeat for all items
6. System detects order completion

**Key Metrics**:
- Sort rate (items per hour)
- Sorting accuracy
- Average time at put wall per order

**Related Services**: None (internal workflow)

---

## L2: Packing Operations

### L2.1: Description
Pack orders into cartons with appropriate materials, generate shipping labels, and prepare for shipment.

### L2.2: Business Value
- Ensure products protected during shipment
- Optimize packaging materials usage
- Generate accurate shipping labels
- Support quality packing standards

### L2.3: L3 Capabilities

#### L3.5.1: Packing Station Workflow
**Description**: Guide packers through the packing process with system-directed workflow.

**Technical Implementation**:
- Packing station application
- Integration with cartonization service
- Label printer integration
- Packing materials inventory
- Real-time packing instructions

**Business Rules**:
- Verify all items scanned before closing carton
- Use carton recommended by cartonization service
- Generate label only after packing complete
- Photograph package if quality flagged
- Weigh package for verification

**Packing Workflow**:
1. Scan order to start packing
2. System displays items and carton recommendation
3. Scan each item to confirm inclusion
4. Select carton and packing materials
5. Pack items with appropriate void fill
6. Weigh package (system verifies vs. expected)
7. Print shipping label
8. Apply label and complete packing

**Key Metrics**:
- Packs per hour per packer
- Packing accuracy (target: 99.9%)
- Carton utilization efficiency
- Weight variance (actual vs. expected)

**Domain Events**:
- `PackingStartedEvent`
- `ItemPackedEvent`
- `PackingCompletedEvent`

**Related Services**:
- Cartonization (carton recommendations)
- Shipment (label generation)

---

#### L3.5.2: Carton Selection & Materials Management
**Description**: Select appropriate cartons and packing materials based on cartonization recommendations.

**Technical Implementation**:
- Integration with cartonization service
- Packing materials inventory tracking
- Material usage recording
- Cost tracking per package

**Business Rules**:
- Follow cartonization recommendations
- Override requires manager approval
- Track material usage for cost allocation
- Alert on low packing materials inventory

**Packing Materials**:
- Cartons (various sizes)
- Void fill (air pillows, paper, peanuts)
- Tape
- Fragile labels
- Desiccant packs (if needed)

**Key Metrics**:
- Carton recommendation adherence rate
- Material cost per package
- Void fill usage rate
- Override rate (carton selection)

**Related Services**:
- Cartonization (recommendations)
- Inventory (packing materials)

---

#### L3.5.3: Package Weight Verification
**Description**: Verify package weight matches expected weight based on contents.

**Technical Implementation**:
- Integration with shipping scales
- Expected weight calculation from product catalog
- Tolerance-based verification
- Exception handling for weight variance

**Business Rules**:
- Weight variance tolerance: ±5% (configurable)
- Exceeding tolerance triggers re-verification
- Significant variance requires manager review
- Weight captured for shipping label accuracy

**Key Metrics**:
- Weight variance distribution
- Re-verification rate
- Weight accuracy impact on shipping costs

**Related Services**:
- Product Catalog (item weights)
- Shipment (package weight for rating)

---

## L2: Location Management

### L2.1: Description
Manage warehouse physical locations including bins, aisles, zones, and location hierarchies.

### L2.2: Business Value
- Optimize warehouse space utilization
- Support directed putaway and picking
- Enable location-based inventory tracking
- Support slotting optimization

### L2.3: L3 Capabilities

#### L3.6.1: Location Hierarchy Management
**Description**: Define and manage hierarchical warehouse location structure.

**Technical Implementation**:
- Hierarchical location model (warehouse → zone → aisle → bin)
- Location attributes (type, capacity, restrictions)
- Location status tracking (active, blocked, maintenance)

**Location Hierarchy**:
```
Warehouse
  ├─ Zone (e.g., "Fast Pick", "Reserve", "Oversize")
  │   ├─ Aisle (e.g., "A01", "A02")
  │   │   ├─ Bin (e.g., "A01-001-001")
```

**Business Rules**:
- Location codes must be unique within warehouse
- Locations have capacity constraints (cubic ft, weight)
- Locations can have item restrictions (size, type)
- Blocked locations unavailable for picking/putaway

**Key Metrics**:
- Location utilization by zone
- Active locations count
- Blocked/maintenance locations

**Related Services**: Inventory (location-based stock)

---

#### L3.6.2: Slotting Optimization
**Description**: Optimize product placement in warehouse locations based on velocity and characteristics.

**Technical Implementation**:
- Velocity-based slotting (fast movers in pick zones)
- ABC classification
- Slotting recommendation engine
- Automated reslotting workflows

**Slotting Strategies**:
- **Velocity Slotting**: High-volume items in accessible locations
- **Affinity Slotting**: Frequently ordered together → nearby locations
- **Size-Based Slotting**: Match item size to location capacity
- **Zone-Based Slotting**: Group by product category

**Business Rules**:
- A-items (80% of picks) in primary pick locations
- B-items in secondary locations
- C-items in reserve storage
- Seasonal adjustments to slotting
- Reslotting during off-peak hours

**Key Metrics**:
- Average pick location access time
- Pick density (picks per linear foot)
- Reslotting frequency
- Travel time reduction from slotting

**Related Services**: Analytics (velocity calculation)

---

## L2: Work Assignment & Management

### L2.1: Description
Assign and track work items across warehouse associates including picking, packing, quality control, and material handling.

### L2.2: Business Value
- Optimize labor utilization
- Balance workload across associates
- Track productivity and performance
- Support labor planning and scheduling

### L2.3: L3 Capabilities

#### L3.7.1: Work Queue Management
**Description**: Manage queues of work items awaiting assignment or execution.

**Technical Implementation**:
- Work queue by work type (pick, pack, QC, etc.)
- Priority-based queue ordering
- Queue depth monitoring
- SLA-based alerts

**Work Types**:
- **Picking**: Pick lists awaiting assignment
- **Packing**: Orders ready for packing
- **Quality Control**: Items/orders for inspection
- **Putaway**: Received goods for storage
- **Replenishment**: Transfer from reserve to pick
- **Cycle Count**: Inventory counting tasks

**Business Rules**:
- High-priority work at front of queue
- Work items age in queue (FIFO within priority)
- Queue depth triggers staffing alerts
- Work redistributed on associate unavailability

**Key Metrics**:
- Queue depth by work type
- Average time in queue
- Queue clearance rate
- Aging work items (>SLA)

**Related Services**: None (internal workflow)

---

#### L3.7.2: Labor Productivity Tracking
**Description**: Track individual and team productivity metrics for continuous improvement.

**Technical Implementation**:
- Real-time productivity dashboards
- Individual performance metrics
- Gamification and leaderboards
- Performance trend analysis

**Productivity Metrics**:
- **Picking**: Units per hour, lines per hour
- **Packing**: Packs per hour
- **Quality**: Inspections per hour, defect rate
- **Accuracy**: Error rate, quality score
- **Utilization**: Active time vs. total time

**Business Rules**:
- Metrics calculated in real-time
- Performance benchmarks by role
- Coaching triggers for below-target performance
- Recognition for top performers

**Key Metrics**:
- Average units per hour by role
- Top performer benchmarks
- Performance improvement trends
- Training impact on productivity

**Related Services**: HR systems (performance management)

---

## L2: License Plate Management

### L2.1: Description
Manage license plates (LPs) for tracking groups of items through receiving, storage, and fulfillment processes.

### L2.2: Business Value
- Unit load tracking throughout warehouse
- Support for pallet and case-level handling
- Improve receiving and putaway efficiency
- Enable cross-docking workflows

### L2.3: L3 Capabilities

#### L3.8.1: License Plate Creation & Assignment
**Description**: Create and assign license plates to received goods or outbound shipments.

**Technical Implementation**:
- LP barcode generation (unique identifiers)
- LP contents tracking (items, quantities)
- LP location tracking
- Nested LP support (pallet contains cases)

**Business Rules**:
- One LP per physical unit (pallet, case, carton)
- LP uniquely identifies contents
- LP tracks through all movements
- LP closed when contents verified

**LP Types**:
- **Receiving LP**: Inbound goods container
- **Storage LP**: Pallet or case in storage
- **Outbound LP**: Shipment container
- **Transfer LP**: Internal movement container

**Key Metrics**:
- Active LPs in warehouse
- LP cycle time (create to close)
- LP movement frequency

**Related Services**: Inventory (LP-based inventory tracking)

---

## L2: Mobile Application Support

### L2.1: Description
Provide mobile applications for warehouse associates to execute picking, packing, and other tasks.

### L2.2: Business Value
- Real-time task assignment and updates
- Barcode scanning for accuracy
- Guided workflows reduce training time
- Offline capability for connectivity issues

### L2.3: L3 Capabilities

#### L3.9.1: Mobile Picking Application
**Description**: Mobile app for pickers with directed workflows and barcode scanning.

**Technical Implementation**:
- Native mobile app (iOS/Android)
- RESTful API integration
- Barcode camera scanning
- Offline queue support
- Real-time sync

**Features**:
- Task list (assigned pick lists)
- Turn-by-turn navigation to locations
- Barcode scanning (item, location, quantity)
- Exception reporting (short pick, damage)
- Performance feedback (picks/hour)

**Key Metrics**:
- App uptime and reliability
- Scanning accuracy
- User satisfaction scores

**Related Services**: All warehouse operations (mobile interface)

---

## L2: Event-Driven Integration

### L2.1: Description
Publish and consume domain events to orchestrate fulfillment workflows and integrate with other services.

### L2.2: Business Value
- Loose coupling between services
- Real-time event-driven orchestration
- Asynchronous processing for scalability
- Complete audit trail via events

### L2.3: L3 Capabilities

#### L3.10.1: Warehouse Event Publishing
**Description**: Publish comprehensive domain events for all warehouse activities.

**Technical Implementation**:
- Kafka event bus
- CloudEvents format
- Event topic: `fulfillment.warehouse.v1.events`
- Transactional outbox pattern (recommended)

**Published Events**:
- `WaveReleasedEvent`
- `PickListGeneratedEvent`
- `PickListAssignedEvent`
- `ItemPickedEvent`
- `PickListCompletedEvent`
- `QualityInspectionCompletedEvent`
- `PackingCompletedEvent`

**Business Rules**:
- Events published after successful domain operation
- Include correlation ID for tracing
- Event schema versioning
- Idempotent event processing

**Related Services**: All services (event consumers)

---

#### L3.10.2: Order Event Consumption
**Description**: Consume order events to trigger warehouse fulfillment workflows.

**Technical Implementation**:
- Kafka consumer for order topic
- Event-driven wave planning
- Idempotent event processing
- Error handling and DLQ

**Consumed Events**:
- `FulfillmentOrderReleasedEvent` → Trigger wave planning
- `FulfillmentOrderCancelledEvent` → Cancel work
- `InventoryAllocatedEvent` → Confirm allocation

**Related Services**: Order Management

---

## L2: Monitoring & Observability

### L2.1: Description
Comprehensive monitoring, metrics, and observability for warehouse operations.

### L2.2: Business Value
- Real-time operational visibility
- Performance optimization
- Proactive issue detection
- Data-driven decision making

### L2.3: L3 Capabilities

#### L3.11.1: Operational Metrics Collection
**Description**: Collect and expose comprehensive metrics for warehouse operations.

**Technical Implementation**:
- Prometheus metrics integration
- Custom business metrics
- Grafana dashboards
- Real-time operational views

**Key Metrics Exposed**:
- `warehouse.waves.active` - Active waves
- `warehouse.picklists.pending` - Pick lists in queue
- `warehouse.picks.per.hour` - Picking rate
- `warehouse.packs.per.hour` - Packing rate
- `warehouse.accuracy.rate` - Accuracy percentage
- `warehouse.queue.depth{type}` - Work queue depths
- `warehouse.associates.active{role}` - Active associates

**Related Services**: Infrastructure (Prometheus, Grafana)

---

## Summary

The Warehouse Operations Service provides comprehensive warehouse fulfillment capabilities through:

### Key Strengths
- **Multi-Domain Architecture**: Separate bounded contexts for wave, pick, quality, etc.
- **Optimization**: Advanced wave planning and pick path optimization
- **Flexibility**: Support for multiple picking strategies
- **Quality**: Comprehensive quality control workflows
- **Productivity**: Mobile apps and labor tracking
- **Scalability**: Event-driven, horizontally scalable

### Business Impact
- **Throughput**: 10,000+ orders per day capacity
- **Accuracy**: >99.9% pick accuracy
- **Productivity**: 100-150 picks per hour per picker
- **Labor Utilization**: >85% associate utilization
- **Cycle Time**: 2-4 hours from wave release to pack complete

### Integration Points
- **Upstream**: Order Management (order release), Inventory (allocations)
- **Downstream**: Shipment (packed orders), Inventory (inventory transactions)
- **Events**: Publishes warehouse activity events, consumes order events

### Domain Model Highlights
- **Wave Aggregate**: Batch planning and execution
- **PickList Aggregate**: Pick execution management
- **QualityInspection Aggregate**: Quality control process
- **Multiple Sub-Domains**: Wave, PickList, Quality, Location, Work, LicensePlate, PutWall, Packaging, Workload

### Technology Highlights
- Hexagonal architecture with DDD
- Multi-domain bounded contexts
- Event-driven orchestration via Kafka
- Mobile application support
- Real-time operational dashboards
- Comprehensive observability
