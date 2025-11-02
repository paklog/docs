# Shipment & Transportation Service - Domain Architecture & Business Capabilities

## Service Overview

The Shipment & Transportation Service manages the end-to-end shipment lifecycle including carrier integration, shipment creation, tracking, and delivery confirmation. It provides multi-carrier support with extensible adapter architecture, currently supporting FedEx with the ability to add UPS, USPS, and other carriers.

**Architecture Pattern**: Hexagonal Architecture with Domain-Driven Design (DDD)
**Technology Stack**: Spring Boot 3.3, Spring Data MongoDB, Spring Kafka, CloudEvents
**Integration Pattern**: Event-Driven + Adapter Pattern for Carriers

---

## Domain Model & Bounded Context

### Bounded Context: Shipment & Transportation

The Shipment & Transportation bounded context is responsible for all aspects of getting packed orders to their destinations via third-party carriers.

#### Context Boundaries

**Responsibilities (What's IN)**:
- Create shipments from packed orders
- Integrate with multiple shipping carriers
- Generate shipping labels and documentation
- Track shipments through delivery
- Manage carrier credentials and authentication
- Calculate shipping rates across carriers
- Handle delivery confirmations and exceptions
- Manage loads for carrier tendering

**External Dependencies (What's OUT)**:
- Order information (Order Management context)
- Package details and cartonization (Cartonization context, Warehouse Operations context)
- Actual physical package handling (Warehouse Operations context)
- Customer delivery notifications (Notification service - external)
- Carrier rate negotiation and contracting (Procurement - external)

#### Ubiquitous Language

**Core Domain Terms**:

- **Shipment**: One or more packages being sent to a recipient
- **Package**: Individual parcel within a shipment
- **Carrier**: Third-party transportation provider (FedEx, UPS, etc.)
- **Service Level**: Speed of delivery (Ground, 2-Day, Overnight, etc.)
- **Tracking Number**: Unique identifier for tracking shipment progress
- **Shipping Label**: Barcode label affixed to package
- **Dimensional Weight**: Weight calculated from package dimensions
- **Rate Quote**: Shipping cost estimate from carrier
- **Tracking Event**: Status update from carrier (picked up, in transit, delivered)
- **Delivery Exception**: Problem with delivery (delay, damage, address issue)
- **Load**: Group of packages tendered to carrier together
- **Manifest**: List of packages in a load for carrier pickup
- **Proof of Delivery**: Confirmation that package was delivered (signature, photo)

---

## Subdomain Classification

### Core Domain: Carrier Integration & Shipment Management

**Strategic Importance**: MEDIUM-HIGH - Enables final delivery to customers

This domain provides critical business value through:
- Multi-carrier integration for cost optimization
- Real-time tracking for customer satisfaction
- Automated label generation for operational efficiency
- Rate shopping for shipping cost reduction

**Subdomains**:

#### 1. **Multi-Carrier Integration** (Core)
- **Complexity**: High - Multiple carrier APIs with different protocols
- **Strategic Value**: High - Enables cost optimization and carrier diversification
- **Volatility**: Medium - Carrier APIs evolve
- **Business Differentiation**: Competitive advantage
- **Investment Priority**: High - Expand carrier network

#### 2. **Rate Shopping & Optimization** (Core)
- **Complexity**: Medium - Rate comparison and selection logic
- **Strategic Value**: High - Direct cost savings
- **Volatility**: High - Rates change frequently
- **Business Differentiation**: Cost leadership
- **Investment Priority**: High - Continuous optimization

#### 3. **Label Generation & Documentation** (Supporting)
- **Complexity**: Medium - Carrier-specific formats
- **Strategic Value**: Medium - Operational necessity
- **Volatility**: Low - Stable requirements
- **Business Differentiation**: Standard capability
- **Investment Priority**: Medium - Maintain compliance

#### 4. **Shipment Tracking** (Supporting)
- **Complexity**: Medium - Event aggregation and polling
- **Strategic Value**: High - Customer visibility
- **Volatility**: Low - Stable tracking patterns
- **Business Differentiation**: Standard capability
- **Investment Priority**: Medium - Maintain reliability

---

## Domain Model

### Aggregates

#### 1. Shipment (Aggregate Root)

**Description**: Represents a shipment containing one or more packages being sent to a recipient via a carrier.

```java
@AggregateRoot
public class Shipment {
    private String shipmentId; // Aggregate ID
    private String orderId;
    private List<Package> packages;
    private Address recipientAddress;
    private Address senderAddress;
    private Carrier carrier;
    private ServiceLevel serviceLevel;
    private ShipmentStatus status;
    private TrackingInfo trackingInfo;
    private List<TrackingEvent> trackingEvents;
    private LocalDateTime createdAt;
    private LocalDateTime estimatedDelivery;
    private LocalDateTime actualDelivery;
    private ProofOfDelivery proofOfDelivery;

    // Business methods
    public void addPackage(Package package_);
    public void assignCarrier(Carrier carrier, ServiceLevel serviceLevel);
    public void generateLabel();
    public void tender();
    public void updateTracking(TrackingEvent event);
    public void markDelivered(ProofOfDelivery pod);
    public void recordException(DeliveryException exception);
    public void cancel();

    // Invariants
    private void ensureHasAtLeastOnePackage();
    private void ensureValidAddress();
    private void ensureCanBeCancelled();
}
```

**Shipment Status State Machine**:
```
CREATED → LABEL_GENERATED → TENDERED → IN_TRANSIT → OUT_FOR_DELIVERY → DELIVERED
                                ↓           ↓
                            CANCELLED   EXCEPTION
```

**Invariants**:
- At least one package required
- Valid recipient address required
- Carrier and service level assigned before label generation
- Cannot cancel after carrier pickup

**Domain Events**:
- `ShipmentCreatedEvent`
- `ShipmentDispatchedEvent`
- `ShipmentInTransitEvent`
- `ShipmentOutForDeliveryEvent`
- `ShipmentDeliveredEvent`
- `ShipmentExceptionEvent`
- `ShipmentCancelledEvent`

---

#### 2. Load (Aggregate Root)

**Description**: Represents a group of packages being tendered to a carrier together (for manifesting and pickup).

```java
@AggregateRoot
public class Load {
    private String loadId; // Aggregate ID
    private Carrier carrier;
    private List<String> shipmentIds;
    private LoadStatus status;
    private LocalDateTime scheduledPickupTime;
    private LocalDateTime actualPickupTime;
    private LocalDateTime closedAt;
    private String manifestDocument;
    private LoadMetrics metrics;

    // Business methods
    public void addShipment(String shipmentId);
    public void closeLoad();
    public void tender();
    public void recordPickup(LocalDateTime pickupTime);

    // Invariants
    private void ensureAllShipmentsForSameCarrier();
    private void ensureNotAlreadyClosed();
}
```

**Domain Events**:
- `LoadCreatedEvent`
- `LoadClosedEvent`
- `LoadTenderedEvent`
- `LoadPickedUpEvent`

---

### Entities

#### Package

```java
@Entity
public class Package {
    private String packageId;
    private String trackingNumber;
    private Dimensions dimensions;
    private Weight weight;
    private List<String> skus; // Contents
    private Label label;

    public DimensionalWeight calculateDimensionalWeight(int dimFactor);
    public boolean requiresOverweightSurcharge(Weight threshold);
}
```

#### TrackingEvent

```java
@Entity
public class TrackingEvent {
    private String eventId;
    private TrackingEventType type;
    private LocalDateTime timestamp;
    private String location;
    private String description;
    private String carrierEventCode;

    public boolean isDeliveryEvent();
    public boolean isExceptionEvent();
}

enum TrackingEventType {
    PICKED_UP,
    DEPARTED_FACILITY,
    ARRIVED_FACILITY,
    IN_TRANSIT,
    OUT_FOR_DELIVERY,
    DELIVERED,
    DELIVERY_ATTEMPT_FAILED,
    EXCEPTION
}
```

---

### Value Objects

#### Address

```java
@ValueObject
public class Address {
    private String recipientName;
    private String company;
    private String addressLine1;
    private String addressLine2;
    private String city;
    private String state;
    private String postalCode;
    private String country;
    private AddressType type; // RESIDENTIAL, COMMERCIAL

    public boolean isValid();
    public boolean isInternational();
    public boolean isResidential();
    public String formatForLabel();
}
```

#### TrackingInfo

```java
@ValueObject
public class TrackingInfo {
    private String masterTrackingNumber;
    private List<String> packageTrackingNumbers;
    private ShipmentStatus currentStatus;
    private String currentLocation;
    private LocalDateTime lastUpdateTime;

    public boolean hasUpdates(LocalDateTime since);
}
```

#### RateQuote

```java
@ValueObject
public class RateQuote {
    private Carrier carrier;
    private ServiceLevel serviceLevel;
    private Money totalCost;
    private Money baseRate;
    private List<Surcharge> surcharges;
    private int transitDays;
    private LocalDateTime estimatedDelivery;

    public Money getTotalCost();
    public boolean isCheaperThan(RateQuote other);
}

@ValueObject
public class Surcharge {
    private String type; // FUEL, RESIDENTIAL, DELIVERY_AREA, etc.
    private Money amount;
}
```

#### ProofOfDelivery

```java
@ValueObject
public class ProofOfDelivery {
    private LocalDateTime deliveredAt;
    private String recipientName; // Who signed
    private String deliveryLocation; // "Front door", "Mailroom"
    private byte[] signature; // Image
    private byte[] photo; // Delivery photo
    private String driverNotes;
}
```

---

## Domain Services

### CarrierSelectionService

**Responsibility**: Select optimal carrier based on shipment requirements and business rules.

```java
@DomainService
public class CarrierSelectionService {

    public Carrier selectCarrier(
        Shipment shipment,
        List<RateQuote> quotes,
        SelectionStrategy strategy
    );

    public Carrier selectForCost(List<RateQuote> quotes);
    public Carrier selectForSpeed(List<RateQuote> quotes);
    public boolean canCarrierShip(Carrier carrier, Shipment shipment);
}
```

---

### RateShoppingService

**Responsibility**: Retrieve and compare rates from multiple carriers.

```java
@DomainService
public class RateShoppingService {

    public List<RateQuote> getRateQuotes(
        List<Package> packages,
        Address destination,
        ServiceLevel serviceLevel
    );

    public RateQuote getLowestCostQuote(List<RateQuote> quotes);
    public RateQuote getFastestQuote(List<RateQuote> quotes);
}
```

---

### DimensionalWeightCalculator

**Responsibility**: Calculate dimensional weight for rate determination.

```java
@DomainService
public class DimensionalWeightCalculator {

    public DimensionalWeight calculate(
        Dimensions packageDimensions,
        Carrier carrier
    );

    public Weight getChargeableWeight(
        Weight actualWeight,
        DimensionalWeight dimWeight
    );

    private int getDimFactor(Carrier carrier); // FedEx: 139, UPS: 139
}
```

---

## Carrier Adapter Pattern

### ICarrierAdapter Interface

```java
public interface ICarrierAdapter {

    // Rating
    RateQuote getRateQuote(ShipmentRequest request);

    // Shipping
    ShipmentResponse createShipment(ShipmentRequest request);
    Label generateLabel(String shipmentId, LabelFormat format);
    void voidShipment(String trackingNumber);

    // Tracking
    TrackingInfo getTracking(String trackingNumber);
    List<TrackingEvent> getTrackingHistory(String trackingNumber);

    // Address validation
    AddressValidationResult validateAddress(Address address);

    // Load management
    ManifestResult createManifest(List<String> trackingNumbers);
}
```

### FedEx Adapter Implementation

```java
@Component
public class FedExAdapter implements ICarrierAdapter {

    private final FedExApiClient apiClient;
    private final FedExRequestSigner signer;
    private final FedExApiProperties properties;

    @Override
    public RateQuote getRateQuote(ShipmentRequest request) {
        // Call FedEx Rating API
        FedExRateRequest fedexRequest = mapToFedExRequest(request);
        FedExRateResponse response = apiClient.getRates(fedexRequest);
        return mapToRateQuote(response);
    }

    @Override
    public ShipmentResponse createShipment(ShipmentRequest request) {
        // Call FedEx Shipping API
        FedExShipRequest fedexRequest = mapToFedExShipRequest(request);
        FedExShipResponse response = apiClient.createShipment(fedexRequest);
        return mapToShipmentResponse(response);
    }

    // ... other methods
}
```

---

## Application Layer

### Ports (Interfaces)

#### Input Ports (Use Cases)

```java
// Commands
public interface CreateShipmentCommand {
    Shipment execute(CreateShipmentRequest request);
}

public interface GenerateLabelCommand {
    Label execute(String shipmentId, LabelFormat format);
}

public interface CancelShipmentCommand {
    void execute(String shipmentId);
}

public interface CreateLoadCommand {
    Load execute(CreateLoadRequest request);
}

// Queries
public interface GetShipmentTrackingQuery {
    TrackingInfo execute(String shipmentId);
}

public interface GetRateQuotesQuery {
    List<RateQuote> execute(RateQuoteRequest request);
}
```

#### Output Ports (Dependencies)

```java
// Repository ports
public interface ShipmentRepository {
    Optional<Shipment> findById(String shipmentId);
    void save(Shipment shipment);
    List<Shipment> findByStatus(ShipmentStatus status);
}

public interface LoadRepository {
    Optional<Load> findById(String loadId);
    void save(Load load);
}

// Carrier adapter registry
public interface CarrierAdapterRegistry {
    ICarrierAdapter getAdapter(Carrier carrier);
    List<ICarrierAdapter> getAllAdapters();
}

// Event publishing
public interface EventPublisher {
    void publish(DomainEvent event);
}
```

---

## Infrastructure Layer

### Adapters

#### Inbound Adapters

**REST Controller**
```java
@RestController
@RequestMapping("/api/v1/shipments")
public class ShipmentController {

    @PostMapping
    public ResponseEntity<ShipmentResponse> createShipment(
        @RequestBody CreateShipmentRequest request
    );

    @GetMapping("/{shipmentId}/tracking")
    public ResponseEntity<TrackingResponse> getTracking(
        @PathVariable String shipmentId
    );

    @GetMapping("/{shipmentId}/label")
    public ResponseEntity<byte[]> getLabel(
        @PathVariable String shipmentId,
        @RequestParam(defaultValue = "PDF") LabelFormat format
    );

    @PostMapping("/{shipmentId}/cancel")
    public ResponseEntity<Void> cancelShipment(@PathVariable String shipmentId);

    @PostMapping("/rate-quotes")
    public ResponseEntity<List<RateQuoteResponse>> getRateQuotes(
        @RequestBody RateQuoteRequest request
    );
}
```

**Event Listener**
```java
@Component
public class WarehouseEventListener {

    @KafkaListener(topics = "fulfillment.warehouse.v1.events")
    public void handlePackingCompleted(PackingCompletedEvent event) {
        // Create shipment for packed order
    }
}
```

#### Background Jobs

**Tracking Update Job**
```java
@Component
@Scheduled(fixedDelay = 3600000) // Every hour
public class TrackingUpdateJob {

    public void updateActiveShipments() {
        List<Shipment> active = shipmentRepository.findByStatus(IN_TRANSIT);

        for (Shipment shipment : active) {
            try {
                updateShipmentTracking(shipment);
            } catch (Exception e) {
                // Log and continue
            }
        }
    }

    private void updateShipmentTracking(Shipment shipment) {
        ICarrierAdapter adapter = adapterRegistry.getAdapter(shipment.getCarrier());
        TrackingInfo info = adapter.getTracking(shipment.getTrackingNumber());

        // Update shipment with new tracking events
        shipment.updateTracking(info);
        shipmentRepository.save(shipment);
    }
}
```

---

## Business Capabilities

### L1: Transportation Management

Comprehensive management of shipments from creation through final delivery.

---

### L2: Shipment Creation & Management

#### L3.1: Shipment Creation from Packages
- Create shipments from packed orders
- Capture package details
- Assign recipient address
- Initialize shipment record

#### L3.2: Multi-Package Shipment Handling
- Group multiple packages under single shipment
- Individual or master tracking numbers
- Package sequencing
- All-delivered confirmation

#### L3.3: Shipment Status Tracking
- Track through complete lifecycle
- Real-time status updates
- Status history maintenance
- Event-driven notifications

#### L3.4: Shipment Cancellation
- Cancel before carrier pickup
- Void labels with carrier
- Release inventory (if needed)
- Refund processing

---

### L2: Carrier Integration & Management

#### L3.5: FedEx Integration
- Full FedEx API integration
- OAuth 2.0 authentication
- Rating, shipping, tracking APIs
- Multiple service levels

#### L3.6: Carrier Adapter Pattern
- Extensible adapter architecture
- Consistent interface across carriers
- Dynamic carrier selection
- Adapter registry

#### L3.7: Carrier Credentials Management
- Secure credential storage
- Per-carrier authentication
- OAuth token management
- Credential rotation

#### L3.8: Carrier Selection Strategy
- Cost-based selection
- Service level matching
- Geographic coverage
- Performance-based selection

---

### L2: Rate Shopping & Cost Optimization

#### L3.9: Multi-Carrier Rate Quotes
- Parallel rate requests
- Rate aggregation
- Cost comparison
- Surcharge calculation

#### L3.10: Dimensional Weight Calculation
- Carrier-specific dim factors
- Actual vs. dimensional weight
- Chargeable weight determination

#### L3.11: Surcharge Calculation
- Fuel surcharges
- Residential delivery fees
- Delivery area surcharges
- Special handling fees

---

### L2: Label Generation & Documentation

#### L3.12: Shipping Label Generation
- Carrier-compliant labels
- Multiple formats (PDF, PNG, ZPL)
- Barcode generation
- Label storage and retrieval

#### L3.13: Tracking Number Assignment
- Carrier tracking numbers
- Format validation
- Unique per package
- Master tracking for multi-package

#### L3.14: Customs Documentation (International)
- Commercial invoice generation
- Harmonized tariff codes
- Country-specific requirements
- Electronic customs submission

---

### L2: Shipment Tracking & Visibility

#### L3.15: Real-Time Tracking Updates
- Scheduled polling of carrier APIs
- Event-driven updates
- Incremental event storage
- Status change notifications

#### L3.16: Tracking Event History
- Chronological event log
- Location and timestamp capture
- Event deduplication
- Complete audit trail

#### L3.17: Tracking Number Lookup
- Lookup by shipment ID or tracking number
- Current status and history
- Estimated delivery date
- Multi-package tracking

#### L3.18: Delivery Confirmation
- Proof of delivery capture
- Signature storage
- Photo evidence
- Delivery location details

---

### L2: Load Management & Carrier Tendering

#### L3.19: Load Creation
- Group packages for carrier pickup
- Carrier-specific loads
- Load capacity tracking

#### L3.20: Load Tendering & Manifesting
- Generate manifests
- Electronic tender submission
- Pickup scheduling
- Load closeout

---

### L2: Exception Handling

#### L3.21: Delivery Exception Management
- Exception detection
- Automated alerting
- Reason code capture
- Resolution workflow

---

## Integration Patterns

### Context Mapping

#### Order Management (Upstream - Customer/Supplier)
- **Type**: Customer/Supplier
- **Integration**: Event-driven
- **Contract**: Shipment requests via events

#### Warehouse Operations (Upstream - Partnership)
- **Type**: Partnership
- **Integration**: Event-driven (bi-directional)
- **Collaboration**: Packing completion → shipment creation

#### Product Catalog (Upstream - Conformist)
- **Type**: Conformist
- **Integration**: REST (dimensions/weight for rating)

#### Carriers (Downstream - Adapter Pattern)
- **Type**: Adapter/Anti-Corruption Layer
- **Integration**: REST APIs (carrier-specific)
- **Protection**: Adapter isolates domain from carrier changes

---

## Event Schemas

### ShipmentCreatedEvent

```json
{
  "specversion": "1.0",
  "type": "com.paklog.shipment.created",
  "source": "shipment-transportation-service",
  "id": "evt-shipment-123",
  "time": "2025-10-18T10:30:00Z",
  "data": {
    "shipmentId": "SHIP-12345",
    "orderId": "ORD-67890",
    "carrier": "FEDEX",
    "serviceLevel": "GROUND",
    "trackingNumber": "123456789012",
    "estimatedDelivery": "2025-10-22T17:00:00Z",
    "packages": [
      {
        "packageId": "PKG-001",
        "trackingNumber": "123456789012",
        "weight": {"value": 5.5, "unit": "POUNDS"}
      }
    ]
  }
}
```

### ShipmentDeliveredEvent

```json
{
  "specversion": "1.0",
  "type": "com.paklog.shipment.delivered",
  "source": "shipment-transportation-service",
  "id": "evt-delivery-456",
  "time": "2025-10-22T15:30:00Z",
  "data": {
    "shipmentId": "SHIP-12345",
    "orderId": "ORD-67890",
    "trackingNumber": "123456789012",
    "deliveredAt": "2025-10-22T15:30:00Z",
    "recipientName": "John Doe",
    "deliveryLocation": "Front door",
    "signature": true
  }
}
```

---

## Quality Attributes

### Reliability
- **Carrier API Availability**: Circuit breakers for carrier downtime
- **Retry Logic**: Exponential backoff for transient failures
- **Fallback**: Alternate carriers on failure

### Performance
- **Rate Quote Response**: <2 seconds for multi-carrier
- **Label Generation**: <2 seconds average
- **Tracking Updates**: Hourly for active shipments

### Integration
- **Carrier Diversity**: Currently FedEx, expandable to UPS, USPS, DHL
- **API Versioning**: Support carrier API evolution
- **Adapter Isolation**: Domain protected from carrier changes

---

## Summary

The Shipment & Transportation Service provides comprehensive shipment management:

- **Multi-Carrier Support**: Extensible adapter architecture
- **Cost Optimization**: Rate shopping across carriers
- **Real-Time Tracking**: Automated tracking updates
- **Clean Architecture**: Adapters protect domain from carrier specifics
- **Scalability**: Event-driven integration

Business Impact: 10-20% cost savings through carrier optimization, >95% on-time delivery, hourly tracking updates, <2 second label generation.
