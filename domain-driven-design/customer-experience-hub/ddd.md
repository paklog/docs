# Customer Experience Hub - Domain-Driven Design

## Bounded Context: Customer Engagement & Self-Service

The Customer Experience Hub acts as a Backend-for-Frontend (BFF) that aggregates data from other services to provide a unified, customer-centric view of the fulfillment process. It manages customer preferences, notifications, and self-service capabilities.

## Domain Model

### Aggregates

#### CustomerProfile (Aggregate Root)
**Purpose**: Manages a customer's preferences and communication settings.

**Properties**:
```java
public class CustomerProfile {
    private CustomerId customerId;
    private DeliveryPreferences deliveryPreferences;
    private CommunicationPreferences communicationPreferences;
    private List<SavedAddress> addressBook;
}
```

#### TrackedOrder (View Model Aggregate)
**Purpose**: Provides a customer-facing, simplified view of an order's status and history. This is a projection built from events from other services.

**Properties**:
```java
public class TrackedOrder {
    private OrderId orderId;
    private DisplayableOrderStatus status;
    private EstimatedDeliveryTime eta;
    private List<TrackingMilestone> history;
    private TrackingNumber trackingNumber;
}
```

### Value Objects
- **DeliveryPreferences**: Preferred time windows, safe drop locations.
- **CommunicationPreferences**: Notification channels (SMS, Email, Push) and frequency.
- **DisplayableOrderStatus**: Simplified status for customers (e.g., 'Processing', 'Shipped', 'Out for Delivery').
- **TrackingMilestone**: A single event in the order's journey.

### Domain Services
- **NotificationService**: Manages sending notifications through various channels.
- **OrderTrackingService**: Aggregates tracking information from multiple sources.
- **PreferenceManagementService**: Handles updates to customer preferences.

### Domain Events

#### Events Published
- `CustomerPreferencesUpdated`
- `NotificationSent`
- `DeliveryStatusViewed`

#### Events Consumed
- `OrderShipped` (from Shipment Transportation)
- `ShipmentInTransit` (from Shipment Transportation)
- `ShipmentDelivered` (from Shipment Transportation)
- `ReturnInitiated` (from Returns Management)

### Integration
- **Upstream**: Consumes events from Order Management, Shipment Transportation, and Returns Management.
- **Downstream**: Pushes notifications to customers via external gateways (Twilio, SendGrid, etc.).
- **Pattern**: Acts as a BFF, providing tailored data views for frontend applications (web portal, mobile app).

## Business Rules
1.  **Notification Opt-in**: Customers must explicitly opt-in for notifications on each channel.
2.  **Preference Caching**: Customer preferences are cached for low-latency access.
3.  **Status Simplification**: Internal fulfillment statuses are mapped to a smaller, customer-friendly set of statuses.
4.  **Proactive Alerts**: Send notifications for potential delays before they happen, based on ETA predictions.
