# PakLog Event Flow Diagrams

## Complete Event-Driven Architecture

### Order Fulfillment Flow - End to End

```mermaid
sequenceDiagram
    participant EC as E-Commerce
    participant OM as Order Management
    participant I as Inventory
    participant C as Cartonization
    participant WO as Warehouse Ops
    participant WP as Wave Planning
    participant TE as Task Execution
    participant PE as Pick Execution
    participant PS as Pack & Ship
    participant ST as Shipment Transport

    EC->>OM: Order Request
    OM->>OM: Validate Order
    OM->>I: Check Availability
    I-->>OM: Stock Available
    OM->>I: Allocate Inventory

    OM->>+OM: Publish OrderCreated
    Note over OM: Domain Event

    OM->>C: Request Cartonization
    C->>C: Calculate 3D Packing
    C-->>OM: PackingSolution

    OM->>+OM: Publish OrderAllocated

    OM->>WO: Release Order
    WO->>+WO: Publish OrderReleasedToWarehouse

    WO->>WP: Add to Wave Queue
    WP->>WP: Optimize Wave
    WP->>+WP: Publish WavePlanned

    WP->>TE: Create Tasks
    TE->>+TE: Publish TaskCreated

    TE->>PE: Assign Pick Task
    PE->>PE: Calculate TSP Path
    PE->>+PE: Publish PickStarted

    PE->>PE: Execute Picks
    PE->>+PE: Publish PickCompleted

    PE->>PS: Transfer to Pack
    PS->>PS: Pack Items
    PS->>+PS: Publish PackageSealed

    PS->>ST: Create Shipment
    ST->>ST: Generate Label
    ST->>+ST: Publish ShipmentCreated

    ST-->>OM: Update Status
    OM->>+OM: Publish OrderShipped
```

### Returns Processing Flow

```mermaid
sequenceDiagram
    participant CUST as Customer
    participant RM as Returns Mgmt
    participant OM as Order Mgmt
    participant I as Inventory
    participant QC as Quality Compliance
    participant FS as Financial Settlement

    CUST->>RM: Request Return
    RM->>OM: Validate Order
    OM-->>RM: Order Details

    RM->>RM: Check Return Window
    RM->>RM: Fraud Detection
    RM->>+RM: Publish ReturnCreated

    alt Approved
        RM->>+RM: Publish ReturnApproved
        RM->>CUST: Send RMA Label

        CUST->>RM: Ship Return
        RM->>+RM: Publish ReturnReceived

        RM->>QC: Inspect Items
        QC->>QC: Quality Check
        QC->>+QC: Publish InspectionCompleted

        QC-->>RM: Inspection Result

        alt Good Condition
            RM->>I: Return to Stock
            I->>+I: Publish InventoryReceived
            RM->>FS: Process Refund
            FS->>+FS: Publish RefundProcessed
        else Damaged
            RM->>RM: Disposition Decision
            RM->>+RM: Publish DispositionDecided
        end
    else Denied
        RM->>+RM: Publish ReturnDenied
        RM->>CUST: Notify Denial
    end
```

### Robotics Fleet Coordination Flow

```mermaid
sequenceDiagram
    participant TE as Task Execution
    participant RF as Robotics Fleet
    participant WES as WES Orchestration
    participant PT as Physical Tracking
    participant LM as Location Master

    TE->>RF: Request Robot
    RF->>RF: Select Best Robot
    RF->>RF: Calculate A* Path
    RF->>+RF: Publish RobotAssigned

    RF->>RF: Check Collisions
    RF->>LM: Get Zone Capacity
    LM-->>RF: Zone Status

    RF->>+RF: Publish PathCalculated

    RF->>PT: Update Position
    PT->>+PT: Publish AssetMoved

    loop Mission Execution
        RF->>RF: Execute Step
        RF->>PT: Update Location
        PT->>+PT: Publish LocationUpdated

        alt Battery Low
            RF->>+RF: Publish BatteryLow
            RF->>RF: Queue Charging
        end
    end

    RF->>+RF: Publish MissionCompleted
    RF->>TE: Task Complete
```

### Predictive Analytics Integration Flow

```mermaid
sequenceDiagram
    participant PA as Predictive Analytics
    participant WP as Wave Planning
    participant WL as Workload Planning
    participant I as Inventory
    participant YM as Yard Management

    Note over PA: Scheduled Job
    PA->>PA: Collect Historical Data
    PA->>PA: Train ML Model
    PA->>PA: Generate Forecasts

    PA->>+PA: Publish DemandForecast
    WP-->>PA: Subscribe
    WL-->>PA: Subscribe

    PA->>+PA: Publish InventoryForecast
    I-->>PA: Subscribe

    PA->>+PA: Publish LaborForecast
    WL-->>PA: Subscribe

    PA->>+PA: Publish VolumeForeca
    YM-->>PA: Subscribe

    alt Anomaly Detected
        PA->>+PA: Publish AnomalyDetected
        Note over PA: Alert stakeholders
    end
```

### Cross-Docking Flow

```mermaid
sequenceDiagram
    participant YM as Yard Management
    participant CD as Cross-Docking
    participant WO as Warehouse Ops
    participant ST as Shipment Transport
    participant I as Inventory

    YM->>+YM: Publish TrailerArrived
    CD-->>YM: Subscribe

    CD->>CD: Check Cross-Dock Eligible

    alt Direct Transfer
        CD->>+CD: Publish CrossDockPlanned
        CD->>WO: Skip Put-Away
        CD->>ST: Direct to Outbound
        ST->>+ST: Publish DirectShipmentCreated
    else Consolidation Required
        CD->>CD: Plan Consolidation
        CD->>+CD: Publish ConsolidationPlanned
        CD->>WO: Stage Items

        loop Wait for All Items
            CD->>CD: Track Arrivals
        end

        CD->>+CD: Publish ConsolidationCompleted
        CD->>ST: Ship Consolidated
    end
```

### WES Orchestration Saga Flow

```mermaid
sequenceDiagram
    participant WES as WES Orchestration
    participant OM as Order Management
    participant I as Inventory
    participant WP as Wave Planning
    participant TE as Task Execution
    participant PS as Pack & Ship

    Note over WES: Complex Order Workflow
    WES->>WES: Start Saga
    WES->>+WES: Publish WorkflowStarted

    WES->>OM: Step 1: Validate Order
    OM-->>WES: Success
    WES->>+WES: Publish StepCompleted

    WES->>I: Step 2: Allocate Inventory
    I-->>WES: Success
    WES->>+WES: Publish StepCompleted

    WES->>WP: Step 3: Plan Wave
    WP-->>WES: Success
    WES->>+WES: Publish StepCompleted

    WES->>TE: Step 4: Execute Tasks

    alt Task Failed
        TE-->>WES: Failure
        WES->>+WES: Publish CompensationStarted

        Note over WES: Reverse Order
        WES->>WP: Compensate: Cancel Wave
        WES->>I: Compensate: Deallocate
        WES->>OM: Compensate: Cancel Order

        WES->>+WES: Publish WorkflowFailed
    else Success
        TE-->>WES: Success
        WES->>PS: Step 5: Ship
        PS-->>WES: Success

        WES->>+WES: Publish WorkflowCompleted
    end
```

## Event Catalog

### Core Domain Events

#### Order Management Events
- `OrderCreated` - New order received
- `OrderValidated` - Order validation complete
- `OrderAllocated` - Inventory allocated
- `OrderReleased` - Released to warehouse
- `OrderPicked` - Picking complete
- `OrderPacked` - Packing complete
- `OrderShipped` - Shipment dispatched
- `OrderDelivered` - Final delivery confirmed
- `OrderCancelled` - Order cancelled
- `OrderModified` - Order details changed

#### Inventory Events
- `InventoryReceived` - New inventory received
- `InventoryMoved` - Location transfer
- `InventoryAdjusted` - Manual adjustment
- `InventoryAllocated` - Reserved for order
- `InventoryDeallocated` - Reservation released
- `InventoryCounted` - Cycle count performed
- `LowStockAlert` - Below reorder point
- `StockoutAlert` - Zero inventory

#### Wave Planning Events
- `WavePlanned` - Wave created
- `WaveOptimized` - Wave re-optimized
- `WaveReleased` - Released for execution
- `WaveStarted` - Execution begun
- `WaveCompleted` - All tasks complete
- `WaveCancelled` - Wave cancelled

#### Task Execution Events
- `TaskCreated` - New task generated
- `TaskQueued` - Added to queue
- `TaskAssigned` - Assigned to worker/robot
- `TaskStarted` - Execution started
- `TaskCompleted` - Successfully completed
- `TaskFailed` - Execution failed
- `TaskReassigned` - Reassigned to different resource

#### Pick Execution Events
- `PickListCreated` - Pick list generated
- `PickStarted` - Picking begun
- `ItemPicked` - Single item picked
- `PickShortage` - Item not available
- `PickCompleted` - All items picked
- `PickException` - Exception during picking

#### Pack & Ship Events
- `PackingStarted` - Packing initiated
- `ItemPacked` - Item added to package
- `PackageSealed` - Package closed
- `LabelGenerated` - Shipping label created
- `PackageWeighed` - Weight captured
- `PackageShipped` - Handed to carrier

#### Robotics Fleet Events
- `RobotAssigned` - Robot assigned to task
- `PathCalculated` - A* path computed
- `MissionStarted` - Robot mission begun
- `CollisionAvoided` - Obstacle detected and avoided
- `BatteryLow` - Charging required
- `ChargingStarted` - Robot charging
- `ChargingCompleted` - Fully charged
- `MissionCompleted` - Task complete
- `RobotError` - Robot malfunction

#### Returns Management Events
- `ReturnRequested` - Customer initiated return
- `ReturnApproved` - RMA approved
- `ReturnDenied` - RMA rejected
- `ReturnReceived` - Physical receipt
- `ReturnInspected` - Quality check complete
- `RefundProcessed` - Money returned
- `ExchangeProcessed` - Replacement sent
- `DispositionDecided` - Final disposition determined

#### Quality Compliance Events
- `InspectionScheduled` - QC planned
- `InspectionStarted` - QC begun
- `DefectDetected` - Quality issue found
- `InspectionCompleted` - QC finished
- `ComplianceViolation` - Rule violation
- `CAPACreated` - Corrective action initiated
- `CAPAClosed` - Corrective action complete

#### Predictive Analytics Events
- `ForecastGenerated` - New prediction created
- `ModelTrained` - ML model updated
- `AnomalyDetected` - Unusual pattern found
- `AlertTriggered` - Threshold exceeded
- `RecommendationGenerated` - Optimization suggestion

## Event Publishing Patterns

### Event Structure (CloudEvents)
```json
{
  "specversion": "1.0",
  "type": "com.paklog.order.OrderCreated",
  "source": "order-management-service",
  "subject": "order/12345",
  "id": "event-uuid",
  "time": "2024-01-15T10:30:00Z",
  "datacontenttype": "application/json",
  "data": {
    "orderId": "12345",
    "customerId": "CUST-789",
    "orderLines": [...],
    "priority": "HIGH"
  }
}
```

### Event Topics

#### Kafka Topic Structure
- `paklog.order.events` - Order lifecycle events
- `paklog.inventory.events` - Inventory movements
- `paklog.warehouse.events` - Warehouse operations
- `paklog.task.events` - Task management
- `paklog.robotics.events` - Robot fleet events
- `paklog.analytics.events` - Predictions and insights
- `paklog.quality.events` - Quality and compliance
- `paklog.returns.events` - Returns processing

### Event Ordering Guarantees
- **Partition Key**: Used to ensure order within aggregate
- **Order Events**: Partitioned by orderId
- **Inventory Events**: Partitioned by SKU
- **Task Events**: Partitioned by workerId
- **Robot Events**: Partitioned by robotId

### Idempotency
- All events include unique `eventId`
- Consumers track processed events
- Duplicate detection window: 7 days

### Event Sourcing Services
- WES Orchestration Engine
- Order Management (audit trail)
- Inventory (movement history)
- Robotics Fleet (mission replay)

### Dead Letter Queue (DLQ) Handling
- Failed events retry 3 times with exponential backoff
- Permanent failures sent to DLQ
- Manual intervention required for DLQ processing
- Monitoring alerts on DLQ depth