# Returns Management - Domain-Driven Design

## Bounded Context: Reverse Logistics & RMA Processing

The Returns Management Service handles the complete return merchandise authorization (RMA) lifecycle, including fraud detection, disposition management, quality inspection, and refund processing.

## Domain Model

### Aggregates

#### Return (Aggregate Root)
**Purpose**: Manages the complete lifecycle of a product return

**Properties**:
```java
public class Return {
    private ReturnId returnId;
    private RMANumber rmaNumber;
    private OrderReference originalOrder;
    private ReturnStatus status;
    private ReturnReason reason;
    private List<ReturnItem> items;
    private FraudAssessment fraudAssessment;
    private InspectionResult inspection;
    private DispositionDecision disposition;
    private RefundCalculation refund;
    private CustomerInfo customer;
    private ReturnWindow returnWindow;
    private ReturnMetrics metrics;
}
```

**Invariants**:
- Must be within return window (30 days default)
- Cannot exceed original order value
- High fraud score requires manual review
- Inspection required before disposition
- Refund cannot be processed without approval

**State Transitions**:
```
REQUESTED -> APPROVED -> SHIPPED -> RECEIVED -> INSPECTED -> REFUNDED
    |                                    |           |
    |                                    |           +-> EXCHANGED
    |                                    |           |
    |                                    |           +-> CREDITED
    |                                    |
    |                                    +-> REJECTED -> RETURNED_TO_CUSTOMER
    |
    +-> DENIED -> CLOSED
```

#### ReturnInspection (Entity)
**Purpose**: Quality inspection and assessment of returned items

**Properties**:
```java
public class ReturnInspection {
    private InspectionId inspectionId;
    private ReturnId returnId;
    private InspectionStatus status;
    private List<InspectionItem> items;
    private QualityGrade overallGrade;
    private List<DefectRecord> defects;
    private List<Photo> photos;
    private InspectorInfo inspector;
    private InspectionNotes notes;
}
```

#### DispositionDecision (Entity)
**Purpose**: Determines the final disposition of returned items

**Properties**:
```java
public class DispositionDecision {
    private DispositionId dispositionId;
    private DispositionType type;
    private List<ItemDisposition> itemDispositions;
    private DispositionRules appliedRules;
    private FinancialImpact financialImpact;
    private ApprovalChain approvals;
}
```

### Value Objects

#### RMANumber
```java
public class RMANumber {
    private String value;
    private LocalDateTime generatedAt;

    public static RMANumber generate() {
        return new RMANumber("RMA-" + UUID.randomUUID().toString().substring(0, 8));
    }
}
```

#### FraudAssessment
```java
public class FraudAssessment {
    private FraudScore score;
    private RiskLevel riskLevel;
    private List<FraudIndicator> indicators;
    private FraudCheckResult checkResult;

    public boolean requiresManualReview() {
        return riskLevel == RiskLevel.HIGH || score.getValue() > 0.7;
    }
}

public class FraudScore {
    private BigDecimal value; // 0.0 to 1.0

    public static FraudScore calculate(List<FraudIndicator> indicators) {
        // Multi-factor scoring algorithm
        BigDecimal score = BigDecimal.ZERO;

        for (FraudIndicator indicator : indicators) {
            score = score.add(indicator.getWeight().multiply(indicator.getScore()));
        }

        return new FraudScore(score.min(BigDecimal.ONE));
    }
}
```

#### ReturnReason
```java
public class ReturnReason {
    private ReasonCode code;
    private String description;
    private ReasonCategory category;
    private Boolean customerFault;

    public enum ReasonCode {
        DEFECTIVE,
        DAMAGED_IN_SHIPPING,
        WRONG_ITEM_SENT,
        NOT_AS_DESCRIBED,
        NO_LONGER_NEEDED,
        FOUND_BETTER_PRICE,
        ORDERED_BY_MISTAKE,
        ARRIVED_TOO_LATE,
        QUALITY_ISSUE,
        SIZE_FIT_ISSUE
    }

    public enum ReasonCategory {
        PRODUCT_ISSUE,
        SHIPPING_ISSUE,
        CUSTOMER_REMORSE,
        MERCHANT_ERROR
    }
}
```

#### DispositionType
```java
public enum DispositionType {
    RETURN_TO_STOCK,      // Good condition, resellable
    REFURBISH,           // Minor repairs needed
    LIQUIDATE,           // Sell at discount
    DONATE,              // Donate to charity
    SCRAP,               // Destroy/recycle
    RETURN_TO_VENDOR,    // Vendor return
    QUARANTINE           // Hold for investigation
}
```

#### RefundCalculation
```java
public class RefundCalculation {
    private Money originalAmount;
    private Money refundAmount;
    private Money restockingFee;
    private Money shippingDeduction;
    private RefundMethod method;
    private List<RefundAdjustment> adjustments;

    public Money calculateRefund() {
        Money refund = originalAmount;
        refund = refund.subtract(restockingFee);
        refund = refund.subtract(shippingDeduction);

        for (RefundAdjustment adjustment : adjustments) {
            refund = adjustment.apply(refund);
        }

        return refund;
    }
}
```

#### ReturnWindow
```java
public class ReturnWindow {
    private LocalDate orderDate;
    private Integer windowDays;
    private LocalDate deadline;
    private List<WindowExtension> extensions;

    public boolean isWithinWindow(LocalDate returnDate) {
        return !returnDate.isAfter(deadline);
    }

    public Integer daysRemaining(LocalDate currentDate) {
        return Math.max(0, (int) ChronoUnit.DAYS.between(currentDate, deadline));
    }
}
```

### Domain Services

#### FraudDetectionService
**Purpose**: Analyzes returns for fraudulent patterns

```java
public interface FraudDetectionService {
    FraudAssessment assessReturn(Return return);
    List<FraudIndicator> detectIndicators(Return return, CustomerHistory history);
    RiskLevel calculateRiskLevel(FraudScore score);
    boolean blockHighRiskReturn(Return return);
}
```

**Fraud Detection Algorithm**:
```java
public class FraudDetector {
    public FraudAssessment assess(Return return, CustomerHistory history) {
        List<FraudIndicator> indicators = new ArrayList<>();

        // Return frequency check
        if (history.getReturnRate() > 0.5) {
            indicators.add(new FraudIndicator("HIGH_RETURN_RATE", 0.3, 0.8));
        }

        // Serial returner check
        if (history.getConsecutiveReturns() > 3) {
            indicators.add(new FraudIndicator("SERIAL_RETURNER", 0.2, 0.9));
        }

        // Value threshold check
        if (return.getTotalValue().isGreaterThan(Money.of(1000))) {
            indicators.add(new FraudIndicator("HIGH_VALUE", 0.15, 0.6));
        }

        // New customer check
        if (history.getOrderCount() == 1) {
            indicators.add(new FraudIndicator("NEW_CUSTOMER", 0.1, 0.5));
        }

        // Different address check
        if (!return.getReturnAddress().equals(history.getUsualAddress())) {
            indicators.add(new FraudIndicator("DIFFERENT_ADDRESS", 0.15, 0.7));
        }

        FraudScore score = FraudScore.calculate(indicators);
        RiskLevel risk = calculateRiskLevel(score);

        return new FraudAssessment(score, risk, indicators);
    }
}
```

#### DispositionService
**Purpose**: Determines optimal disposition for returned items

```java
public interface DispositionService {
    DispositionDecision determineDisposition(ReturnInspection inspection);
    DispositionType applyDispositionRules(ReturnItem item, QualityGrade grade);
    FinancialImpact calculateFinancialImpact(DispositionDecision decision);
    void routeToDisposition(ReturnItem item, DispositionType type);
}
```

#### RefundService
**Purpose**: Calculates and processes refunds

```java
public interface RefundService {
    RefundCalculation calculateRefund(Return return);
    Money applyRestockingFee(Return return);
    RefundResult processRefund(Return return, RefundCalculation calculation);
    void initiatePaymentReversal(RefundResult result);
}
```

### Domain Events

#### Return Lifecycle Events
```java
public class ReturnRequested extends DomainEvent {
    private ReturnId returnId;
    private OrderId orderId;
    private CustomerId customerId;
    private ReturnReason reason;
    private List<ReturnItem> items;
}

public class ReturnApproved extends DomainEvent {
    private ReturnId returnId;
    private RMANumber rmaNumber;
    private ReturnLabel shippingLabel;
    private LocalDateTime approvalTime;
}

public class ReturnDenied extends DomainEvent {
    private ReturnId returnId;
    private DenialReason reason;
    private String explanation;
}

public class ReturnReceived extends DomainEvent {
    private ReturnId returnId;
    private LocalDateTime receivedAt;
    private WarehouseLocation location;
    private List<ReceivedItem> items;
}

public class ReturnInspected extends DomainEvent {
    private ReturnId returnId;
    private InspectionResult result;
    private QualityGrade grade;
    private List<DefectRecord> defects;
}

public class RefundProcessed extends DomainEvent {
    private ReturnId returnId;
    private Money refundAmount;
    private RefundMethod method;
    private TransactionId transactionId;
}

public class FraudDetected extends DomainEvent {
    private ReturnId returnId;
    private FraudScore score;
    private RiskLevel riskLevel;
    private List<FraudIndicator> indicators;
}
```

### Repository Interfaces

```java
public interface ReturnRepository {
    Return save(Return return);
    Optional<Return> findById(ReturnId returnId);
    Optional<Return> findByRMANumber(RMANumber rmaNumber);
    List<Return> findByStatus(ReturnStatus status);
    List<Return> findByCustomer(CustomerId customerId);
}

public interface DispositionRepository {
    DispositionDecision save(DispositionDecision disposition);
    Optional<DispositionDecision> findByReturnId(ReturnId returnId);
    List<DispositionDecision> findPendingDispositions();
}
```

## Integration Patterns

### Upstream Dependencies
- **Order Management**: Validates original orders
- **Customer Experience**: Receives return requests

### Downstream Dependencies
- **Inventory**: Updates stock for returned items
- **Financial Settlement**: Processes refunds
- **Quality Compliance**: Inspection requirements

### Events Published
- ReturnRequested
- ReturnApproved
- ReturnDenied
- ReturnReceived
- ReturnInspected
- RefundProcessed
- FraudDetected

### Events Subscribed
- OrderCompleted (from Order Management)
- CustomerProfileUpdated (from Customer Experience)
- InspectionCompleted (from Quality Compliance)

## Business Rules

### Return Eligibility Rules
1. **Time Window**: Within 30 days of delivery
2. **Condition**: Item must be in original condition
3. **Packaging**: Original packaging preferred
4. **Documentation**: Receipt or order number required
5. **Restrictions**: No returns on consumables, customized items

### Fraud Detection Rules
1. **High Risk Threshold**: Fraud score > 0.7
2. **Auto-Deny**: Fraud score > 0.9
3. **Manual Review**: Score 0.5-0.7
4. **Block List**: Deny if customer on block list
5. **Velocity Check**: Max 3 returns per month

### Disposition Rules
1. **Grade A (90-100%)**: Return to stock
2. **Grade B (70-89%)**: Refurbish or discount
3. **Grade C (50-69%)**: Liquidate
4. **Grade D (<50%)**: Scrap or donate
5. **Hazardous**: Special disposal required

### Refund Rules
1. **Full Refund**: If merchant error or defective
2. **Restocking Fee**: 15% for customer remorse
3. **Shipping Deduction**: Original shipping not refunded
4. **Processing Time**: 3-5 business days
5. **Method**: Same as original payment

## Performance Optimization

### Caching Strategy
- Cache customer return history
- Cache disposition rules
- Cache fraud patterns
- Cache refund policies

### Batch Processing
- Batch inspection scheduling
- Batch disposition routing
- Batch refund processing

### Machine Learning Integration
```java
public interface MLFraudDetectionPort {
    FraudPrediction predict(Return return, CustomerFeatures features);
    void trainModel(List<LabeledReturn> trainingData);
    ModelMetrics evaluateModel(List<LabeledReturn> testData);
}
```

## Monitoring & Metrics

### Key Metrics
- Return rate (%)
- Average processing time
- Fraud detection accuracy
- Disposition distribution
- Refund processing time
- Customer satisfaction score

### SLA Targets
- RMA generation: < 30 seconds
- Fraud assessment: < 2 seconds
- Inspection scheduling: Same day
- Refund processing: 3-5 days
- Disposition routing: < 24 hours