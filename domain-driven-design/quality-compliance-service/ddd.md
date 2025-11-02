# Quality Control & Compliance - Domain-Driven Design

## Bounded Context: Inspection, SPC & Regulatory Compliance

## Domain Model

### Aggregates

#### InspectionRecord (Aggregate Root)
**Purpose**: Quality inspection tracking

**Properties**:
```java
public class InspectionRecord {
    private InspectionId inspectionId;
    private InspectionType type;
    private SamplingStrategy sampling;
    private InspectionResult result;
    private List<Defect> defects;
    private List<Photo> documentation;
}
```

#### ComplianceRule (Entity)
**Purpose**: Regulatory and quality requirements

**Properties**:
```java
public class ComplianceRule {
    private RuleId ruleId;
    private ComplianceLevel level;
    private EvaluationCriteria criteria;
    private EnforcementAction action;
}
```

### Value Objects
- InspectionType (RECEIVING, PICKING, PACKING, SHIPPING)
- SamplingStrategy (FULL, AQL_2_5, RANDOM)
- DefectSeverity (CRITICAL, MAJOR, MINOR)
- ComplianceLevel (MANDATORY, RECOMMENDED)

### Domain Services
- StatisticalProcessControlService (SPC with control charts)
- RuleEvaluationService
- DefectAnalysisService
- CAPAManagementService

### Domain Events
- InspectionCompleted
- DefectDetected
- ComplianceViolation
- CAPACreated

### Integration
- **Cross-cutting**: Quality assurance for all services
- **Upstream**: Returns Management

## Business Rules
1. **Critical Defects**: Immediate quarantine
2. **SPC Rules**: Western Electric rules
3. **Sampling**: AQL 2.5% standard
4. **Photo Required**: All defects
5. **CAPA Deadline**: 48 hours