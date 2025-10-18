# Shipment & Transportation Service - Business Capabilities

**Service Overview**: The Shipment & Transportation Service manages the end-to-end shipment lifecycle including carrier integration, shipment creation, tracking, and delivery confirmation. It provides multi-carrier support with extensible adapter architecture, currently supporting FedEx with the ability to add UPS, USPS, and other carriers.

**Architecture**: Hexagonal Architecture with Domain-Driven Design (DDD)
**Technology Stack**: Spring Boot 3.3, Spring Data MongoDB, Spring Kafka, CloudEvents
**Domain Model**: Shipment and Load aggregates with carrier adapter pattern

---

## L1: Transportation Management

### L1.1: Description
Comprehensive management of shipments from creation through final delivery, including carrier selection, rate shopping, label generation, tracking, and proof of delivery.

### L1.2: Strategic Value
- **Cost Optimization**: Select optimal carriers and service levels for cost savings
- **Customer Satisfaction**: Provide accurate tracking and delivery estimates
- **Operational Efficiency**: Automate carrier integration and label generation
- **Scalability**: Support multiple carriers and service levels
- **Visibility**: Real-time tracking across all carriers

---

## L2: Shipment Creation & Management

### L2.1: Description
Create and manage shipments from packed orders, including package information, recipient details, and carrier selection.

### L2.2: Business Value
- Automated shipment creation from warehouse output
- Support for multi-package shipments
- Flexible carrier and service level selection
- Complete shipment lifecycle management

### L2.3: L3 Capabilities

#### L3.1.1: Shipment Creation from Packages
**Description**: Create shipments from packed orders, capturing package details and recipient information.

**Technical Implementation**:
- `CreateShipmentCommand` processed via application service
- `Shipment` aggregate instantiation
- Package details from cartonization service
- Recipient address from order management
- MongoDB persistence with event publishing

**Business Rules**:
- Shipment requires at least one package
- Recipient address must be valid and deliverable
- Total weight calculated from packages
- Dimensional weight calculated if applicable
- Service level defaults to standard if not specified

**Domain Model**:
```java
@AggregateRoot
class Shipment {
  private String shipmentId;
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
}

@Entity
class Package {
  private String packageId;
  private Dimensions dimensions;
  private Weight weight;
  private List<String> skus;
}
```

**Key Metrics**:
- Shipments created per hour
- Average packages per shipment
- Shipment creation processing time

**API Endpoints**:
- `POST /api/v1/shipments` - Create shipment

**Domain Events**:
- `ShipmentCreatedEvent` - Published when shipment created

**Related Services**:
- Order Management (order details)
- Warehouse Operations (package information)
- Cartonization (package dimensions)

---

#### L3.1.2: Multi-Package Shipment Handling
**Description**: Support shipments consisting of multiple packages for the same order.

**Technical Implementation**:
- Grouping of packages under single shipment entity
- Individual tracking numbers per package (carrier-dependent)
- Master tracking number for shipment
- Package sequencing and labeling

**Business Rules**:
- All packages share same recipient address
- All packages typically use same carrier (exceptions allowed)
- Each package has individual dimensions and weight
- Total shipment cost calculated across all packages
- Delivery confirmation when all packages delivered

**Key Metrics**:
- Percentage of multi-package shipments
- Average packages per multi-package shipment
- Multi-package delivery completion rate

**Related Services**: Cartonization (multi-carton solutions)

---

#### L3.1.3: Shipment Status Tracking
**Description**: Track shipment through its complete lifecycle from creation to delivery.

**Technical Implementation**:
- State machine for shipment status transitions
- Status updates from carrier tracking APIs
- Manual status updates supported
- Event publication on status changes

**Shipment Status States**:
- `CREATED` - Shipment record created
- `LABEL_GENERATED` - Shipping label created
- `TENDERED` - Handed to carrier
- `IN_TRANSIT` - In carrier network
- `OUT_FOR_DELIVERY` - On delivery vehicle
- `DELIVERED` - Successfully delivered
- `EXCEPTION` - Delivery exception/delay
- `RETURNED` - Returned to sender

**Business Rules**:
- Status updates follow defined state transitions
- Historical status retained (append-only)
- Timestamps captured for all status changes
- Exceptions require reason codes

**Key Metrics**:
- Average time in each status
- Exception rate by carrier
- On-time delivery rate

**Domain Events**:
- `ShipmentDispatchedEvent`
- `ShipmentInTransitEvent`
- `ShipmentDeliveredEvent`
- `ShipmentExceptionEvent`

**Related Services**: Order Management (status updates)

---

#### L3.1.4: Shipment Cancellation
**Description**: Cancel shipments before carrier pickup or in early transit stages.

**Technical Implementation**:
- Void label request to carrier API
- Status transition to CANCELLED
- Refund processing for carrier charges
- Notification to warehouse and order management

**Business Rules**:
- Can only cancel before carrier pickup (typically)
- Some carriers charge cancellation fees
- Voided labels cannot be reused
- Must create new shipment if needed
- Inventory adjustments may be required

**Key Metrics**:
- Cancellation rate
- Cancellations by status
- Cancellation cost impact

**API Endpoints**:
- `POST /api/v1/shipments/{shipmentId}/cancel`

**Domain Events**:
- `ShipmentCancelledEvent`

**Related Services**: Order Management (order cancellations)

---

## L2: Carrier Integration & Management

### L2.1: Description
Integrate with multiple shipping carriers through extensible adapter pattern, supporting carrier-specific APIs and requirements.

### L2.2: Business Value
- Multi-carrier support for flexibility and cost optimization
- Carrier-agnostic business logic
- Easy addition of new carriers
- Carrier failover capabilities

### L2.3: L3 Capabilities

#### L3.2.1: FedEx Integration
**Description**: Full integration with FedEx APIs for label generation, rate quotes, and tracking.

**Technical Implementation**:
- `FedExAdapter` implements `ICarrierAdapter` interface
- `FedExApiClient` for HTTP API communication
- OAuth 2.0 authentication with token refresh
- Request signing with `FedExRequestSigner`
- Error handling and retry logic

**Supported FedEx APIs**:
- **Rating API**: Get rate quotes for shipments
- **Shipping API**: Create labels and shipments
- **Tracking API**: Track shipment status
- **Address Validation API**: Validate recipient addresses

**FedEx Service Levels**:
- `FEDEX_GROUND` - Ground delivery (1-5 business days)
- `FEDEX_2_DAY` - 2-day delivery
- `FEDEX_OVERNIGHT` - Next-day delivery
- `FEDEX_PRIORITY_OVERNIGHT` - Priority next-day
- `FEDEX_INTERNATIONAL_PRIORITY` - International express

**Business Rules**:
- API credentials stored securely (encrypted)
- Token refresh automated before expiration
- Rate limiting respected (API quotas)
- Retry failed requests (transient errors)
- Fallback to alternate carrier on failure

**Key Metrics**:
- FedEx API success rate (target: >99.5%)
- API response time (p95)
- Authentication failures
- Rate quote accuracy

**Configuration**:
```java
@ConfigurationProperties(prefix = "carrier.fedex")
class FedExApiProperties {
  private String apiUrl;
  private String clientId;
  private String clientSecret;
  private String accountNumber;
  private String meterNumber;
}
```

**Related Services**: None (external carrier)

---

#### L3.2.2: Carrier Adapter Pattern
**Description**: Extensible adapter pattern to support multiple carriers with consistent interface.

**Technical Implementation**:
- `ICarrierAdapter` interface defines contract
- Carrier-specific adapters implement interface
- Adapter selection via strategy pattern
- Adapter registry for dynamic carrier selection

**Adapter Interface**:
```java
interface ICarrierAdapter {
  RateQuote getRateQuote(ShipmentRequest request);
  Label createShipment(ShipmentRequest request);
  TrackingInfo getTracking(String trackingNumber);
  void voidLabel(String trackingNumber);
  AddressValidationResult validateAddress(Address address);
}
```

**Supported Carriers** (Current & Planned):
- ✅ **FedEx** - Fully implemented
- 🔄 **UPS** - Planned
- 🔄 **USPS** - Planned
- 🔄 **DHL** - Planned

**Business Rules**:
- All carriers must implement full interface
- Adapter failures trigger fallback to next carrier
- Carrier selection based on cost, service level, restrictions
- Carrier credentials managed per adapter

**Key Metrics**:
- Carrier usage distribution
- Carrier performance comparison
- Adapter error rates by carrier

**Related Services**: None (infrastructure pattern)

---

#### L3.2.3: Carrier Credentials Management
**Description**: Secure management of carrier API credentials and authentication.

**Technical Implementation**:
- Encrypted storage of API keys and secrets
- Per-carrier credential configuration
- Credential rotation support
- OAuth token management for carriers supporting it

**Business Rules**:
- Credentials encrypted at rest
- Access restricted to carrier adapters
- Credential expiration monitoring
- Automated alerts on authentication failures
- Support for multiple accounts per carrier (future)

**Key Metrics**:
- Authentication success rate
- Token refresh frequency
- Credential rotation compliance

**Related Services**: None (security infrastructure)

---

#### L3.2.4: Carrier Selection Strategy
**Description**: Automatically select optimal carrier based on shipment requirements and business rules.

**Technical Implementation**:
- Strategy pattern for selection logic
- Multi-factor decision making
- Configurable selection rules
- Support for manual override

**Selection Factors**:
1. **Cost**: Select lowest-cost carrier for service level
2. **Service Level**: Match required delivery speed
3. **Geographic Coverage**: Carrier services destination
4. **Weight/Size Restrictions**: Carrier can handle package
5. **Special Requirements**: Hazmat, signature, etc.
6. **Carrier Performance**: Historical on-time rate
7. **Business Rules**: Preferred carriers, blacklists

**Business Rules**:
- Default to cost optimization for standard service
- Rush orders use fastest available carrier
- International shipments require international carriers
- Hazmat restrictions filter carrier options
- Customer preferences honored if specified

**Key Metrics**:
- Carrier selection distribution
- Cost savings from optimization
- Override rate (manual selections)

**Related Services**: None (internal decision logic)

---

## L2: Rate Shopping & Cost Optimization

### L2.1: Description
Provide rate quotes from multiple carriers and service levels to optimize shipping costs.

### L2.2: Business Value
- Minimize shipping costs through rate comparison
- Provide accurate shipping cost estimates
- Support customer shipping choices
- Enable cost-based carrier selection

### L2.3: L3 Capabilities

#### L3.3.1: Multi-Carrier Rate Quotes
**Description**: Retrieve rate quotes from multiple carriers for comparison and selection.

**Technical Implementation**:
- Parallel API calls to carrier rating endpoints
- Rate quote aggregation and normalization
- Caching of rate quotes (short TTL)
- Fallback on carrier API failures

**Business Rules**:
- Request rates from all eligible carriers
- Filter carriers by service level match
- Include all surcharges in total cost
- Sort by total cost (ascending)
- Cache rates for 5 minutes

**Rate Quote Response**:
```json
{
  "quotes": [
    {
      "carrier": "FEDEX",
      "serviceLevel": "GROUND",
      "totalCost": 12.50,
      "baseRate": 10.00,
      "fuelSurcharge": 1.50,
      "otherSurcharges": 1.00,
      "estimatedDelivery": "2025-10-22",
      "transitDays": 4
    },
    {
      "carrier": "UPS",
      "serviceLevel": "GROUND",
      "totalCost": 13.25,
      "baseRate": 10.50,
      "fuelSurcharge": 1.75,
      "otherSurcharges": 1.00,
      "estimatedDelivery": "2025-10-23",
      "transitDays": 5
    }
  ]
}
```

**Key Metrics**:
- Rate quote response time
- Carrier API availability
- Cost variance between carriers
- Quote accuracy vs. actual costs

**API Endpoints**:
- `POST /api/v1/shipments/rate-quotes` - Get rate quotes

**Related Services**: Order Management (shipping cost estimates)

---

#### L3.3.2: Dimensional Weight Calculation
**Description**: Calculate dimensional weight for rate determination.

**Technical Implementation**:
- Formula: (L × W × H) / DIM_FACTOR
- Carrier-specific dim factors (FedEx: 139, UPS: 139)
- Compare actual weight vs. dimensional weight
- Charge based on greater of the two

**Business Rules**:
- Use actual weight if greater than dim weight
- Use dim weight if greater than actual weight
- Dim factor varies by carrier and service level
- International may have different factors
- Round up to next whole number

**Key Metrics**:
- Dimensional weight vs. actual weight ratio
- Percentage of shipments charged by dim weight
- Impact on shipping costs

**Related Services**: Product Catalog (package dimensions)

---

#### L3.3.3: Surcharge Calculation
**Description**: Calculate applicable surcharges (fuel, residential, etc.) for accurate total cost.

**Technical Implementation**:
- Surcharge rules engine
- Carrier-specific surcharge tables
- Periodic surcharge updates
- Surcharge breakdown in quotes

**Common Surcharges**:
- **Fuel Surcharge**: Percentage of base rate (variable)
- **Residential Delivery**: Fixed fee for residential addresses
- **Delivery Area Surcharge**: Remote/extended areas
- **Large Package**: Oversized packages
- **Additional Handling**: Heavy or irregular packages
- **Signature Required**: Adult signature, indirect signature
- **Saturday Delivery**: Weekend delivery fee

**Business Rules**:
- All surcharges included in total cost
- Surcharge tables updated weekly (fuel)
- Residential detection via address type
- Automatic calculation (no manual entry)

**Key Metrics**:
- Surcharge percentage of total cost
- Most common surcharges
- Surcharge trend analysis

**Related Services**: None (carrier data)

---

## L2: Label Generation & Documentation

### L2.1: Description
Generate shipping labels, customs documentation, and other required shipping documents.

### L2.2: Business Value
- Automated label generation eliminates manual entry
- Compliance with carrier label requirements
- Support for international shipping documentation
- Barcode generation for warehouse scanning

### L2.3: L3 Capabilities

#### L3.4.1: Shipping Label Generation
**Description**: Generate carrier-compliant shipping labels with barcodes and tracking numbers.

**Technical Implementation**:
- Carrier API integration for label creation
- PDF/PNG label format support
- Thermal printer format support (ZPL)
- Label storage and retrieval

**Business Rules**:
- Labels generated after shipment creation
- One label per package (multi-package support)
- Labels include barcode with tracking number
- Sender and recipient addresses printed
- Service level and delivery date printed
- Special handling labels (fragile, hazmat) if needed

**Label Formats**:
- `PDF` - Standard 4×6 label
- `PNG` - Image format
- `ZPL` - Zebra thermal printer
- `EPL` - Eltron thermal printer

**Key Metrics**:
- Label generation success rate (target: >99.9%)
- Label generation time
- Label reprints (rate)

**API Endpoints**:
- `GET /api/v1/shipments/{shipmentId}/label` - Retrieve label
- `POST /api/v1/shipments/{shipmentId}/label/reprint` - Reprint label

**Related Services**: Warehouse Operations (label printing)

---

#### L3.4.2: Tracking Number Assignment
**Description**: Assign and manage carrier tracking numbers for shipment visibility.

**Technical Implementation**:
- Tracking numbers from carrier API
- Tracking number format validation
- Unique tracking per package
- Master tracking for multi-package shipments

**Business Rules**:
- Tracking number assigned at label generation
- Tracking number format varies by carrier
- Barcode generated from tracking number
- Tracking number never reused
- Multi-package shipments have master tracking

**Tracking Number Formats**:
- **FedEx**: 12 or 15 digits
- **UPS**: 18 characters starting with "1Z"
- **USPS**: 20-22 digits

**Key Metrics**:
- Tracking number issuance rate
- Duplicate tracking numbers (should be 0)
- Tracking number validation errors

**Related Services**: Order Management (tracking info to customer)

---

#### L3.4.3: Customs Documentation (International)
**Description**: Generate customs forms and documentation for international shipments.

**Technical Implementation**:
- Commercial invoice generation
- Harmonized tariff code support
- Country-specific customs requirements
- Electronic customs submission (if supported)

**Business Rules**:
- Required for all international shipments
- Accurate product descriptions required
- Declared value must match invoice
- Harmonized codes must be accurate
- Restricted items flagged
- Export compliance verification

**Customs Documents**:
- Commercial Invoice
- Packing List
- Certificate of Origin (if needed)
- NAFTA Certificate (if applicable)

**Key Metrics**:
- International shipment percentage
- Customs documentation accuracy
- Customs delay incidents

**Related Services**: Product Catalog (HS codes, product descriptions)

---

## L2: Shipment Tracking & Visibility

### L2.1: Description
Provide real-time tracking and visibility into shipment status and location.

### L2.2: Business Value
- Customer self-service for shipment tracking
- Proactive exception notification
- Delivery confirmation
- Support for customer service inquiries

### L2.3: L3 Capabilities

#### L3.5.1: Real-Time Tracking Updates
**Description**: Poll carrier tracking APIs to retrieve and update shipment status.

**Technical Implementation**:
- Scheduled background jobs for tracking updates
- Polling frequency based on shipment status
- Incremental tracking event storage
- Event-driven notifications on status changes

**Business Rules**:
- Track active shipments every hour (configurable)
- Track shipments out-for-delivery every 15 minutes
- Stop tracking after delivery confirmation
- Retry failed tracking requests
- Alert on tracking API failures

**Tracking Update Frequency**:
- `IN_TRANSIT`: Every 1 hour
- `OUT_FOR_DELIVERY`: Every 15 minutes
- `EXCEPTION`: Every 30 minutes
- `DELIVERED`: Stop tracking

**Key Metrics**:
- Tracking update success rate
- Average tracking data freshness
- Tracking API response time

**Related Services**: None (carrier APIs)

---

#### L3.5.2: Tracking Event History
**Description**: Maintain complete history of tracking events for each shipment.

**Technical Implementation**:
- Append-only tracking event list
- Event deduplication (idempotency)
- Chronological event ordering
- Location and timestamp captured

**Tracking Event Types**:
- `PICKED_UP` - Carrier picked up package
- `DEPARTED_FACILITY` - Left carrier facility
- `ARRIVED_FACILITY` - Arrived at carrier facility
- `IN_TRANSIT` - In transit to destination
- `OUT_FOR_DELIVERY` - On delivery vehicle
- `DELIVERED` - Delivered to recipient
- `DELIVERY_ATTEMPT_FAILED` - Delivery attempted but failed
- `EXCEPTION` - Exception occurred (delay, damage, etc.)

**Event Data**:
```java
class TrackingEvent {
  private String eventType;
  private LocalDateTime timestamp;
  private String location;
  private String description;
  private String carrier;
}
```

**Key Metrics**:
- Average tracking events per shipment
- Event processing latency
- Duplicate event rate (should be 0)

**Related Services**: Customer portal (tracking display)

---

#### L3.5.3: Tracking Number Lookup
**Description**: Provide API for tracking shipments by tracking number.

**Technical Implementation**:
- RESTful API endpoint for tracking lookup
- Support for both shipment ID and tracking number
- Return current status and event history
- Estimated delivery date calculation

**Business Rules**:
- Support lookup by shipment ID or tracking number
- Include complete event history
- Show estimated delivery if available
- Handle multiple packages (multi-package shipments)

**Key Metrics**:
- Tracking query volume
- Tracking query response time
- Not found rate

**API Endpoints**:
- `GET /api/v1/shipments/{shipmentId}/tracking` - Track by shipment ID
- `GET /api/v1/tracking/{trackingNumber}` - Track by tracking number

**Response Example**:
```json
{
  "shipmentId": "SHIP-12345",
  "trackingNumber": "123456789012",
  "status": "IN_TRANSIT",
  "estimatedDelivery": "2025-10-22",
  "events": [
    {
      "type": "PICKED_UP",
      "timestamp": "2025-10-18T14:00:00Z",
      "location": "Memphis, TN",
      "description": "Package picked up"
    },
    {
      "type": "DEPARTED_FACILITY",
      "timestamp": "2025-10-18T18:00:00Z",
      "location": "Memphis, TN",
      "description": "Departed FedEx facility"
    }
  ]
}
```

**Related Services**: Customer notifications (tracking updates)

---

#### L3.5.4: Delivery Confirmation
**Description**: Capture and store proof of delivery information.

**Technical Implementation**:
- Delivery confirmation from carrier tracking
- Signature capture (if applicable)
- Photo proof of delivery (if available)
- Delivery location details

**Business Rules**:
- Capture delivery timestamp
- Record recipient name (if signed)
- Store delivery location (if different from address)
- Photo stored securely (retention policy)
- Signature image stored (retention policy)

**Delivery Confirmation Data**:
- Delivery timestamp
- Recipient name (or "Left at door")
- Delivery location description
- Signature (if applicable)
- Photo (if available)
- Driver notes

**Key Metrics**:
- Delivery confirmation rate
- Signature capture rate
- Photo delivery rate

**Related Services**: Order Management (delivery confirmation)

---

## L2: Load Management & Carrier Tendering

### L2.1: Description
Group packages into loads for carrier pickup and tendering.

### L2.2: Business Value
- Efficient carrier pickups
- Support for less-than-truckload (LTL) shipping
- Parcel carrier manifesting
- End-of-day close-out

### L2.3: L3 Capabilities

#### L3.6.1: Load Creation
**Description**: Create loads grouping packages for carrier pickup.

**Technical Implementation**:
- `Load` aggregate manages grouped packages
- `CreateLoadCommand` for load creation
- Automatic or manual load creation
- Carrier-specific load requirements

**Business Rules**:
- Loads contain packages for single carrier
- Packages added before carrier pickup
- Loads closed (manifested) before pickup
- Load weight and package count tracked

**Domain Model**:
```java
@AggregateRoot
class Load {
  private String loadId;
  private Carrier carrier;
  private List<String> shipmentIds;
  private LoadStatus status; // OPEN, CLOSED, TENDERED, PICKED_UP
  private LocalDateTime closedAt;
  private LocalDateTime pickupTime;
  private String manifestDocument;
}
```

**Key Metrics**:
- Loads created per day
- Average packages per load
- Load close time (before pickup)

**API Endpoints**:
- `POST /api/v1/loads` - Create load

**Related Services**: Warehouse Operations (outbound staging)

---

#### L3.6.2: Load Tendering & Manifesting
**Description**: Tender loads to carriers and generate manifest documents.

**Technical Implementation**:
- Carrier API integration for manifesting
- Manifest document generation (PDF)
- Electronic tender submission
- Pickup scheduling

**Business Rules**:
- Loads must be closed before tendering
- All labels generated before manifest
- Manifest includes all package details
- Pickup time scheduled
- Cannot modify load after manifest

**Key Metrics**:
- Manifest generation success rate
- Time from load close to manifest
- Pickup scheduling success rate

**Domain Events**:
- `LoadTenderedEvent`
- `LoadPickedUpEvent`

**Related Services**: None (carrier APIs)

---

## L2: Exception Handling & Returns

### L2.1: Description
Handle delivery exceptions, failed deliveries, and return shipments.

### L2.2: Business Value
- Proactive exception management
- Customer notification for delays
- Return processing automation
- Cost recovery for carrier failures

### L2.3: L3 Capabilities

#### L3.7.1: Delivery Exception Management
**Description**: Detect, track, and resolve delivery exceptions.

**Technical Implementation**:
- Exception detection from tracking events
- Automated alerting on exceptions
- Exception reason code capture
- Resolution workflow

**Exception Types**:
- `WEATHER_DELAY` - Weather-related delay
- `ADDRESS_ISSUE` - Invalid or incomplete address
- `RECIPIENT_UNAVAILABLE` - Recipient not available
- `DAMAGED_PACKAGE` - Package damaged in transit
- `LOST_PACKAGE` - Package lost in carrier network
- `CUSTOMS_DELAY` - Customs clearance delay (international)

**Business Rules**:
- Exceptions trigger notifications
- Automatic resolution attempted (address corrections)
- Manual intervention for unresolved exceptions
- Customer service alerted
- Claim filed for lost/damaged packages

**Key Metrics**:
- Exception rate by carrier
- Exception resolution time
- Exception reasons distribution
- Cost impact of exceptions

**Domain Events**:
- `ShipmentExceptionEvent`

**Related Services**: Customer service (exception handling)

---

## L2: Monitoring & Observability

### L2.1: Description
Comprehensive monitoring, metrics, and observability for shipment operations.

### L2.2: Business Value
- Proactive issue detection
- Carrier performance monitoring
- Cost analysis and optimization
- SLA compliance tracking

### L2.3: L3 Capabilities

#### L3.8.1: Shipment Metrics Collection
**Description**: Collect and expose comprehensive metrics for shipment operations.

**Technical Implementation**:
- Prometheus metrics integration
- Custom business metrics
- Grafana dashboards
- Metric-based alerting

**Key Metrics Exposed**:
- `shipments.created.total` - Shipments created
- `shipments.status{status}` - Shipments by status
- `shipments.carrier{carrier}` - Volume by carrier
- `shipments.delivery.ontime.rate` - On-time delivery %
- `shipments.exception.rate` - Exception rate
- `shipments.cost.total` - Total shipping costs
- `shipments.tracking.update.lag` - Tracking data freshness

**Related Services**: Infrastructure (Prometheus, Grafana)

---

## Summary

The Shipment & Transportation Service provides comprehensive shipment management through:

### Key Strengths
- **Multi-Carrier Support**: Extensible adapter architecture
- **Cost Optimization**: Rate shopping and carrier selection
- **Real-Time Tracking**: Automated tracking updates
- **Scalability**: Event-driven integration
- **Reliability**: Retry logic and failover capabilities

### Business Impact
- **Carrier Options**: Currently FedEx, extensible for UPS, USPS, DHL
- **Cost Savings**: 10-20% through carrier optimization
- **On-Time Delivery**: >95% on-time rate
- **Tracking Updates**: Hourly tracking for active shipments
- **Label Generation**: <2 seconds average

### Integration Points
- **Upstream**: Order Management, Warehouse Operations (shipment requests)
- **Downstream**: Carriers (FedEx, UPS, etc.)
- **Events**: Publishes shipment lifecycle events

### Technology Highlights
- Hexagonal architecture with adapter pattern
- Event-driven integration via Kafka
- Secure credential management
- Background job scheduling for tracking updates
- Comprehensive observability
