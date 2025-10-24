# Yard Management System - Domain-Driven Design

## Bounded Context: Dock Scheduling & Trailer Management

## Domain Model

### Aggregates

#### YardLocation (Aggregate Root)
**Purpose**: Manages dock doors and yard staging areas

**Properties**:
```java
public class YardLocation {
    private LocationId locationId;
    private LocationType type; // DOCK, STAGING, PARKING
    private LocationStatus status;
    private CurrentOccupant occupant;
    private DockAppointment appointment;
    private LocationCapacity capacity;
}
```

#### Trailer (Entity)
**Purpose**: Tracks trailers in the yard

**Properties**:
```java
public class Trailer {
    private TrailerId trailerId;
    private TrailerStatus status;
    private GPSCoordinates position;
    private DwellTime dwellTime;
    private CarrierInfo carrier;
    private LoadStatus loadStatus;
}
```

#### DockAppointment (Entity)
**Purpose**: Scheduled dock door appointments

**Properties**:
```java
public class DockAppointment {
    private AppointmentId appointmentId;
    private TimeWindow window;
    private Carrier carrier;
    private AppointmentType type;
    private DockDoor assignedDock;
}
```

### Value Objects
- GPSCoordinates (latitude, longitude)
- DwellTime (arrival, maxAllowed)
- TimeWindow (start, end, buffer)
- LoadStatus (EMPTY, LOADED, PARTIAL)

### Domain Services
- DockSchedulingService
- TrailerTrackingService
- YardOptimizationService
- AppointmentService

### Domain Events
- TrailerCheckedIn
- DockAssigned
- TrailerDeparted
- AppointmentScheduled
- DwellTimeExceeded

### Integration
- **Partnership**: Shipment Transportation
- **Upstream**: Order Management (appointments)

## Business Rules
1. **Dwell Time**: Maximum 48 hours
2. **Appointment Window**: 30-minute slots
3. **Dock Capacity**: 50 doors max
4. **Check-in**: Required before dock assignment
5. **Priority**: Live loads over drop trailers