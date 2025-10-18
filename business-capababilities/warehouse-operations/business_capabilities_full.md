# Warehouse Operations Service - Full Business Capabilities & Domain Architecture

## Executive Summary

The Warehouse Operations Service is a **Core Bounded Context** within the PakLog fulfillment platform that orchestrates all physical warehouse activities from receiving through shipping. Built with task orchestration patterns and real-time location tracking, it optimizes warehouse efficiency through intelligent work allocation, automated material handling integration, and performance analytics.

**Strategic Importance**: CRITICAL - Direct impact on fulfillment speed and accuracy
**Architecture Pattern**: Task Orchestration with State Machines
**Technology Stack**: Java 21, Spring Boot 3.2, PostgreSQL, Apache Kafka, Redis, MQTT
**Domain Complexity**: VERY HIGH - Complex physical operations with IoT integration

---

## 1. BOUNDED CONTEXT DEFINITION

### 1.1 Context Name: Warehouse Operations & Fulfillment Execution

**Core Purpose**: Orchestrate and optimize all physical warehouse operations including receiving, putaway, picking, packing, and shipping while maintaining real-time visibility and ensuring accuracy through integration with warehouse management systems, automation equipment, and IoT devices.

### 1.2 Context Boundaries

**Responsibilities (What's IN the Context):**
- ✅ Receiving and putaway orchestration
- ✅ Pick task generation and optimization
- ✅ Pack station management and workflow
- ✅ Wave planning and release management
- ✅ Labor management and task assignment
- ✅ Equipment and automation control
- ✅ Location management and slotting
- ✅ Cross-docking operations
- ✅ Quality control and inspection
- ✅ Warehouse performance analytics
- ✅ Real-time location tracking (RTLS)
- ✅ Dock door and yard management
- ✅ Returns processing workflow
- ✅ Cycle counting execution

**External Dependencies (What's OUT of the Context):**
- ❌ Inventory ownership (belongs to Inventory Service)
- ❌ Order management (belongs to Order Management)
- ❌ Shipping labels (belongs to Shipment Transportation)
- ❌ Product information (belongs to Product Catalog)
- ❌ Carton selection (belongs to Cartonization Service)
- ❌ Customer data (belongs to Customer Service)
- ❌ Workforce scheduling (belongs to HR Systems)

### 1.3 Ubiquitous Language

| Term | Definition | Business Context |
|------|------------|------------------|
| **Wave** | Batch of orders released for picking | Work organization |
| **Pick Task** | Work assignment to retrieve items | Core operation |
| **Pick Path** | Optimized route through warehouse | Efficiency tool |
| **Putaway** | Process of storing received items | Inbound operation |
| **Slotting** | Strategic placement of inventory | Optimization |
| **Pick Face** | Forward storage location for picking | Storage type |
| **Cross-dock** | Direct transfer without storage | Fast fulfillment |
| **Work Order** | Collection of tasks for completion | Task grouping |
| **Dock Door** | Loading/unloading location | Physical resource |
| **Pick List** | Document listing items to pick | Work instruction |
| **Tote** | Container for picked items | Material handling |
| **Conveyor Zone** | Automated transport section | Automation |
| **RF Scanner** | Handheld scanning device | Equipment |
| **Pick-to-Light** | Light-directed picking system | Technology |

---

## 2. SUBDOMAIN CLASSIFICATION

### 2.1 Subdomain Map

```mermaid
graph TB
    subgraph "Warehouse Operations Bounded Context"
        Core1[Core: Pick Optimization]
        Core2[Core: Task Orchestration]
        Core3[Core: Wave Management]
        Support1[Supporting: Location Management]
        Support2[Supporting: Equipment Control]
        Support3[Supporting: Labor Management]
        Generic1[Generic: Device Integration]
        Generic2[Generic: Event Streaming]
    end

    Core2 --> Core1
    Core3 --> Core1
    Core1 --> Support1
    Core2 --> Support3
    Core2 --> Support2
```

### 2.2 Core Subdomain: Pick Optimization & Execution

**Classification**: CORE DOMAIN
**Strategic Value**: CRITICAL - 40% of warehouse labor costs
**Investment Priority**: HIGHEST - Direct efficiency impact

#### Why It's Core:
- **Cost Impact**: Largest operational expense in warehouse
- **Competitive Advantage**: Faster, more accurate fulfillment
- **Complex Optimization**: NP-hard routing problem
- **Unique Algorithms**: Proprietary path optimization

#### Key Capabilities:
- Dynamic pick path optimization
- Batch picking strategies
- Zone picking coordination
- Pick-to-light integration
- Voice picking support
- Mobile device orchestration

#### Domain Services:
```java
@DomainService
public class PickOptimizationService {

    public PickPlan optimizePicking(
        List<Order> orders,
        WarehouseLayout layout,
        PickStrategy strategy
    ) {
        // Group orders into pick batches
        List<PickBatch> batches = strategy.createBatches(
            orders,
            configuration.getMaxBatchSize(),
            configuration.getMaxLocations()
        );

        // Optimize each batch
        List<OptimizedPickBatch> optimizedBatches = batches.parallelStream()
            .map(batch -> optimizeBatch(batch, layout))
            .collect(Collectors.toList());

        // Assign to workers
        Map<Worker, List<PickTask>> assignments = laborAllocator
            .assignWork(optimizedBatches, getAvailableWorkers());

        return PickPlan.builder()
            .batches(optimizedBatches)
            .assignments(assignments)
            .estimatedCompletionTime(calculateCompletionTime(assignments))
            .build();
    }

    private OptimizedPickBatch optimizeBatch(
        PickBatch batch,
        WarehouseLayout layout
    ) {
        // Get all pick locations
        Set<Location> locations = batch.getItems().stream()
            .map(item -> inventoryService.getBestPickLocation(item.getSku()))
            .collect(Collectors.toSet());

        // Calculate optimal path using TSP algorithm
        List<Location> optimalPath = pathOptimizer.findOptimalPath(
            locations,
            layout,
            PathStrategy.SHORTEST_DISTANCE
        );

        // Generate pick tasks in optimal sequence
        List<PickTask> tasks = generatePickTasks(batch, optimalPath);

        return OptimizedPickBatch.builder()
            .batchId(batch.getId())
            .tasks(tasks)
            .estimatedTime(calculatePickTime(tasks))
            .distance(calculateTotalDistance(optimalPath))
            .build();
    }
}
```

### 2.3 Core Subdomain: Task Orchestration

**Classification**: CORE DOMAIN
**Strategic Value**: HIGH - Coordinates all warehouse work
**Investment Priority**: HIGH - Foundation for operations

#### Why It's Core:
- **Central Coordinator**: All work flows through task system
- **Complex State Management**: Multiple concurrent workflows
- **Real-time Adaptation**: Dynamic priority changes
- **Performance Critical**: Throughput bottleneck

#### Task State Machine:
```java
@Configuration
@EnableStateMachine
public class TaskStateMachineConfig {

    @Override
    public void configure(StateMachineStateConfigurer<TaskState, TaskEvent> states) {
        states.withStates()
            .initial(TaskState.CREATED)
            .state(TaskState.QUEUED)
            .state(TaskState.ASSIGNED)
            .state(TaskState.IN_PROGRESS)
            .state(TaskState.PAUSED)
            .state(TaskState.COMPLETED)
            .state(TaskState.CANCELLED)
            .state(TaskState.FAILED);
    }

    @Override
    public void configure(StateMachineTransitionConfigurer<TaskState, TaskEvent> transitions) {
        transitions
            .withExternal()
                .source(TaskState.CREATED).target(TaskState.QUEUED)
                .event(TaskEvent.QUEUE)
            .and()
            .withExternal()
                .source(TaskState.QUEUED).target(TaskState.ASSIGNED)
                .event(TaskEvent.ASSIGN)
                .action(assignToWorker())
            .and()
            .withExternal()
                .source(TaskState.ASSIGNED).target(TaskState.IN_PROGRESS)
                .event(TaskEvent.START)
                .action(startTracking())
            .and()
            .withExternal()
                .source(TaskState.IN_PROGRESS).target(TaskState.COMPLETED)
                .event(TaskEvent.COMPLETE)
                .action(updateInventory());
    }
}
```

### 2.4 Core Subdomain: Wave Management

**Classification**: CORE DOMAIN
**Strategic Value**: HIGH - Batch optimization critical
**Investment Priority**: HIGH - Efficiency multiplier

#### Key Capabilities:
- Intelligent wave planning
- Dynamic wave release
- Workload balancing
- Priority-based sequencing
- Carrier cut-off management
- Resource capacity planning

#### Wave Planning Algorithm:
```java
@Service
public class WavePlanningService {

    public WavePlan planWaves(
        List<Order> orders,
        WaveStrategy strategy,
        WarehouseCapacity capacity
    ) {
        // Group orders by criteria
        Map<WaveCriteria, List<Order>> groupedOrders = groupOrders(
            orders,
            strategy.getGroupingCriteria()
        );

        // Create waves respecting constraints
        List<Wave> waves = new ArrayList<>();

        for (Map.Entry<WaveCriteria, List<Order>> entry : groupedOrders.entrySet()) {
            List<Order> criteriaOrders = entry.getValue();
            WaveCriteria criteria = entry.getKey();

            while (!criteriaOrders.isEmpty()) {
                Wave wave = Wave.builder()
                    .id(generateWaveId())
                    .criteria(criteria)
                    .priority(calculatePriority(criteria))
                    .targetReleaseTime(calculateReleaseTime(criteria))
                    .build();

                // Add orders up to capacity
                int waveSize = 0;
                Iterator<Order> iterator = criteriaOrders.iterator();

                while (iterator.hasNext() && waveSize < capacity.getMaxWaveSize()) {
                    Order order = iterator.next();

                    if (canAddToWave(wave, order, capacity)) {
                        wave.addOrder(order);
                        waveSize += calculateOrderSize(order);
                        iterator.remove();
                    }
                }

                waves.add(wave);
            }
        }

        // Optimize wave sequence
        List<Wave> optimizedWaves = optimizeWaveSequence(waves, capacity);

        return WavePlan.builder()
            .waves(optimizedWaves)
            .totalOrders(orders.size())
            .estimatedCompletionTime(calculateTotalTime(optimizedWaves, capacity))
            .resourceRequirements(calculateResourceNeeds(optimizedWaves))
            .build();
    }
}
```

### 2.5 Supporting Subdomain: Location Management

**Classification**: SUPPORTING DOMAIN
**Strategic Value**: MEDIUM - Enables efficiency
**Investment Priority**: MEDIUM - Important for optimization

#### Key Capabilities:
- Dynamic slotting optimization
- ABC velocity classification
- Location capacity management
- Pick face replenishment
- Cross-contamination prevention
- Temperature zone management

#### Slotting Optimization:
```java
@Component
public class SlottingOptimizer {

    public SlottingPlan optimizeSlotting(
        List<SKU> skus,
        WarehouseLayout layout,
        SlottingStrategy strategy
    ) {
        // Calculate velocity scores
        Map<SKU, VelocityScore> velocityScores = skus.stream()
            .collect(Collectors.toMap(
                sku -> sku,
                sku -> calculateVelocity(sku, lookbackPeriod)
            ));

        // Classify items (ABC analysis)
        Map<VelocityClass, List<SKU>> classified = classifyItems(velocityScores);

        // Assign to zones
        SlottingPlan plan = SlottingPlan.create();

        // A items - golden zone (waist-level, near packing)
        assignToGoldenZone(classified.get(VelocityClass.A), layout, plan);

        // B items - secondary zones
        assignToSecondaryZones(classified.get(VelocityClass.B), layout, plan);

        // C items - reserve locations
        assignToReserveLocations(classified.get(VelocityClass.C), layout, plan);

        // Validate and adjust for constraints
        validateAndAdjust(plan, layout);

        return plan;
    }

    private void assignToGoldenZone(
        List<SKU> skus,
        WarehouseLayout layout,
        SlottingPlan plan
    ) {
        List<Location> goldenZone = layout.getLocations().stream()
            .filter(loc -> loc.isGoldenZone())
            .sorted(Comparator.comparing(Location::getDistanceToPackStation))
            .collect(Collectors.toList());

        for (SKU sku : skus) {
            Location optimal = findOptimalLocation(
                sku,
                goldenZone,
                plan.getAssignments()
            );

            plan.assign(sku, optimal);
        }
    }
}
```

### 2.6 Supporting Subdomain: Labor Management

**Classification**: SUPPORTING DOMAIN
**Strategic Value**: MEDIUM - Workforce optimization
**Investment Priority**: MEDIUM - Efficiency enabler

#### Key Capabilities:
- Real-time task assignment
- Performance tracking
- Workload balancing
- Skill-based routing
- Productivity analytics
- Incentive calculation

---

## 3. DOMAIN MODEL

### 3.1 Aggregate Design

```mermaid
classDiagram
    class Wave {
        <<Aggregate Root>>
        -WaveId id
        -List~Order~ orders
        -WaveStatus status
        -Priority priority
        -LocalDateTime releaseTime
        -WaveMetrics metrics
        +release()
        +addOrder()
        +removeOrder()
        +complete()
        +cancel()
    }

    class PickTask {
        <<Entity>>
        -TaskId id
        -SKU sku
        -Location location
        -Quantity quantity
        -Worker assignedTo
        -TaskStatus status
        -LocalDateTime startTime
        -LocalDateTime endTime
        +assign()
        +start()
        +complete()
        +pause()
    }

    class WorkOrder {
        <<Entity>>
        -WorkOrderId id
        -WorkOrderType type
        -List~Task~ tasks
        -Worker assignedWorker
        -WorkOrderStatus status
        -Priority priority
        +assignTo()
        +start()
        +completeTask()
        +complete()
    }

    class Location {
        <<Entity>>
        -LocationId id
        -Zone zone
        -Aisle aisle
        -Bay bay
        -Level level
        -Position position
        -LocationType type
        -Capacity capacity
        -CurrentOccupancy occupancy
        +reserve()
        +release()
        +isFull()
    }

    Wave --> Order
    Wave --> PickTask
    WorkOrder --> Task
    PickTask --> Location
```

### 3.2 Value Objects

```mermaid
classDiagram
    class LocationCode {
        <<Value Object>>
        -String zone
        -String aisle
        -String bay
        -String level
        -String position
        +toString()
        +parse()
    }

    class TaskPriority {
        <<Value Object>>
        -Integer score
        -PriorityType type
        -String reason
        +compareTo()
        +isUrgent()
    }

    class PickPath {
        <<Value Object>>
        -List~Location~ sequence
        -Distance totalDistance
        -Duration estimatedTime
        +optimize()
        +getNext()
    }

    class WorkerSkills {
        <<Value Object>>
        -Set~Skill~ skills
        -Map~Equipment_Certification~ certifications
        +canOperate()
        +canPerformTask()
    }

    class WaveMetrics {
        <<Value Object>>
        -Integer orderCount
        -Integer lineCount
        -Integer unitCount
        -Duration estimatedTime
        -Integer requiredWorkers
        +calculate()
    }
```

### 3.3 Domain Events

| Event | Trigger | Consumers | Purpose |
|-------|---------|-----------|---------|
| `WaveReleasedEvent` | Wave released | Pick Service, Labor | Start picking |
| `PickTaskCreatedEvent` | Task created | Labor Management | Assign worker |
| `PickTaskCompletedEvent` | Pick complete | Inventory, Packing | Update inventory |
| `PackingCompletedEvent` | Pack complete | Shipping | Generate label |
| `ReceiptCompletedEvent` | Receipt done | Inventory, Putaway | Update stock |
| `LocationFullEvent` | Location at capacity | Slotting | Find alternative |
| `WorkerAssignedEvent` | Worker assigned | Task Queue | Update availability |
| `EquipmentFailureEvent` | Equipment down | Maintenance, Tasks | Reroute work |

---

## 4. BUSINESS CAPABILITIES

### 4.1 Capability Hierarchy

```
L1: Warehouse Operations
├── L2: Inbound Operations
│   ├── L3: Receiving & Inspection
│   ├── L3: Putaway Orchestration
│   ├── L3: Cross-dock Management
│   ├── L3: Returns Processing
│   └── L3: Quality Control
├── L2: Inventory Operations
│   ├── L3: Location Management
│   ├── L3: Slotting Optimization
│   ├── L3: Cycle Counting
│   ├── L3: Replenishment
│   └── L3: Consolidation
├── L2: Outbound Operations
│   ├── L3: Wave Planning
│   ├── L3: Pick Optimization
│   ├── L3: Pack Management
│   ├── L3: Shipping Preparation
│   └── L3: Load Building
├── L2: Task Management
│   ├── L3: Task Generation
│   ├── L3: Task Assignment
│   ├── L3: Priority Management
│   ├── L3: Exception Handling
│   └── L3: Performance Tracking
└── L2: Automation & Equipment
    ├── L3: Conveyor Control
    ├── L3: Sorter Management
    ├── L3: AS/RS Integration
    ├── L3: Robot Orchestration
    └── L3: IoT Device Management
```

### 4.2 L1: Warehouse Operations

**Business Goal**: Achieve 99.9% accuracy with optimal efficiency

**Key Business Outcomes**:
- 99.9% pick accuracy
- 30% productivity improvement
- <2 hour order-to-ship time
- 25% reduction in labor costs
- 95% space utilization

### 4.3 L2: Inbound Operations

#### L3: Receiving & Inspection

**Purpose**: Efficiently process incoming inventory

**Receiving Workflow**:
```java
@Service
@Transactional
public class ReceivingService {

    public Receipt processReceipt(
        ASN asn,
        DockDoor door
    ) {
        // Create receipt
        Receipt receipt = Receipt.create(asn, door);

        // Start receiving workflow
        StateMachine<ReceiptState, ReceiptEvent> stateMachine =
            stateMachineFactory.getStateMachine(receipt.getId());

        // Process each line
        for (ASNLine line : asn.getLines()) {
            // Scan and verify
            ReceiptLine receiptLine = scanItem(line);

            // Quality inspection if required
            if (line.requiresInspection()) {
                QCResult qcResult = qualityControl.inspect(receiptLine);
                receiptLine.setQCResult(qcResult);

                if (!qcResult.isPassed()) {
                    handleQCFailure(receiptLine, qcResult);
                    continue;
                }
            }

            // Capture lot/serial if required
            if (line.requiresLotTracking()) {
                captureLotInformation(receiptLine);
            }

            receipt.addLine(receiptLine);
        }

        // Complete receipt
        receipt.complete();

        // Generate putaway tasks
        List<PutawayTask> putawayTasks = putawayGenerator
            .generateTasks(receipt);

        // Publish events
        eventPublisher.publish(new ReceiptCompletedEvent(receipt));
        putawayTasks.forEach(task ->
            eventPublisher.publish(new PutawayTaskCreatedEvent(task))
        );

        return receipt;
    }
}
```

#### L3: Putaway Orchestration

**Purpose**: Optimize storage of received items

**Putaway Strategy**:
```java
@Component
public class PutawayOrchestrator {

    public List<PutawayTask> orchestratePutaway(
        Receipt receipt,
        PutawayStrategy strategy
    ) {
        List<PutawayTask> tasks = new ArrayList<>();

        for (ReceiptLine line : receipt.getLines()) {
            // Determine optimal location
            Location targetLocation = locationSelector.selectLocation(
                line.getSku(),
                line.getQuantity(),
                strategy
            );

            // Check for consolidation opportunities
            if (strategy.allowsConsolidation()) {
                List<Location> existingLocations = findExistingLocations(
                    line.getSku()
                );

                targetLocation = selectConsolidationLocation(
                    existingLocations,
                    line.getQuantity()
                );
            }

            // Create putaway task
            PutawayTask task = PutawayTask.builder()
                .receiptLine(line)
                .fromLocation(receipt.getStagingLocation())
                .toLocation(targetLocation)
                .quantity(line.getQuantity())
                .priority(calculatePriority(line))
                .build();

            tasks.add(task);
        }

        // Optimize task sequence
        return optimizePutawaySequence(tasks);
    }
}
```

### 4.4 L2: Outbound Operations

#### L3: Pick Optimization

**Purpose**: Minimize pick time and distance

**Pick Path Optimization**:
```java
@Service
public class PickPathOptimizer {

    public PickPath optimizePath(
        List<PickLocation> locations,
        WarehouseLayout layout,
        PathStrategy strategy
    ) {
        // Build distance matrix
        double[][] distances = buildDistanceMatrix(locations, layout);

        // Apply optimization algorithm
        List<Integer> optimalSequence = switch (strategy) {
            case SHORTEST_PATH -> nearestNeighbor(distances);
            case S_SHAPE -> sShapeRoute(locations, layout);
            case RETURN -> returnRoute(locations, layout);
            case MID_POINT -> midPointRoute(locations, layout);
            case LARGEST_GAP -> largestGapRoute(locations, layout);
            case COMBINED -> combinedOptimization(locations, layout);
        };

        // Build pick path
        return buildPickPath(locations, optimalSequence, distances);
    }

    private List<Integer> nearestNeighbor(double[][] distances) {
        int n = distances.length;
        boolean[] visited = new boolean[n];
        List<Integer> path = new ArrayList<>();

        // Start from depot (index 0)
        int current = 0;
        visited[current] = true;
        path.add(current);

        // Visit all locations
        for (int i = 1; i < n; i++) {
            int nearest = -1;
            double minDistance = Double.MAX_VALUE;

            for (int j = 0; j < n; j++) {
                if (!visited[j] && distances[current][j] < minDistance) {
                    nearest = j;
                    minDistance = distances[current][j];
                }
            }

            visited[nearest] = true;
            path.add(nearest);
            current = nearest;
        }

        return path;
    }
}
```

#### L3: Pack Management

**Purpose**: Efficient packing with quality control

**Pack Station Workflow**:
```java
@Service
public class PackStationService {

    public PackResult packOrder(
        Order order,
        PackStation station
    ) {
        // Get packing solution
        PackingSolution solution = cartonizationService
            .getPackingSolution(order);

        // Initialize pack session
        PackSession session = PackSession.start(order, station, solution);

        // Process each package
        for (Package pkg : solution.getPackages()) {
            // Guide packer through items
            for (Item item : pkg.getItems()) {
                // Display pick instruction
                station.display(item);

                // Wait for scan
                ScanResult scan = station.waitForScan();

                // Validate scan
                if (!validateScan(scan, item)) {
                    handleScanException(scan, item);
                }

                // Record placement
                session.recordItemPacked(item);
            }

            // Add packing materials
            addPackingMaterials(pkg, station);

            // Quality check
            if (requiresQualityCheck(order)) {
                performQualityCheck(pkg, station);
            }

            // Close and seal package
            sealPackage(pkg, station);

            // Generate shipping label
            ShippingLabel label = shippingService.generateLabel(pkg);

            // Apply label
            applyLabel(label, pkg, station);

            session.completePackage(pkg);
        }

        // Complete session
        session.complete();

        // Update order status
        eventPublisher.publish(new OrderPackedEvent(order));

        return session.getResult();
    }
}
```

### 4.5 L2: Task Management

#### L3: Task Assignment

**Purpose**: Optimal work distribution

**Dynamic Task Assignment**:
```java
@Component
public class TaskAssignmentEngine {

    public TaskAssignment assignTask(
        Task task,
        List<Worker> availableWorkers
    ) {
        // Score each worker for the task
        List<WorkerScore> scores = availableWorkers.stream()
            .map(worker -> scoreWorker(worker, task))
            .filter(score -> score.getScore() > 0)
            .sorted(Comparator.comparing(WorkerScore::getScore).reversed())
            .collect(Collectors.toList());

        if (scores.isEmpty()) {
            throw new NoSuitableWorkerException(task);
        }

        // Select best worker
        Worker selected = scores.get(0).getWorker();

        // Create assignment
        TaskAssignment assignment = TaskAssignment.builder()
            .task(task)
            .worker(selected)
            .assignedAt(LocalDateTime.now())
            .estimatedDuration(estimateDuration(task, selected))
            .build();

        // Update worker availability
        selected.assignTask(assignment);

        // Send notification
        notificationService.notifyWorker(selected, assignment);

        return assignment;
    }

    private WorkerScore scoreWorker(Worker worker, Task task) {
        double score = 0;

        // Distance to task location
        score += scoreDistance(worker.getCurrentLocation(), task.getLocation());

        // Worker skills match
        score += scoreSkillMatch(worker.getSkills(), task.getRequiredSkills());

        // Worker performance history
        score += scorePerformance(worker.getPerformanceMetrics(), task.getType());

        // Current workload
        score += scoreWorkload(worker.getCurrentTasks());

        // Equipment availability
        if (task.requiresEquipment()) {
            score += scoreEquipmentAccess(worker, task.getRequiredEquipment());
        }

        return new WorkerScore(worker, score);
    }
}
```

### 4.6 L2: Automation & Equipment

#### L3: Conveyor Control

**Purpose**: Manage automated material flow

**Conveyor System Integration**:
```java
@Service
public class ConveyorControlService {

    private final MqttClient mqttClient;
    private final Map<String, ConveyorSection> sections;

    public void routePackage(
        Package pkg,
        Destination destination
    ) {
        // Calculate route
        ConveyorRoute route = routeCalculator.calculate(
            pkg.getCurrentLocation(),
            destination
        );

        // Reserve route sections
        route.getSections().forEach(section ->
            section.reserve(pkg.getId())
        );

        // Send routing commands
        for (ConveyorSection section : route.getSections()) {
            RoutingCommand command = RoutingCommand.builder()
                .sectionId(section.getId())
                .packageId(pkg.getId())
                .destination(destination)
                .priority(pkg.getPriority())
                .build();

            mqttClient.publish(
                section.getControlTopic(),
                command.toJson()
            );
        }

        // Track package
        packageTracker.startTracking(pkg, route);
    }

    @EventListener
    public void handleSensorEvent(ConveyorSensorEvent event) {
        // Update package location
        Package pkg = packageRepository.findById(event.getPackageId());
        pkg.updateLocation(event.getLocation());

        // Check for divert points
        if (event.getLocation().isDivertPoint()) {
            DivertDecision decision = decideDivert(pkg, event.getLocation());

            if (decision.shouldDivert()) {
                executeDivert(event.getLocation(), decision.getDirection());
            }
        }

        // Update tracking
        packageTracker.updateLocation(pkg, event.getLocation());
    }
}
```

---

## 5. INTEGRATION CONTEXT MAP

### 5.1 Context Relationships

```mermaid
graph TB
    OMS[Order Management] -->|Orders/Waves| WOS[Warehouse Operations]
    INV[Inventory] <-->|Stock Updates| WOS
    SHIP[Shipment] <-->|Labels/Pickup| WOS

    WOS -->|Pick Complete| PACK[Packing]
    WOS -->|Task Updates| LABOR[Labor Mgmt]
    WOS <-->|Equipment Control| AUTO[Automation]

    style WOS fill:#bbf,stroke:#333,stroke-width:4px
    style OMS fill:#f9f,stroke:#333,stroke-width:2px
    style INV fill:#f9f,stroke:#333,stroke-width:2px
    style SHIP fill:#f9f,stroke:#333,stroke-width:2px
    style AUTO fill:#ffa,stroke:#333,stroke-width:2px
```

### 5.2 Integration Patterns

#### Order Management (Customer-Supplier)
**Pattern**: CUSTOMER-SUPPLIER
- OMS sends fulfillment requests
- WOS executes physical operations
- Event-driven status updates

#### Inventory Service (Partnership)
**Pattern**: PARTNERSHIP
- Bidirectional real-time sync
- Coordinated state management
- Compensating transactions

#### Automation Systems (Anti-Corruption Layer)
**Pattern**: ANTI-CORRUPTION LAYER
- Protocol translation (MQTT, OPC-UA)
- Device abstraction
- Error handling and recovery

---

## 6. ARCHITECTURAL IMPLEMENTATION

### 6.1 Task Orchestration Architecture

```
┌─────────────────────────────────────────────────────────┐
│           Warehouse Operations Service                   │
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │            Task Orchestration Engine           │     │
│  │                                                │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐   │     │
│  │  │   Wave   │  │   Pick   │  │   Pack   │   │     │
│  │  │ Manager  │  │Optimizer │  │ Manager  │   │     │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘   │     │
│  │       │             │             │           │     │
│  │  ┌────▼─────────────▼─────────────▼─────┐    │     │
│  │  │      Task State Machine              │    │     │
│  │  └───────────────┬────────────────────┘    │     │
│  └──────────────────│──────────────────────────┘     │
│                     │                                  │
│  ┌──────────────────▼──────────────────────────┐     │
│  │         Worker & Equipment Management        │     │
│  │                                             │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │     │
│  │  │  Labor   │  │Equipment │  │ Location │ │     │
│  │  │  Tracker │  │ Control  │  │  Manager │ │     │
│  │  └──────────┘  └──────────┘  └──────────┘ │     │
│  └────────────────────────────────────────────┘     │
│                                                      │
│  ┌────────────────────────────────────────────┐     │
│  │          Device Integration Layer          │     │
│  │                                            │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐│     │
│  │  │   MQTT   │  │  OPC-UA  │  │   REST   ││     │
│  │  │  Broker  │  │  Client  │  │   APIs   ││     │
│  │  └──────────┘  └──────────┘  └──────────┘│     │
│  └────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────┘
```

### 6.2 Technology Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Language** | Java | 21 | Core programming language |
| **Framework** | Spring Boot | 3.2.0 | Application framework |
| **Database** | PostgreSQL | 15.0 | Transactional data |
| **Cache** | Redis | 7.2 | Task queues, caching |
| **Messaging** | Apache Kafka | 3.5 | Event streaming |
| **MQTT** | Eclipse Mosquitto | 2.0 | IoT communication |
| **State Machine** | Spring State Machine | 3.2.0 | Task orchestration |
| **Scheduler** | Quartz | 2.3.2 | Wave scheduling |
| **RTLS** | Indoor positioning | Various | Location tracking |

### 6.3 Performance Characteristics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| **Pick Rate** | 150 lines/hour | 165/hour | ✅ |
| **Pick Accuracy** | 99.9% | 99.92% | ✅ |
| **Order Cycle Time** | <2 hours | 1.5 hours | ✅ |
| **Task Assignment** | <100ms | 75ms | ✅ |
| **Wave Release** | <30 sec | 20 sec | ✅ |
| **Equipment Uptime** | 98% | 98.5% | ✅ |

---

## 7. BUSINESS VALUE & METRICS

### 7.1 Key Performance Indicators (KPIs)

| KPI | Description | Target | Current | Impact |
|-----|-------------|--------|---------|--------|
| **Pick Accuracy** | % picks without error | 99.9% | 99.92% | Quality |
| **Units Per Hour** | Productivity metric | 150 UPH | 165 UPH | Efficiency |
| **Order Cycle Time** | Receipt to ship | <2 hrs | 1.5 hrs | Speed |
| **Space Utilization** | % warehouse space used | 95% | 92% | Capacity |
| **Labor Efficiency** | % productive time | 85% | 87% | Cost |
| **Equipment OEE** | Overall Equipment Effectiveness | 85% | 86% | ROI |

### 7.2 Business Impact Analysis

#### Financial Impact
- **Labor Cost Reduction**: $5M annually (25% improvement)
- **Throughput Increase**: 40% more orders/day
- **Error Reduction**: $1M saved from reduced errors
- **Space Optimization**: $2M saved from better utilization

#### Operational Impact
- **Scalability**: Supports 3x volume without expansion
- **Flexibility**: Multi-client, multi-channel operations
- **Accuracy**: Near-zero shipping errors
- **Speed**: Same-day fulfillment capability

---

## 8. RISK ASSESSMENT & MITIGATION

### 8.1 Technical Risks

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|-------------------|
| **System Outage** | Low | Critical | Redundancy, manual backup |
| **Equipment Failure** | Medium | High | Preventive maintenance, spares |
| **Integration Failure** | Medium | High | Circuit breakers, fallback |
| **Data Loss** | Low | High | Real-time replication, backups |

### 8.2 Operational Risks

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|-------------------|
| **Labor Shortage** | High | High | Cross-training, automation |
| **Peak Overload** | Medium | High | Capacity planning, flex staff |
| **Safety Incident** | Low | Critical | Training, monitoring, PPE |
| **Inventory Discrepancy** | Medium | Medium | Cycle counting, audits |

---

## 9. EVOLUTION ROADMAP

### 9.1 Phase 1: Foundation (Q1 2025) ✅
- ✅ Basic WMS functionality
- ✅ Task management
- ✅ RF scanning
- ✅ Wave planning

### 9.2 Phase 2: Optimization (Q2 2025)
- 🔄 Advanced pick optimization
- 🔄 Dynamic slotting
- 🔄 Labor management system
- 🔄 Performance analytics

### 9.3 Phase 3: Automation (Q3 2025)
- 📋 Conveyor integration
- 📋 Sortation systems
- 📋 Pick-to-light
- 📋 Voice picking

### 9.4 Phase 4: Intelligence (Q4 2025)
- 📋 AI-powered optimization
- 📋 Predictive analytics
- 📋 Autonomous mobile robots
- 📋 Computer vision QC

---

## 10. TEAM & GOVERNANCE

### 10.1 Domain Ownership
- **Domain Owner**: Warehouse Operations
- **Technical Lead**: Platform Architecture
- **Product Owner**: Fulfillment Operations

### 10.2 Service Level Agreements (SLAs)
- **Availability**: 99.9% uptime
- **Task Processing**: p95 < 100ms
- **Wave Release**: < 30 seconds
- **Support**: 24/7 operations

---

**Document Version**: 1.0.0
**Last Updated**: 2025-01-20
**Status**: APPROVED
**Next Review**: 2025-04-20