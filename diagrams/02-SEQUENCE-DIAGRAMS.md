# PakLog Sequence Diagrams - Business Flows

## Table of Contents
1. [Order Fulfillment Flow](#order-fulfillment-flow)
2. [Wave Planning and Release](#wave-planning-and-release)
3. [Task Assignment Flow](#task-assignment-flow)
4. [Pick Execution Flow](#pick-execution-flow)
5. [Pack and Ship Flow](#pack-and-ship-flow)
6. [Inventory Movement Flow](#inventory-movement-flow)
7. [Location Slotting Optimization](#location-slotting-optimization)
8. [Error Handling and Compensation](#error-handling-and-compensation)

---

## Order Fulfillment Flow

Complete end-to-end order fulfillment process from order receipt to shipment.

```mermaid
sequenceDiagram
    title Complete Order Fulfillment Flow

    participant EC as E-Commerce
    participant GW as API Gateway
    participant WP as Wave Planning
    participant TE as Task Execution
    participant PE as Pick Execution
    participant PS as Pack & Ship
    participant PT as Physical Tracking
    participant TMS as Transport System
    participant K as Kafka

    EC->>+GW: POST /orders
    GW->>+WP: Create order
    WP->>WP: Validate order
    WP->>K: Publish OrderValidated
    WP-->>-GW: Order accepted
    GW-->>-EC: 201 Created

    Note over WP: Wave planning cycle
    WP->>WP: Optimize wave
    WP->>K: Publish WaveReleased

    K->>+TE: WaveReleased event
    TE->>TE: Generate pick tasks
    TE->>K: Publish TaskCreated
    TE-->>-K: Ack

    K->>+PE: TaskCreated event
    PE->>PE: Create pick session
    PE->>PE: Optimize pick path
    PE-->>-K: Ack

    Note over PE: Operator picks items
    PE->>PE: Update picks
    PE->>K: Publish PickingCompleted

    K->>+PS: PickingCompleted event
    PS->>PS: Create pack session
    PS->>PS: Pack items
    PS->>PS: Generate shipping label
    PS->>K: Publish PackingCompleted
    PS-->>-K: Ack

    K->>+PT: PackingCompleted event
    PT->>PT: Create license plate
    PT->>PT: Update inventory
    PT->>K: Publish ShipmentReady
    PT-->>-K: Ack

    PS->>+TMS: Book shipment
    TMS-->>-PS: Tracking number
    PS->>K: Publish OrderShipped

    K->>EC: OrderShipped notification
```

---

## Wave Planning and Release

Detailed wave planning, optimization, and release process.

```mermaid
sequenceDiagram
    title Wave Planning and Release Process

    participant UI as Web UI
    participant WP as Wave Planning
    participant LM as Location Master
    participant WL as Workload Planning
    participant INV as Inventory Service
    participant K as Kafka

    UI->>+WP: Create wave request
    WP->>WP: Validate parameters

    WP->>+INV: Check inventory availability
    INV-->>-WP: Inventory status

    WP->>+LM: Get picking locations
    LM->>LM: Query optimal locations
    LM-->>-WP: Location list

    WP->>+WL: Check capacity
    WL->>WL: Calculate workload
    WL-->>-WP: Capacity available

    WP->>WP: Run optimization algorithm
    Note over WP: Optimize by priority, SLA, zones

    WP->>WP: Create wave
    WP->>K: Publish WaveCreated
    WP-->>-UI: Wave details

    UI->>+WP: Release wave
    WP->>WP: Validate wave state
    WP->>WP: Generate pick lists
    WP->>K: Publish WaveReleased

    par Parallel processing
        K-->>INV: Allocate inventory
    and
        K-->>LM: Reserve locations
    and
        K-->>WL: Update workload
    end

    WP-->>-UI: Wave released
```

---

## Task Assignment Flow

Task creation, prioritization, and assignment to operators.

```mermaid
sequenceDiagram
    title Task Assignment and Execution Flow

    participant K as Kafka
    participant TE as Task Execution
    participant R as Redis Queue
    participant WL as Workload Planning
    participant OP as Mobile App
    participant PE as Pick Execution

    K->>+TE: WaveReleased event
    TE->>TE: Parse wave details

    loop For each order line
        TE->>TE: Create pick task
        TE->>TE: Calculate priority
        TE->>R: Add to priority queue
    end

    TE->>K: Publish TasksCreated
    TE-->>-K: Ack

    OP->>+TE: GET /tasks/next
    TE->>+WL: Get operator skills
    WL-->>-TE: Skill matrix

    TE->>R: Pop from queue
    R-->>TE: Next task

    TE->>TE: Match task to operator
    TE->>TE: Assign task
    TE->>K: Publish TaskAssigned
    TE-->>-OP: Task details

    OP->>+TE: POST /tasks/{id}/start
    TE->>TE: Update status
    TE->>K: Publish TaskStarted
    TE-->>-OP: 200 OK

    OP->>+PE: Execute pick
    PE->>PE: Process pick
    PE->>K: Publish PickCompleted
    PE-->>-OP: Pick confirmed

    OP->>+TE: POST /tasks/{id}/complete
    TE->>TE: Mark complete
    TE->>R: Update metrics
    TE->>K: Publish TaskCompleted
    TE-->>-OP: 200 OK
```

---

## Pick Execution Flow

Detailed picking process with path optimization and exception handling.

```mermaid
sequenceDiagram
    title Pick Execution with Path Optimization

    participant OP as Operator Device
    participant PE as Pick Execution
    participant LM as Location Master
    participant PT as Physical Tracking
    participant K as Kafka

    OP->>+PE: Start pick session
    PE->>PE: Create session
    PE->>+LM: Get pick locations
    LM-->>-PE: Location details

    PE->>PE: Run TSP algorithm
    Note over PE: Optimize pick path using 2-opt

    PE->>PE: Generate pick sequence
    PE-->>-OP: Optimized pick list

    loop For each pick
        OP->>+PE: Scan location
        PE->>PE: Validate location

        alt Location correct
            PE-->>OP: Show items to pick
            OP->>PE: Scan items
            PE->>PE: Validate items

            alt Items correct
                PE->>+PT: Update inventory
                PT->>PT: Deduct from location
                PT->>K: Publish InventoryMoved
                PT-->>-PE: Updated
                PE-->>-OP: Pick confirmed
            else Items incorrect
                PE->>PE: Log discrepancy
                PE->>K: Publish PickException
                PE-->>OP: Report issue
            end
        else Location incorrect
            PE-->>-OP: Wrong location
        end
    end

    OP->>+PE: Complete session
    PE->>PE: Validate all picks
    PE->>K: Publish PickSessionCompleted
    PE-->>-OP: Session summary
```

---

## Pack and Ship Flow

Packing, quality check, and shipping label generation process.

```mermaid
sequenceDiagram
    title Pack and Ship Process Flow

    participant OP as Operator
    participant PS as Pack & Ship
    participant QC as Quality Check
    participant TMS as Transport Management
    participant PT as Physical Tracking
    participant K as Kafka

    K->>+PS: PickingCompleted event
    PS->>PS: Create pack session
    PS-->>-K: Ack

    OP->>+PS: Start packing
    PS->>PS: Get order items
    PS-->>-OP: Items to pack

    OP->>+PS: Scan items
    PS->>PS: Validate items

    PS->>+QC: Quality check
    QC->>QC: Check criteria
    alt Quality passed
        QC-->>-PS: QC passed

        PS->>PS: Select carton
        PS->>PS: Calculate dimensions
        PS-->>OP: Suggested carton

        OP->>PS: Confirm carton
        PS->>PS: Generate packing list

        PS->>+TMS: Get shipping rates
        TMS-->>-PS: Rate options

        PS->>PS: Select service
        PS->>+TMS: Create shipment
        TMS-->>-PS: Label data

        PS->>PS: Generate label
        PS-->>OP: Print label

        PS->>+PT: Create license plate
        PT->>PT: Generate SSCC
        PT->>K: Publish LicensePlateCreated
        PT-->>-PS: LP number

        PS->>K: Publish PackingCompleted
        PS-->>-OP: Pack complete
    else Quality failed
        QC-->>PS: QC failed
        PS->>K: Publish QualityCheckFailed
        PS-->>OP: Rework required
    end
```

---

## Inventory Movement Flow

Inventory transfers between locations and cycle counting.

```mermaid
sequenceDiagram
    title Inventory Movement and Tracking

    participant OP as Operator
    participant PT as Physical Tracking
    participant LM as Location Master
    participant INV as Inventory Service
    participant K as Kafka

    OP->>+PT: Initiate transfer
    PT->>PT: Create movement record

    PT->>+LM: Validate source location
    LM-->>-PT: Location status

    PT->>+INV: Check availability
    INV-->>-PT: Available quantity

    alt Sufficient inventory
        PT->>PT: Reserve quantity
        PT-->>OP: Scan items

        OP->>PT: Confirm items
        PT->>PT: Validate scans

        PT->>+LM: Validate target location
        LM->>LM: Check capacity
        LM-->>-PT: Can receive

        PT->>PT: Execute transfer
        PT->>INV: Update balances

        par Update locations
            PT->>LM: Update source
        and
            PT->>LM: Update target
        end

        PT->>K: Publish InventoryMoved
        PT-->>-OP: Transfer complete

    else Insufficient inventory
        PT-->>-OP: Not enough stock
    end

    Note over PT,OP: Cycle Count Process

    OP->>+PT: Start cycle count
    PT->>+LM: Get location items
    LM-->>-PT: Expected items

    PT-->>-OP: Items to count

    OP->>+PT: Submit counts
    PT->>PT: Compare counts

    alt Count matches
        PT->>K: Publish CycleCountCompleted
        PT-->>-OP: Count confirmed
    else Discrepancy found
        PT->>PT: Calculate variance
        PT->>K: Publish InventoryAdjustment
        PT->>INV: Adjust inventory
        PT-->>OP: Recount required
    end
```

---

## Location Slotting Optimization

Dynamic slotting optimization based on velocity and seasonality.

```mermaid
sequenceDiagram
    title Location Slotting Optimization Process

    participant SCH as Scheduler
    participant LM as Location Master
    participant WL as Workload Planning
    participant AI as Analytics Engine
    participant PT as Physical Tracking
    participant K as Kafka

    SCH->>+LM: Trigger optimization

    LM->>+AI: Get velocity data
    AI->>AI: Analyze pick frequency
    AI->>AI: Calculate ABC classification
    AI-->>-LM: Item velocities

    LM->>+WL: Get seasonal patterns
    WL-->>-LM: Demand forecast

    LM->>LM: Run optimization algorithm
    Note over LM: Minimize travel distance
    Note over LM: Balance zone utilization

    LM->>LM: Generate move tasks

    loop For each relocation
        LM->>+PT: Create move task
        PT->>PT: Schedule move
        PT->>K: Publish RelocationRequired
        PT-->>-LM: Task created
    end

    LM->>K: Publish SlottingOptimized
    LM-->>-SCH: Optimization complete

    K->>WL: Update workload
    K->>PT: Execute relocations
```

---

## Error Handling and Compensation

Distributed saga pattern for handling failures and compensating transactions.

```mermaid
sequenceDiagram
    title Error Handling and Compensation Saga

    participant WP as Wave Planning
    participant TE as Task Execution
    participant PE as Pick Execution
    participant PS as Pack & Ship
    participant SC as Saga Coordinator
    participant K as Kafka

    WP->>+SC: Start fulfillment saga
    SC->>SC: Create saga instance

    SC->>WP: Execute wave release
    WP->>K: WaveReleased
    WP-->>SC: Success

    SC->>TE: Create tasks
    TE->>K: TasksCreated
    TE-->>SC: Success

    SC->>PE: Start picking
    PE->>PE: Process picks

    alt Pick shortage detected
        PE->>K: PickShortage
        PE-->>SC: Failure: shortage

        Note over SC: Initiate compensation

        SC->>PE: Compensate: cancel picks
        PE->>PE: Rollback picks
        PE->>K: PicksCancelled

        SC->>TE: Compensate: cancel tasks
        TE->>TE: Cancel remaining tasks
        TE->>K: TasksCancelled

        SC->>WP: Compensate: adjust wave
        WP->>WP: Remove shortage items
        WP->>K: WaveAdjusted

        SC->>SC: Restart from adjustment
        SC->>TE: Create adjusted tasks

    else Pick successful
        PE->>K: PickingCompleted
        PE-->>SC: Success

        SC->>PS: Start packing
        PS->>PS: Pack items

        alt Packing error
            PS-->>SC: Failure: damaged

            SC->>PS: Compensate: unpack
            PS->>K: PackingCancelled

            SC->>PE: Compensate: return items
            PE->>K: ItemsReturned

            SC->>SC: Mark saga failed
            SC->>K: FulfillmentFailed

        else Packing successful
            PS->>K: PackingCompleted
            PS-->>SC: Success
            SC->>SC: Mark saga complete
            SC->>K: FulfillmentCompleted
        end
    end

    SC-->>-WP: Saga result
```

---

## Real-time Task Monitoring

WebSocket-based real-time monitoring of task execution.

```mermaid
sequenceDiagram
    title Real-time Task Monitoring via WebSocket

    participant UI as Dashboard UI
    participant GW as API Gateway
    participant TE as Task Execution
    participant K as Kafka
    participant WS as WebSocket Handler

    UI->>+GW: WS /monitor/tasks
    GW->>+WS: Establish connection
    WS-->>-GW: Connection established
    GW-->>-UI: WebSocket connected

    UI->>GW: Subscribe: warehouse=WH001
    GW->>WS: Register subscription

    par Real-time events
        K->>TE: TaskCreated
        TE->>WS: Notify subscribers
        WS->>GW: Push update
        GW->>UI: Task created event
    and
        K->>TE: TaskAssigned
        TE->>WS: Notify subscribers
        WS->>GW: Push update
        GW->>UI: Task assigned event
    and
        K->>TE: TaskCompleted
        TE->>WS: Notify subscribers
        WS->>GW: Push update
        GW->>UI: Task completed event
    end

    UI->>GW: Request metrics
    GW->>TE: GET /metrics/realtime
    TE-->>GW: Current metrics
    GW-->>UI: Metrics update

    Note over UI: Connection lost
    UI->>GW: WS reconnect
    GW->>WS: Re-establish
    WS->>WS: Restore subscriptions
    WS-->>GW: Reconnected
    GW-->>UI: Connection restored
```

---

## Integration with External Systems

External system integration patterns.

```mermaid
sequenceDiagram
    title External System Integration Patterns

    participant ERP as ERP System
    participant ESB as Integration Service
    participant WP as Wave Planning
    participant INV as Inventory Service
    participant K as Kafka
    participant DB as Database

    Note over ERP,ESB: Order synchronization
    ERP->>+ESB: New order (SOAP/XML)
    ESB->>ESB: Transform to domain model
    ESB->>+WP: POST /orders
    WP->>DB: Store order
    WP->>K: OrderReceived
    WP-->>-ESB: 201 Created
    ESB-->>-ERP: ACK

    Note over ERP,ESB: Inventory sync
    K->>ESB: InventoryAdjusted event
    ESB->>ESB: Transform to ERP format
    ESB->>+ERP: Update inventory (SOAP)
    ERP-->>-ESB: Confirmed

    Note over ERP,ESB: Master data sync
    ERP->>+ESB: Item master update
    ESB->>ESB: Validate and transform
    ESB->>+INV: PUT /items/{id}
    INV->>DB: Update item
    INV->>K: ItemUpdated
    INV-->>-ESB: 200 OK
    ESB-->>-ERP: Sync complete

    Note over ERP,ESB: Error handling
    ERP->>+ESB: Invalid data
    ESB->>ESB: Validation fails
    ESB->>K: IntegrationError
    ESB->>DB: Log error
    ESB-->>-ERP: Error response
```