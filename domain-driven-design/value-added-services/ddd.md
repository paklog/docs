# Value-Added Services - Domain-Driven Design

## Bounded Context: Kitting, Customization & Special Handling

## Domain Model

### Aggregates

#### VASOrder (Aggregate Root)
**Purpose**: Manages value-added service requests

**Properties**:
```java
public class VASOrder {
    private VASOrderId orderId;
    private ServiceType serviceType;
    private WorkflowStatus status;
    private List<WorkflowStep> workflow;
    private QualityRequirements quality;
    private BillingInfo billing;
}
```

#### WorkflowStep (Entity)
**Purpose**: Individual step in VAS process

**Properties**:
```java
public class WorkflowStep {
    private StepId stepId;
    private StepType type;
    private StepStatus status;
    private WorkInstructions instructions;
    private QualityCheckpoint checkpoint;
}
```

### Value Objects
- ServiceType (KITTING, LABELING, GIFT_WRAP, ASSEMBLY, CUSTOMIZATION)
- WorkflowStatus (PENDING, IN_PROGRESS, COMPLETED)
- QualityGrade (A: ≥90%, B: ≥80%, C: ≥70%, D: <70%)
- BillingType (TIME_BASED, PER_UNIT)

### Domain Services
- WorkflowOrchestratorService
- KittingService
- CustomizationService
- QualityInspectionService

### Domain Events
- VASOrderCreated
- WorkflowStepCompleted
- QualityCheckPassed
- KittingCompleted
- CustomizationCompleted

### Integration
- **Within**: Warehouse Operations context
- **Downstream**: Pack & Ship

## Business Rules
1. **Max Components**: 20 per kit
2. **Quality Check**: After each major step
3. **SLA**: 12-48 hours by service type
4. **Rework**: Max 2 attempts
5. **Documentation**: Photo required