# Yard Management System - Business Capabilities

**Service Overview**: The Yard Management System orchestrates all yard operations including trailer tracking, dock door scheduling, appointment management, and yard jockey coordination, optimizing the flow of inbound and outbound shipments through the facility perimeter.

**Architecture**: Hexagonal Architecture (Ports & Adapters)
**Technology Stack**: Spring Boot 3.2, MongoDB (with geospatial indexes), Apache Kafka, GPS Integration
**Domain Model**: Event-driven with real-time location tracking

---

## L1: Yard Operations Management

### L1.1: Description
Optimize yard utilization and trailer flow through intelligent dock scheduling, real-time tracking, and automated yard moves to maximize throughput and minimize dwell time.

### L1.2: Strategic Value
- **Operational Efficiency**: Reduce trailer dwell time by 40%
- **Visibility**: Real-time location of all yard assets
- **Cost Reduction**: Minimize detention and demurrage charges
- **Safety**: Controlled yard traffic and movements

---

## L2: Trailer Management

### L2.1: Description
Track and manage all trailers in the yard from gate check-in through departure, maintaining real-time visibility and status.

### L2.2: Business Value
- Complete trailer visibility and tracking
- Reduced search time for trailers
- Optimized trailer utilization
- Automated check-in/check-out processes

### L2.3: L3 Capabilities

#### L3.1.1: Gate Check-in/Check-out
**Description**: Automate trailer processing at yard gates with driver identification, documentation validation, and seal verification.

**Technical Implementation**:
- RFID/barcode scanning
- Driver credential validation
- Documentation verification
- Seal integrity checking

**Business Rules**:
- Valid appointment required for entry
- Maximum dwell time: 48 hours
- Security seal verification mandatory
- Photo documentation required

**Key Metrics**:
- Gate processing time
- Check-in accuracy
- Documentation compliance
- Queue length

**Related Services**: Shipment Transportation (carrier data)

---

#### L3.1.2: Real-time GPS Tracking
**Description**: Track trailer locations within the yard using GPS transponders with geofencing and movement history.

**Technical Implementation**:
- GPS coordinate updates (every 30 seconds)
- Geospatial indexing in MongoDB
- Movement history tracking
- Geofence alerts

**Business Rules**:
- Position accuracy: within 3 meters
- Update frequency: 30 seconds
- History retention: 30 days
- Unauthorized movement alerts

**Key Metrics**:
- Location accuracy
- Update latency
- Tracking coverage
- Alert response time

**Related Services**: Physical Tracking Service

---

## L2: Dock Door Management

### L2.1: Description
Optimize dock door assignments and scheduling to maximize throughput while minimizing trailer movements and wait times.

### L2.2: Business Value
- Increased dock utilization to 90%
- Reduced trailer movements by 30%
- Minimized loading/unloading time
- Better appointment compliance

### L2.3: L3 Capabilities

#### L3.2.1: Intelligent Dock Assignment
**Description**: Automatically assign optimal dock doors based on trailer type, contents, destination, and current dock availability.

**Technical Implementation**:
- Constraint-based optimization
- Distance minimization algorithms
- Load type compatibility
- Real-time availability tracking

**Business Rules**:
- Refrigerated loads to cold docks
- Hazmat to designated areas
- Closest available dock preference
- Cross-dock priority lanes

**Key Metrics**:
- Dock utilization rate
- Assignment optimality
- Trailer travel distance
- Wait time to dock

**Related Services**: Cross-Docking Operations

---

#### L3.2.2: Dock Scheduling Optimization
**Description**: Schedule dock appointments to balance workload, minimize congestion, and ensure resource availability.

**Technical Implementation**:
- Time-slot management (30-minute windows)
- Capacity planning algorithms
- Resource availability checking
- Schedule conflict resolution

**Business Rules**:
- 30-minute appointment windows
- Maximum 2 trailers per dock per day
- 1-hour buffer between appointments
- Priority for time-sensitive loads

**Key Metrics**:
- Schedule adherence
- Dock turnover rate
- Appointment fulfillment
- Resource utilization

**Related Services**: WES Orchestration Engine

---

## L2: Appointment Management

### L2.1: Description
Manage carrier appointments for deliveries and pickups, ensuring smooth yard flow and warehouse readiness.

### L2.2: Business Value
- Reduced carrier wait times by 50%
- Improved warehouse planning
- Better resource allocation
- Enhanced carrier relationships

### L2.3: L3 Capabilities

#### L3.3.1: Carrier Appointment Booking
**Description**: Enable carriers to schedule appointments through web portal or API with real-time availability checking.

**Technical Implementation**:
- Web portal and API interfaces
- Real-time slot availability
- Automated confirmation
- Calendar integration

**Business Rules**:
- Advance booking: 24-72 hours
- Same-day appointments limited
- Cancellation: 4 hours notice
- No-show penalties applied

**Key Metrics**:
- Booking lead time
- Slot utilization
- Cancellation rate
- No-show rate

**Related Services**: Shipment Transportation

---

#### L3.3.2: Appointment Coordination
**Description**: Coordinate appointments with warehouse operations to ensure resources and space availability.

**Technical Implementation**:
- Warehouse capacity checking
- Labor availability validation
- Equipment reservation
- Cross-functional notifications

**Business Rules**:
- Verify receiving capacity
- Confirm labor availability
- Reserve required equipment
- Alert relevant departments

**Key Metrics**:
- Coordination success rate
- Resource conflicts
- Preparation time
- Department readiness

**Related Services**: Warehouse Operations

---

## L2: Yard Jockey Operations

### L2.1: Description
Manage yard jockey tasks and movements to efficiently relocate trailers between parking, staging, and dock positions.

### L2.2: Business Value
- Optimized jockey utilization
- Reduced trailer movement time
- Improved safety through controlled moves
- Better task prioritization

### L2.3: L3 Capabilities

#### L3.4.1: Move Task Assignment
**Description**: Assign trailer move tasks to available jockeys based on location, priority, and equipment availability.

**Technical Implementation**:
- Task queue management
- Jockey location tracking
- Priority-based assignment
- Route optimization

**Business Rules**:
- Closest available jockey
- High-priority moves first
- Maximum 10 tasks in queue
- Safety check requirements

**Key Metrics**:
- Task completion time
- Jockey utilization
- Queue length
- Priority compliance

**Related Services**: Task Execution Service

---

#### L3.4.2: Move Optimization
**Description**: Optimize the sequence and routing of trailer moves to minimize total travel distance and time.

**Technical Implementation**:
- Multi-stop route planning
- Deadhead minimization
- Batch move grouping
- Dynamic re-optimization

**Business Rules**:
- Minimize empty travels
- Group moves by area
- Urgent moves override optimization
- Safety zones respected

**Key Metrics**:
- Total distance saved
- Move efficiency
- Deadhead percentage
- Optimization impact

**Related Services**: Robotics Fleet Management

---

## L2: Yard Analytics

### L2.1: Description
Provide comprehensive analytics on yard performance, dwell times, and bottlenecks to drive continuous improvement.

### L2.2: Business Value
- Identify and eliminate bottlenecks
- Reduce detention charges
- Improve yard layout decisions
- Optimize resource allocation

### L2.3: L3 Capabilities

#### L3.5.1: Dwell Time Analysis
**Description**: Track and analyze trailer dwell times to identify delays and optimize yard flow.

**Technical Implementation**:
- Time-in-yard tracking
- Dwell time by trailer type
- Root cause analysis
- Trend identification

**Business Rules**:
- Alert at 24-hour dwell
- Escalation at 36 hours
- Maximum 48-hour limit
- Daily dwell reports

**Key Metrics**:
- Average dwell time
- Dwell time distribution
- Detention costs
- On-time departure rate

**Related Services**: Performance Intelligence

---

#### L3.5.2: Capacity Planning
**Description**: Analyze yard utilization patterns to optimize capacity and plan for peak periods.

**Technical Implementation**:
- Utilization heat maps
- Peak period analysis
- Capacity forecasting
- Space optimization

**Business Rules**:
- Target 85% utilization
- Reserve 10% for emergencies
- Seasonal adjustment factors
- Weekly capacity reviews

**Key Metrics**:
- Yard utilization rate
- Peak capacity percentage
- Space turnover rate
- Overflow frequency

**Related Services**: Predictive Analytics

---

## Integration Points

### Inbound Integrations
- **Shipment Transportation**: Carrier and shipment data
- **Order Management**: Inbound/outbound requirements
- **WES Orchestration**: Dock work assignments
- **Cross-Docking**: Direct transfer requirements

### Outbound Integrations
- **Warehouse Operations**: Dock readiness
- **Task Execution**: Yard jockey tasks
- **Physical Tracking**: Location updates
- **Performance Intelligence**: Yard metrics

---

## Business Events

### Domain Events Published
- `TrailerCheckedInEvent`: Trailer arrived at gate
- `TrailerCheckedOutEvent`: Trailer departed
- `DockAssignedEvent`: Dock door assigned
- `DockReleasedEvent`: Dock door freed
- `TrailerMovedEvent`: Trailer relocated
- `AppointmentScheduledEvent`: New appointment created
- `AppointmentArrivedEvent`: Appointment checked in
- `AppointmentCompletedEvent`: Appointment finished
- `YardCapacityWarningEvent`: Capacity threshold reached
- `DwellTimeAlertEvent`: Excessive dwell detected

### Events Consumed
- `ShipmentArrivingEvent`: Prepare for arrival
- `OrderReadyEvent`: Schedule pickup
- `DockWorkCompleteEvent`: Release dock
- `CrossDockRequiredEvent`: Priority dock assignment

---

## Performance Targets

- Gate processing: < 5 minutes
- Dock assignment: < 30 seconds
- GPS update latency: < 1 second
- Move task assignment: < 1 minute
- Appointment booking: < 10 seconds
- Yard location query: < 100ms
- System availability: 99.9%