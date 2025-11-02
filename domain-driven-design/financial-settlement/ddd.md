# Financial Settlement Service - Domain-Driven Design

## Service Overview

The Financial Settlement Service manages billing reconciliation, cost allocation, invoicing, payment processing, and financial reporting for warehouse operations, including 3PL billing and client chargebacks.

**Bounded Context**: Financial Settlement
**Architecture Pattern**: Hexagonal Architecture with DDD
**Technology Stack**: Spring Boot, PostgreSQL, Apache Kafka
**Integration Pattern**: Event-Driven Architecture with Saga Pattern

## Domain Model

### Core Aggregates

#### 1. BillingAccount Aggregate
**Purpose**: Manages client billing accounts and contracts

**Root Entity**: BillingAccount
- `AccountId` (Value Object)
- `ClientId` (Value Object)
- `AccountType` (Enum: CONTRACT, ADHOC, SUBSCRIPTION)
- `BillingCycle` (Enum: DAILY, WEEKLY, MONTHLY, QUARTERLY)
- `PaymentTerms` (Value Object)
- `CreditLimit` (Money)
- `CurrentBalance` (Money)
- `Status` (Enum: ACTIVE, SUSPENDED, CLOSED)

**Entities**:
- `Contract`: Service agreements and rate cards
- `RateCard`: Pricing for different services
- `CreditHistory`: Credit limit changes

**Value Objects**:
- `AccountId`: Unique account identifier
- `ClientId`: Reference to client
- `PaymentTerms`: NET30, NET60, etc.
- `Money`: Amount with currency
- `BillingAddress`: Billing contact information

**Domain Events**:
- `BillingAccountCreated`
- `ContractActivated`
- `CreditLimitUpdated`
- `AccountSuspended`

#### 2. Invoice Aggregate
**Purpose**: Manages invoice generation and lifecycle

**Root Entity**: Invoice
- `InvoiceId` (Value Object)
- `AccountId` (Reference)
- `InvoiceNumber` (Value Object)
- `InvoiceDate` (Value Object)
- `DueDate` (Value Object)
- `TotalAmount` (Money)
- `Status` (Enum: DRAFT, ISSUED, SENT, PAID, OVERDUE, CANCELLED)
- `PaymentStatus` (Enum: PENDING, PARTIAL, PAID)

**Entities**:
- `InvoiceLineItem`: Individual charges
- `Adjustment`: Credits, debits, discounts
- `TaxCalculation`: Tax breakdown

**Value Objects**:
- `InvoiceId`: Unique invoice identifier
- `InvoiceNumber`: Business invoice number
- `LineItemDetail`: Service description and charges
- `TaxInfo`: Tax rates and amounts

**Domain Events**:
- `InvoiceGenerated`
- `InvoiceSent`
- `PaymentReceived`
- `InvoiceOverdue`
- `InvoiceCancelled`

#### 3. ChargeTransaction Aggregate
**Purpose**: Tracks individual billable transactions

**Root Entity**: ChargeTransaction
- `TransactionId` (Value Object)
- `AccountId` (Reference)
- `TransactionType` (Enum: STORAGE, PICKING, PACKING, SHIPPING, VALUE_ADDED)
- `ServiceDate` (Value Object)
- `Quantity` (Value Object)
- `UnitPrice` (Money)
- `TotalAmount` (Money)
- `Status` (Enum: PENDING, APPROVED, INVOICED, DISPUTED)

**Entities**:
- `ChargeDetail`: Detailed breakdown of charges
- `ActivityReference`: Link to warehouse activity
- `DisputeRecord`: Dispute information if contested

**Value Objects**:
- `TransactionId`: Unique transaction ID
- `ServiceCode`: Service type code
- `Quantity`: Units with UOM
- `ChargeRate`: Rate calculation details

**Domain Events**:
- `ChargeTransactionCreated`
- `ChargeApproved`
- `ChargeDisputed`
- `ChargeInvoiced`

#### 4. Payment Aggregate
**Purpose**: Manages payment processing and reconciliation

**Root Entity**: Payment
- `PaymentId` (Value Object)
- `AccountId` (Reference)
- `PaymentMethod` (Enum: BANK_TRANSFER, CHECK, CREDIT_CARD, ACH)
- `Amount` (Money)
- `PaymentDate` (Value Object)
- `Status` (Enum: PENDING, PROCESSED, FAILED, REVERSED)
- `Reference` (Value Object)

**Entities**:
- `PaymentAllocation`: Invoice allocations
- `PaymentDetail`: Bank/processor details
- `Reconciliation`: Bank reconciliation records

**Value Objects**:
- `PaymentId`: Unique payment identifier
- `PaymentReference`: External reference number
- `BankDetails`: Banking information
- `ProcessorResponse`: Payment processor details

**Domain Events**:
- `PaymentReceived`
- `PaymentProcessed`
- `PaymentAllocated`
- `PaymentFailed`
- `PaymentReversed`

### Domain Services

#### BillingCalculationService
- Calculates charges based on activities
- Applies rate cards and contracts
- Handles complex pricing rules

#### InvoiceGenerationService
- Generates periodic invoices
- Consolidates charges
- Applies adjustments and taxes

#### PaymentAllocationService
- Allocates payments to invoices
- Handles partial payments
- Manages payment priorities

#### SettlementReconciliationService
- Reconciles payments with bank
- Matches transactions
- Handles discrepancies

### Repository Interfaces

```java
interface BillingAccountRepository {
    BillingAccount findById(AccountId id);
    List<BillingAccount> findByStatus(AccountStatus status);
    void save(BillingAccount account);
}

interface InvoiceRepository {
    Invoice findById(InvoiceId id);
    List<Invoice> findByAccount(AccountId accountId);
    List<Invoice> findOverdue();
    void save(Invoice invoice);
}

interface ChargeTransactionRepository {
    ChargeTransaction findById(TransactionId id);
    List<ChargeTransaction> findPendingByAccount(AccountId accountId);
    List<ChargeTransaction> findByDateRange(DateRange range);
    void save(ChargeTransaction transaction);
}

interface PaymentRepository {
    Payment findById(PaymentId id);
    List<Payment> findByAccount(AccountId accountId);
    List<Payment> findUnallocated();
    void save(Payment payment);
}
```

## Integration Patterns

### Inbound Adapters
- REST API for billing management
- Kafka consumers for warehouse activities
- Scheduled jobs for invoice generation
- Webhook receivers for payment notifications

### Outbound Adapters
- Kafka producers for financial events
- Email service for invoice delivery
- Payment gateway integrations
- ERP system connectors

### Anti-Corruption Layer
- Translation of warehouse activities to charges
- Mapping of external payment formats
- Currency conversion services
- Tax calculation service integration

## Business Capabilities

### Billing Management
- Contract and rate card management
- Dynamic pricing rules
- Volume discounts and tiered pricing
- Minimum billing guarantees

### Invoice Generation
- Automated periodic invoicing
- Consolidated billing
- Pro-forma invoices
- Credit note generation

### Payment Processing
- Multiple payment methods
- Payment allocation
- Partial payment handling
- Payment reconciliation

### Financial Reporting
- Revenue recognition
- Accounts receivable aging
- Billing analytics
- Client profitability analysis

### Dispute Management
- Charge dispute workflow
- Resolution tracking
- Credit/debit adjustments
- Audit trail maintenance

## Event Flow Examples

### Monthly Invoice Generation Flow
1. `BillingCycleTriggered` (from scheduler)
2. `ChargesConsolidated` (gather monthly charges)
3. `InvoiceGenerated` (create invoice)
4. `TaxCalculated` (apply taxes)
5. `InvoiceSent` (email to client)
6. `PaymentTermsSet` (due date established)

### Payment Processing Flow
1. `PaymentReceived` (from payment gateway)
2. `PaymentValidated` (verify details)
3. `PaymentProcessed` (update records)
4. `PaymentAllocated` (apply to invoices)
5. `InvoiceStatusUpdated` (mark as paid)
6. `ReceiptGenerated` (send confirmation)

### Dispute Resolution Flow
1. `ChargeDisputed` (client raises dispute)
2. `DisputeInvestigated` (review charge)
3. `AdjustmentCreated` (if valid)
4. `CreditNoteIssued` (reduce invoice)
5. `DisputeResolved` (close case)

## Implementation Considerations

### Financial Accuracy
- Decimal precision for monetary calculations
- Immutable financial records
- Audit logging for all transactions
- Double-entry bookkeeping patterns

### Performance Optimization
- Batch processing for large invoice runs
- Caching of rate cards
- Async payment processing
- Read models for reporting

### Compliance & Security
- PCI compliance for payment data
- Encryption of sensitive financial data
- Role-based access control
- Regulatory reporting support

### Data Consistency
- Saga pattern for distributed transactions
- Event sourcing for financial audit trail
- Idempotent payment processing
- Reconciliation checkpoints