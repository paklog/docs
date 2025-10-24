# Cross-Docking Operations - Domain-Driven Design

## Bounded Context: Flow-Through & Consolidation

## Domain Model

### Aggregates

#### CrossDockOperation (Aggregate Root)
**Purpose**: Manages direct transfer without storage

**Properties**:
```java
public class CrossDockOperation {
    private OperationId operationId;
    private TransferType type; // DIRECT, CONSOLIDATED
    private FlowStatus status;
    private List<InboundTrailer> inbound;
    private List<OutboundTrailer> outbound;
    private TransferWindow timeWindow;
    private ConsolidationPlan consolidation;
}
```

#### TransferOrder (Entity)
**Purpose**: Individual transfer request

**Properties**:
```java
public class TransferOrder {
    private TransferId transferId;
    private SourceLocation source;
    private DestinationLocation destination;
    private List<TransferItem> items;
    private TransferPriority priority;
}
```

### Value Objects
- TransferType (DIRECT, CONSOLIDATED, DECONSOLIDATED)
- FlowStatus (PLANNED, IN_PROGRESS, COMPLETED)
- TransferWindow (maxDwell: 2 hours)
- ConsolidationStrategy (PRODUCT, DESTINATION, TIME)

### Domain Services
- FlowOptimizationService
- ConsolidationService
- TransferCoordinationService

### Domain Events
- CrossDockPlanned
- TransferInitiated
- ConsolidationCompleted
- DirectShipmentCreated

### Integration
- **Specialized Operation**: Within Warehouse Operations
- **Upstream**: Yard Management

## Business Rules
1. **Dwell Time**: Max 2 hours floor time
2. **Direct Transfer**: No putaway required
3. **Consolidation**: Multiple to single
4. **Deconsolidation**: Single to multiple
5. **Priority**: Time-sensitive first