# PakLog State Machine Diagrams

## Table of Contents
1. [Wave Lifecycle State Machine](#wave-lifecycle-state-machine)
2. [Task State Machine](#task-state-machine)
3. [Pick Session State Machine](#pick-session-state-machine)
4. [Order State Machine](#order-state-machine)
5. [Location State Machine](#location-state-machine)
6. [License Plate State Machine](#license-plate-state-machine)
7. [Inventory Item State Machine](#inventory-item-state-machine)
8. [Pack Session State Machine](#pack-session-state-machine)
9. [Shipment State Machine](#shipment-state-machine)
10. [Operator State Machine](#operator-state-machine)

---

## Wave Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> Draft: Create Wave

    Draft --> Planned: Plan Wave
    Draft --> Cancelled: Cancel

    Planned --> Optimizing: Optimize
    Planned --> Released: Release Wave
    Planned --> Cancelled: Cancel

    Optimizing --> Planned: Optimization Complete
    Optimizing --> Failed: Optimization Failed

    Released --> InProgress: Tasks Started
    Released --> Cancelled: Cancel Release

    InProgress --> Completing: All Tasks Done
    InProgress --> Paused: Pause Wave
    InProgress --> Cancelled: Cancel Wave

    Paused --> InProgress: Resume Wave
    Paused --> Cancelled: Cancel Wave

    Completing --> Completed: Validation Passed
    Completing --> InProgress: Validation Failed

    Completed --> [*]: Archive
    Cancelled --> [*]: Archive
    Failed --> Draft: Retry

    note right of Draft
        Initial state when wave is created
        Can add/remove orders
    end note

    note right of Released
        Wave released to floor
        Tasks are being generated
    end note

    note right of InProgress
        Active picking happening
        Monitor progress
    end note

    note right of Completed
        All orders fulfilled
        Ready for reporting
    end note
```

---

## Task State Machine

```mermaid
stateDiagram-v2
    [*] --> Created: Generate Task

    Created --> Queued: Add to Queue
    Created --> Cancelled: Cancel Task

    Queued --> Assigning: Get Next Task
    Queued --> Cancelled: Cancel Task

    Assigning --> Assigned: Assign to Operator
    Assigning --> Queued: Assignment Failed

    Assigned --> Accepted: Operator Accepts
    Assigned --> Rejected: Operator Rejects
    Assigned --> Expired: Timeout

    Rejected --> Queued: Return to Queue
    Expired --> Queued: Return to Queue

    Accepted --> InProgress: Start Task
    Accepted --> Cancelled: Cancel Task

    InProgress --> Paused: Pause Task
    InProgress --> Completing: Submit Task
    InProgress --> Abandoned: Abandon Task

    Paused --> InProgress: Resume Task
    Paused --> Abandoned: Timeout

    Abandoned --> Queued: Return to Queue

    Completing --> Completed: Validation Passed
    Completing --> InProgress: Validation Failed

    Completed --> [*]: Close Task
    Cancelled --> [*]: Close Task

    note right of Queued
        Task in priority queue
        Waiting for assignment
    end note

    note right of InProgress
        Operator actively working
        Track time and progress
    end note

    note right of Completed
        Task successfully completed
        Update metrics
    end note
```

---

## Pick Session State Machine

```mermaid
stateDiagram-v2
    [*] --> Initialized: Create Session

    Initialized --> Ready: Load Pick List
    Initialized --> Cancelled: Cancel

    Ready --> Started: Start Picking
    Ready --> Cancelled: Cancel

    Started --> Picking: First Pick
    Started --> Cancelled: Cancel

    Picking --> PickCompleted: Complete Pick
    Picking --> Exception: Report Exception
    Picking --> Paused: Pause Session

    PickCompleted --> Picking: Next Pick
    PickCompleted --> Reviewing: Last Pick

    Exception --> ExceptionHandling: Handle Exception

    ExceptionHandling --> Resolved: Resolve
    ExceptionHandling --> Escalated: Escalate

    Resolved --> Picking: Continue
    Escalated --> Suspended: Await Resolution

    Suspended --> Picking: Resume
    Suspended --> Cancelled: Cancel

    Paused --> Picking: Resume
    Paused --> Cancelled: Cancel

    Reviewing --> Completed: Confirm All
    Reviewing --> Picking: Corrections Needed

    Completed --> [*]: Close Session
    Cancelled --> [*]: Close Session

    note right of Picking
        Active picking state
        Scan location and items
    end note

    note right of Exception
        Handle shortages, damages
        Wrong items, etc.
    end note

    note right of Reviewing
        Final validation
        Check completeness
    end note
```

---

## Order State Machine

```mermaid
stateDiagram-v2
    [*] --> Received: Order Placed

    Received --> Validating: Validate Order

    Validating --> Validated: Validation Passed
    Validating --> Invalid: Validation Failed

    Invalid --> Received: Fix & Retry
    Invalid --> Cancelled: Cancel Order

    Validated --> AllocatingInventory: Check Inventory

    AllocatingInventory --> Allocated: Inventory Available
    AllocatingInventory --> BackOrdered: Partial/No Stock

    BackOrdered --> AllocatingInventory: Stock Received
    BackOrdered --> Cancelled: Cancel Order

    Allocated --> WaveAssigned: Add to Wave

    WaveAssigned --> Released: Wave Released
    WaveAssigned --> Cancelled: Cancel Order

    Released --> Picking: Start Picking

    Picking --> Picked: Picking Complete
    Picking --> PartialPicked: Partial Pick

    PartialPicked --> Picking: Continue Picking
    PartialPicked --> Cancelled: Cancel Remaining

    Picked --> Packing: Start Packing

    Packing --> Packed: Packing Complete
    Packing --> QCFailed: Quality Check Failed

    QCFailed --> Packing: Repack
    QCFailed --> Cancelled: Cancel Order

    Packed --> ReadyToShip: Label Generated

    ReadyToShip --> Shipped: Carrier Pickup

    Shipped --> Delivered: In Transit
    Delivered --> [*]: Order Complete

    Cancelled --> [*]: Order Cancelled

    note right of Allocated
        Inventory reserved
        Ready for fulfillment
    end note

    note right of Picking
        Order being picked
        Track progress
    end note

    note right of Shipped
        With carrier
        Track shipment
    end note
```

---

## Location State Machine

```mermaid
stateDiagram-v2
    [*] --> Created: Create Location

    Created --> Configuring: Configure Settings

    Configuring --> Active: Configuration Complete

    Active --> Reserved: Reserve Location
    Active --> Blocked: Block Location
    Active --> Full: Mark Full
    Active --> Maintenance: Schedule Maintenance
    Active --> Decommissioning: Start Decommission

    Reserved --> Active: Release Reservation
    Reserved --> Blocked: Block Location

    Blocked --> Active: Unblock
    Blocked --> Maintenance: Start Maintenance
    Blocked --> Decommissioning: Decommission

    Full --> Active: Space Available
    Full --> Blocked: Block Location

    Maintenance --> Active: Maintenance Complete
    Maintenance --> Blocked: Issue Found
    Maintenance --> Decommissioning: Beyond Repair

    Decommissioning --> Decommissioned: Complete Decommission

    Decommissioned --> [*]: Archive

    note right of Active
        Location available for use
        Normal operations
    end note

    note right of Reserved
        Reserved for specific purpose
        Cycle count, special project
    end note

    note right of Blocked
        Temporarily unavailable
        Damage, safety issue
    end note

    note right of Decommissioned
        Permanently removed
        Cannot be reactivated
    end note
```

---

## License Plate State Machine

```mermaid
stateDiagram-v2
    [*] --> Created: Generate LP

    Created --> Open: Initialize

    Open --> Receiving: Add Items
    Open --> Moving: Start Movement

    Receiving --> Open: Items Added
    Receiving --> PartiallyFilled: Some Items

    PartiallyFilled --> Receiving: Add More
    PartiallyFilled --> Moving: Move LP
    PartiallyFilled --> Consolidating: Combine LPs

    Moving --> InTransit: Movement Started

    InTransit --> Arrived: At Destination
    InTransit --> Lost: Cannot Locate

    Arrived --> Open: Put Away
    Arrived --> Staged: Stage for Shipping

    Staged --> Loading: Load on Truck
    Staged --> Open: Return to Storage

    Loading --> Shipped: On Truck

    Consolidating --> Open: Consolidation Complete

    Open --> Closing: Close LP

    Closing --> Closed: Validation Passed
    Closing --> Open: Validation Failed

    Closed --> Archived: Archive LP
    Shipped --> Archived: Shipment Complete
    Lost --> Investigating: Investigate

    Investigating --> Found: LP Found
    Investigating --> WrittenOff: Not Found

    Found --> Open: Return to Use
    WrittenOff --> Archived: Close Case

    Archived --> [*]: End

    note right of Open
        LP available for operations
        Can add/remove items
    end note

    note right of InTransit
        Being moved between locations
        Track movement
    end note

    note right of Closed
        No more changes allowed
        Ready for shipping
    end note
```

---

## Inventory Item State Machine

```mermaid
stateDiagram-v2
    [*] --> Pending: Item Created

    Pending --> Receiving: Start Receipt

    Receiving --> QCRequired: Needs Inspection
    Receiving --> Available: Direct Put Away

    QCRequired --> InQC: Quality Check

    InQC --> QCPassed: Pass
    InQC --> QCFailed: Fail

    QCPassed --> Available: Release
    QCFailed --> Quarantined: Quarantine

    Available --> Allocated: Allocate for Order
    Available --> Reserved: Reserve
    Available --> CycleCount: Count Required
    Available --> Moving: Move Item

    Allocated --> Picking: Start Pick
    Allocated --> Available: Deallocate

    Picking --> Picked: Pick Complete
    Picking --> Available: Pick Cancelled

    Reserved --> Available: Release
    Reserved --> Allocated: Allocate

    CycleCount --> Counting: Count in Progress

    Counting --> Verified: Count Matches
    Counting --> Discrepancy: Count Mismatch

    Verified --> Available: Return to Stock
    Discrepancy --> Adjusting: Adjust Quantity

    Adjusting --> Available: Adjustment Complete
    Adjusting --> Investigating: Major Discrepancy

    Investigating --> Available: Resolved
    Investigating --> WrittenOff: Write Off

    Moving --> InTransit: Movement Started

    InTransit --> Available: Movement Complete
    InTransit --> Lost: Cannot Locate

    Quarantined --> Investigating: Investigate Issue
    Quarantined --> Disposed: Dispose

    Picked --> Packed: In Packing
    Packed --> Shipped: On Shipment

    Lost --> Investigating: Search

    WrittenOff --> [*]: End
    Disposed --> [*]: End
    Shipped --> [*]: End

    note right of Available
        In stock and available
        Ready for allocation
    end note

    note right of Allocated
        Reserved for order
        Not available for others
    end note

    note right of Quarantined
        On hold for issues
        Requires resolution
    end note
```

---

## Pack Session State Machine

```mermaid
stateDiagram-v2
    [*] --> Created: Create Session

    Created --> Initialized: Load Order Items

    Initialized --> Ready: Items Staged
    Initialized --> Cancelled: Cancel

    Ready --> Started: Begin Packing
    Ready --> Cancelled: Cancel

    Started --> Scanning: Scan First Item

    Scanning --> ItemVerified: Item Matches
    Scanning --> ItemMismatch: Wrong Item

    ItemVerified --> Packing: Add to Carton
    ItemMismatch --> ExceptionHandling: Handle Exception

    Packing --> Scanning: Next Item
    Packing --> CartonFull: Carton at Capacity
    Packing --> AllPacked: Last Item

    CartonFull --> CartonSelection: Select New Carton

    CartonSelection --> Packing: Continue Packing

    ExceptionHandling --> Resolved: Issue Resolved
    ExceptionHandling --> Escalated: Escalate Issue

    Resolved --> Scanning: Continue
    Escalated --> Suspended: Await Resolution

    Suspended --> Scanning: Resume
    Suspended --> Cancelled: Cancel

    AllPacked --> QualityCheck: Perform QC

    QualityCheck --> QCPassed: Quality OK
    QualityCheck --> QCFailed: Issues Found

    QCFailed --> Repacking: Fix Issues

    Repacking --> QualityCheck: Re-check

    QCPassed --> Sealing: Seal Carton

    Sealing --> LabelPrinting: Print Label

    LabelPrinting --> LabelApplied: Apply Label

    LabelApplied --> Completed: Session Complete

    Completed --> [*]: Close Session
    Cancelled --> [*]: Close Session

    note right of Packing
        Actively packing items
        Track carton fill rate
    end note

    note right of QualityCheck
        Verify pack accuracy
        Check for damage
    end note

    note right of Completed
        Ready for shipping
        Update inventory
    end note
```

---

## Shipment State Machine

```mermaid
stateDiagram-v2
    [*] --> Draft: Create Shipment

    Draft --> Booking: Add Orders

    Booking --> Booked: Carrier Booked
    Booking --> Failed: Booking Failed

    Failed --> Booking: Retry
    Failed --> Cancelled: Cancel

    Booked --> Staging: Stage at Dock

    Staging --> Ready: All Orders Staged
    Staging --> Partial: Partial Staged

    Partial --> Staging: Continue Staging
    Partial --> Modified: Modify Shipment

    Modified --> Staging: Resume Staging

    Ready --> Loading: Start Loading

    Loading --> Loaded: Loading Complete
    Loading --> LoadException: Loading Issue

    LoadException --> Loading: Resolve & Continue
    LoadException --> Modified: Modify Shipment

    Loaded --> Documentation: Generate Docs

    Documentation --> Documented: Docs Complete

    Documented --> Dispatched: Carrier Pickup

    Dispatched --> InTransit: On Route

    InTransit --> Delivered: At Destination
    InTransit --> Exception: Delivery Exception
    InTransit --> Lost: Shipment Lost

    Exception --> InTransit: Exception Resolved
    Exception --> Returned: Return to Sender

    Returned --> Processing: Process Return

    Processing --> Restocked: Items Restocked
    Processing --> Damaged: Items Damaged

    Restocked --> [*]: Complete
    Damaged --> [*]: Complete
    Delivered --> [*]: Complete
    Lost --> Claimed: Insurance Claim

    Claimed --> [*]: Claim Processed
    Cancelled --> [*]: Cancelled

    note right of Ready
        All items staged
        Awaiting carrier
    end note

    note right of InTransit
        With carrier
        Track progress
    end note

    note right of Delivered
        Successfully delivered
        POD received
    end note
```

---

## Operator State Machine

```mermaid
stateDiagram-v2
    [*] --> LoggedOut: Initial State

    LoggedOut --> LoggingIn: Login Attempt

    LoggingIn --> LoggedIn: Auth Success
    LoggingIn --> LoggedOut: Auth Failed

    LoggedIn --> Available: Clock In

    Available --> TaskAssigned: Receive Task
    Available --> Break: Start Break
    Available --> Training: Start Training

    TaskAssigned --> Working: Accept Task
    TaskAssigned --> Available: Reject Task

    Working --> TaskCompleting: Complete Task
    Working --> Paused: Pause Work
    Working --> Incident: Report Issue

    TaskCompleting --> Available: Task Done
    TaskCompleting --> Working: Validation Failed

    Paused --> Working: Resume
    Paused --> Available: Abandon Task

    Incident --> IncidentHandling: Handle Issue

    IncidentHandling --> Working: Resolved
    IncidentHandling --> Escalated: Escalate

    Escalated --> Available: Manager Override
    Escalated --> Suspended: Pending Resolution

    Suspended --> Available: Issue Resolved

    Break --> Returning: Break Ending

    Returning --> Available: Return from Break
    Returning --> Extended: Extend Break

    Extended --> Returning: Time to Return

    Training --> TrainingComplete: Finish Training

    TrainingComplete --> Available: Return to Work

    Available --> LoggingOut: Clock Out

    LoggingOut --> LoggedOut: Logout Complete

    LoggedOut --> [*]: End Session

    note right of Available
        Ready for tasks
        Idle but active
    end note

    note right of Working
        Actively on task
        Track productivity
    end note

    note right of Break
        On scheduled break
        Track time
    end note
```

---

## Complex Process State Machine - Returns

```mermaid
stateDiagram-v2
    [*] --> Initiated: Return Request

    Initiated --> Authorizing: Review Request

    Authorizing --> Authorized: Approve
    Authorizing --> Rejected: Deny

    Rejected --> [*]: End Process

    Authorized --> AwaitingReturn: RMA Issued

    AwaitingReturn --> Receiving: Item Received
    AwaitingReturn --> Expired: Time Limit

    Expired --> [*]: Close Return

    Receiving --> Inspecting: Start Inspection

    Inspecting --> InspectionComplete: Finish Inspection

    InspectionComplete --> Acceptable: Good Condition
    InspectionComplete --> Damaged: Item Damaged
    InspectionComplete --> Different: Wrong Item

    Acceptable --> Processing: Process Return
    Damaged --> Evaluating: Assess Damage
    Different --> Investigating: Investigate

    Evaluating --> PartialCredit: Partial Refund
    Evaluating --> NoCredit: No Refund
    Evaluating --> FullCredit: Full Refund

    Investigating --> Processing: Correct Item
    Investigating --> Rejected: Invalid Return

    Processing --> Restocking: Put Away
    Processing --> Refunding: Issue Refund

    Restocking --> Restocked: In Inventory
    Refunding --> Refunded: Payment Issued

    PartialCredit --> Refunding: Process Partial
    NoCredit --> Notifying: Notify Customer
    FullCredit --> Refunding: Process Full

    Notifying --> Closed: Customer Notified

    Restocked --> Completed: Update Systems
    Refunded --> Completed: Update Records

    Completed --> [*]: Return Complete
    Closed --> [*]: Return Closed

    note right of Inspecting
        Check condition
        Verify item matches
    end note

    note right of Processing
        Update inventory
        Process credits
    end note

    note right of Completed
        Return fully processed
        Records updated
    end note
```