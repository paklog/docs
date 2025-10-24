# Last-Mile Delivery Coordination - Domain-Driven Design

## Bounded Context: Route Optimization & Delivery Management

## Domain Model

### Aggregates

#### DeliveryRoute (Aggregate Root)
**Purpose**: Optimized delivery route using VRP

**Properties**:
```java
public class DeliveryRoute {
    private RouteId routeId;
    private Vehicle vehicle;
    private Driver driver;
    private List<DeliveryStop> stops;
    private RouteStatus status;
    private RouteMetrics metrics;
    private OptimizationAlgorithm algorithm;
}
```

#### DeliveryStop (Entity)
**Purpose**: Individual delivery location

**Properties**:
```java
public class DeliveryStop {
    private StopId stopId;
    private DeliveryAddress address;
    private TimeWindow deliveryWindow;
    private List<Package> packages;
    private StopStatus status;
    private ProofOfDelivery proof;
}
```

### Value Objects
- TimeWindow (2-hour windows)
- ProofOfDelivery (signature, photo, GPS)
- RouteMetrics (distance, duration, cost)
- DeliveryAttempt (max 3 attempts)

### Domain Services
- RouteOptimizationService (VRP with 2-opt)
- DeliverySchedulingService
- TrafficIntegrationService
- ProofCaptureService

### Domain Events
- RouteOptimized
- DeliveryStarted
- StopCompleted
- DeliveryFailed
- ProofCaptured

### Integration
- **Downstream**: From Shipment Transportation
- **External**: Traffic APIs, Customer notifications

## Business Rules
1. **Max Stops**: 50 per route
2. **Time Windows**: 2-hour delivery slots
3. **Attempts**: Maximum 3 per delivery
4. **Vehicle Capacity**: Weight and volume limits
5. **Proof Required**: Signature or photo