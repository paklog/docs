# PakLog Extended Sequence Diagrams - WMS/WES Integration

## Table of Contents
1. [WMS to WES Handoff](#wms-to-wes-handoff)
2. [Cross-Service Event Choreography](#cross-service-event-choreography)
3. [Location State Synchronization](#location-state-synchronization)
4. [WES Orchestration Workflow](#wes-orchestration-workflow)
5. [Workload Planning Integration](#workload-planning-integration)

---

## WMS to WES Handoff

Shows the clear separation between WMS strategic planning and WES execution.

```mermaid
sequenceDiagram
    title WMS to WES Service Handoff

    participant UI as Planning UI
    participant WMS_WP as WMS: Wave Planning
    participant WMS_WL as WMS: Workload Planning
    participant WMS_LM as WMS: Location Master
    participant K as Event Bus (Kafka)
    participant WES_TE as WES: Task Execution
    participant WES_PE as WES: Pick Execution
    participant WES_WO as WES: Orchestration

    Note over UI,WMS_WP: Strategic Planning (WMS)

    UI->>+WMS_WP: Create wave strategy
    WMS_WP->>+WMS_WL: Check capacity
    WMS_WL->>WMS_WL: Analyze workload
    WMS_WL-->>-WMS_WP: Capacity confirmed

    WMS_WP->>+WMS_LM: Get slotting strategy
    WMS_LM-->>-WMS_WP: Optimal locations

    WMS_WP->>WMS_WP: Plan wave
    WMS_WP->>K: Publish WavePlanned
    WMS_WP-->>-UI: Wave ready

    Note over K,WES_WO: Execution Handoff

    K->>+WES_WO: WavePlanned event
    WES_WO->>WES_WO: Create workflow
    WES_WO->>K: Publish WorkflowStarted
    WES_WO-->>-K: Ack

    Note over WES_TE,WES_PE: Real-time Execution (WES)

    K->>+WES_TE: WorkflowStarted event
    WES_TE->>WES_TE: Generate tasks
    WES_TE->>K: Publish TasksCreated
    WES_TE-->>-K: Ack

    K->>+WES_PE: TasksCreated event
    WES_PE->>WES_PE: Optimize paths
    WES_PE->>WES_PE: Assign to operators
    WES_PE->>K: Publish ExecutionStarted
    WES_PE-->>-K: Ack

    Note over WMS_WP,WES_PE: Clear WMS/WES boundary
```

---

## Cross-Service Event Choreography

Event-driven choreography between multiple services without central orchestration.

```mermaid
sequenceDiagram
    title Event Choreography Pattern

    participant WMS_OM as WMS: Order Mgmt
    participant WMS_INV as WMS: Inventory
    participant WMS_WP as WMS: Wave Planning
    participant K as Kafka
    participant WES_TE as WES: Task Execution
    participant WES_PE as WES: Pick Execution
    participant WES_PS as WES: Pack & Ship
    participant WES_PT as WES: Physical Tracking

    WMS_OM->>K: OrderValidated

    par Parallel event processing
        K-->>WMS_INV: OrderValidated
        WMS_INV->>WMS_INV: Reserve inventory
        WMS_INV->>K: InventoryReserved
    and
        K-->>WMS_WP: OrderValidated
        WMS_WP->>WMS_WP: Add to wave
        WMS_WP->>K: OrderWaved
    end

    Note over K: Both events received

    K-->>WMS_WP: InventoryReserved
    WMS_WP->>WMS_WP: Confirm wave ready
    WMS_WP->>K: WaveReleased

    par WES services react independently
        K-->>WES_TE: WaveReleased
        WES_TE->>K: TasksGenerated
    and
        K-->>WES_PT: WaveReleased
        WES_PT->>K: LocationsReserved
    end

    K-->>WES_PE: TasksGenerated & LocationsReserved
    WES_PE->>WES_PE: Start execution
    WES_PE->>K: PickingStarted

    Note over K,WES_PS: Event cascade continues

    WES_PE->>K: PickingCompleted
    K-->>WES_PS: PickingCompleted
    WES_PS->>K: PackingStarted

    WES_PS->>K: PackingCompleted
    K-->>WES_PT: PackingCompleted
    WES_PT->>K: ShipmentReady

    K-->>WMS_OM: ShipmentReady
    WMS_OM->>WMS_OM: Update order status
```

---

## Location State Synchronization

Bi-directional synchronization between Location Master (WMS) and Physical Tracking (WES).

```mermaid
sequenceDiagram
    title Location Master and Physical Tracking Sync

    participant WMS_LM as WMS: Location Master
    participant K as Kafka
    participant WES_PT as WES: Physical Tracking
    participant WES_PE as WES: Pick Execution
    participant RTLS as RTLS System

    Note over WMS_LM: Configuration Change

    WMS_LM->>WMS_LM: Update location capacity
    WMS_LM->>K: LocationConfigChanged

    K->>+WES_PT: LocationConfigChanged
    WES_PT->>WES_PT: Update constraints
    WES_PT-->>-K: Ack

    Note over WES_PT: Physical State Change

    RTLS->>+WES_PT: Movement detected
    WES_PT->>WES_PT: Update location state
    WES_PT->>K: LocationStateChanged
    WES_PT-->>-RTLS: Processed

    K->>+WMS_LM: LocationStateChanged
    WMS_LM->>WMS_LM: Update occupancy
    WMS_LM-->>-K: Ack

    Note over WES_PE: Execution Impact

    WES_PE->>+WES_PT: Query location
    WES_PT->>WES_PT: Check real-time state

    alt Location available
        WES_PT-->>-WES_PE: Location details
        WES_PE->>WES_PE: Execute pick
        WES_PE->>K: PickExecuted

        K->>WES_PT: PickExecuted
        WES_PT->>WES_PT: Update state
        WES_PT->>K: LocationUpdated

        K->>WMS_LM: LocationUpdated
        WMS_LM->>WMS_LM: Sync state
    else Location blocked
        WES_PT-->>WES_PE: Location blocked
        WES_PE->>K: LocationException

        K->>WMS_LM: LocationException
        WMS_LM->>WMS_LM: Trigger re-slotting
        WMS_LM->>K: ReslottingRequired
    end
```

---

## WES Orchestration Workflow

Complex workflow orchestration managed by WES Orchestration Engine.

```mermaid
sequenceDiagram
    title WES Orchestration Engine Workflow

    participant K as Kafka
    participant WO as WES Orchestration
    participant TE as Task Execution
    participant PE as Pick Execution
    participant PS as Pack & Ship
    participant QC as Quality Check
    participant PT as Physical Tracking

    K->>+WO: WaveReleased
    WO->>WO: Load workflow definition
    WO->>WO: Create workflow instance
    WO->>K: WorkflowStarted

    Note over WO: Step 1: Task Creation
    WO->>+TE: CreateTasks command
    TE->>TE: Generate tasks
    TE->>K: TasksCreated
    TE-->>-WO: Step completed

    Note over WO: Step 2: Picking (with retry)
    WO->>+PE: ExecutePicks command
    PE->>PE: Start picking

    alt Picking fails
        PE-->>WO: Error: Item not found
        WO->>WO: Log attempt 1
        WO->>PE: Retry with alternative
        PE->>PE: Try backup location
        PE->>K: PickCompleted
        PE-->>-WO: Step completed
    else Picking succeeds
        PE->>K: PickCompleted
        PE-->>WO: Step completed
    end

    Note over WO: Step 3: Quality Check (conditional)
    WO->>WO: Check if QC required

    opt Quality check needed
        WO->>+QC: InspectItems command
        QC->>QC: Perform inspection
        QC->>K: QualityPassed
        QC-->>-WO: Step completed
    end

    Note over WO: Step 4: Packing
    WO->>+PS: PackOrder command
    PS->>PS: Pack items
    PS->>K: PackingCompleted
    PS-->>-WO: Step completed

    Note over WO: Step 5: Update tracking
    WO->>+PT: UpdateLocation command
    PT->>PT: Update physical state
    PT->>K: LocationUpdated
    PT-->>-WO: Step completed

    WO->>WO: Mark workflow complete
    WO->>K: WorkflowCompleted
    WO-->>-K: Ack
```

---

## Workload Planning Integration

Integration between Workload Planning and real-time execution metrics.

```mermaid
sequenceDiagram
    title Workload Planning and Execution Feedback Loop

    participant WMS_WL as WMS: Workload Planning
    participant WMS_WP as WMS: Wave Planning
    participant K as Kafka
    participant WES_TE as WES: Task Execution
    participant WES_metrics as WES: Metrics Service
    participant AI as ML/Analytics

    Note over WMS_WL: Planning Phase

    WMS_WL->>+AI: Get demand forecast
    AI-->>-WMS_WL: Predicted volume

    WMS_WL->>WMS_WL: Calculate capacity
    WMS_WL->>WMS_WL: Plan labor allocation
    WMS_WL->>K: WorkloadPlanned

    K->>WMS_WP: WorkloadPlanned
    WMS_WP->>WMS_WP: Create waves per capacity
    WMS_WP->>K: WaveCreated

    Note over WES_TE: Execution Phase

    K->>WES_TE: WaveCreated
    WES_TE->>WES_TE: Execute tasks

    loop Every 5 minutes
        WES_TE->>WES_metrics: Report progress
        WES_metrics->>WES_metrics: Calculate KPIs
        WES_metrics->>K: MetricsUpdate
    end

    Note over WMS_WL: Feedback Loop

    K->>WMS_WL: MetricsUpdate
    WMS_WL->>WMS_WL: Compare plan vs actual

    alt Performance below target
        WMS_WL->>WMS_WL: Adjust allocation
        WMS_WL->>K: CapacityAdjusted

        K->>WES_TE: CapacityAdjusted
        WES_TE->>WES_TE: Rebalance workload
        WES_TE->>K: WorkloadRebalanced
    else Performance on track
        WMS_WL->>WMS_WL: Log metrics
    end

    Note over AI: Learning Phase

    WMS_WL->>AI: Send actual vs planned
    AI->>AI: Update ML model
    AI->>AI: Improve predictions
    AI->>K: ModelUpdated
```

---

## Notes on Sequence Diagrams

### Key Design Patterns Illustrated

1. **Event-Driven Architecture**: All services communicate primarily through Kafka events
2. **Saga Pattern**: Complex workflows use compensation for failure handling
3. **CQRS**: Commands flow through orchestration, queries can be direct
4. **Circuit Breaker**: Services handle failures gracefully with retries
5. **Event Sourcing**: All state changes are captured as events

### Service Boundaries

- **WMS Services**: Strategic planning, configuration, optimization
- **WES Services**: Real-time execution, physical operations, task management
- **Shared Services**: Cross-cutting concerns like quality, authentication

### Communication Patterns

- **Synchronous**: REST/gRPC for queries and immediate responses
- **Asynchronous**: Kafka for events and long-running operations
- **WebSocket**: Real-time updates for UI dashboards
- **Batch**: Scheduled jobs for optimization and analytics