# WES Orchestration Engine - Class Diagrams

## Workflow Domain Model

```mermaid
classDiagram
    class WorkflowDefinition {
        <<Aggregate Root>>
        -String workflowId
        -String name
        -Version version
        -WorkflowType type
        -List~WorkflowStep~ steps
        -List~Transition~ transitions
        -List~Variable~ variables
        -List~Trigger~ triggers
        -WorkflowStatus status
        -ValidationRules validationRules
        +addStep(step) void
        +connectSteps(from, to, condition) void
        +validate() ValidationResult
        +activate() void
        +deprecate() void
        +clone() WorkflowDefinition
    }

    class WorkflowInstance {
        <<Aggregate Root>>
        -String instanceId
        -String definitionId
        -String correlationId
        -InstanceStatus status
        -Map~String, Object~ context
        -List~StepExecution~ executions
        -CurrentStep currentStep
        -DateTime startTime
        -DateTime endTime
        -List~WorkflowEvent~ history
        +start(input) void
        +executeStep(stepId) StepResult
        +transition(toStep) void
        +pause() void
        +resume() void
        +cancel(reason) void
        +complete() void
        +retry(stepId) void
        +compensate() void
    }

    class WorkflowStep {
        <<Entity>>
        -String stepId
        -String name
        -StepType type
        -ServiceCall serviceCall
        -RetryPolicy retryPolicy
        -TimeoutPolicy timeout
        -CompensationHandler compensation
        -List~Condition~ preconditions
        -List~Condition~ postconditions
        +execute(context) StepResult
        +compensate(context) void
        +validate(context) boolean
    }

    class StepExecution {
        <<Entity>>
        -String executionId
        -String stepId
        -ExecutionStatus status
        -DateTime startTime
        -DateTime endTime
        -int attemptNumber
        -Map~String, Object~ input
        -Map~String, Object~ output
        -Error error
        +start() void
        +complete(output) void
        +fail(error) void
        +retry() void
    }

    class Transition {
        <<Value Object>>
        -String fromStepId
        -String toStepId
        -TransitionType type
        -Condition condition
        -Priority priority
        +evaluate(context) boolean
        +isDefault() boolean
    }

    WorkflowDefinition "1" --> "*" WorkflowStep : contains
    WorkflowDefinition "1" --> "*" Transition : defines
    WorkflowInstance "1" --> "*" StepExecution : tracks
    WorkflowInstance "1" --> "1" WorkflowDefinition : implements
```

## Orchestration Engine

```mermaid
classDiagram
    class OrchestrationEngine {
        <<Domain Service>>
        -WorkflowExecutor executor
        -StateManager stateManager
        -EventDispatcher dispatcher
        -ServiceRegistry registry
        +startWorkflow(definitionId, input) InstanceId
        +executeStep(instanceId, stepId) StepResult
        +handleEvent(event) void
        +monitorInstances() List~InstanceStatus~
        -processTransitions(instance) void
        -evaluateConditions(instance) void
    }

    class WorkflowExecutor {
        <<Service>>
        -ExecutorService threadPool
        -ServiceInvoker invoker
        -RetryManager retryManager
        +execute(step, context) StepResult
        +executeAsync(step, context) Future~StepResult~
        +executeParallel(steps, context) List~StepResult~
        -invokeService(call, context) Response
        -handleRetry(step, error) StepResult
    }

    class StateManager {
        <<Service>>
        -StateStore stateStore
        -SnapshotManager snapshots
        +saveState(instanceId, state) void
        +loadState(instanceId) WorkflowState
        +createSnapshot(instanceId) Snapshot
        +restoreFromSnapshot(snapshotId) void
        -persistState(state) void
        -hydrateState(data) WorkflowState
    }

    class ServiceInvoker {
        <<Service>>
        -ServiceRegistry registry
        -CircuitBreaker circuitBreaker
        -LoadBalancer loadBalancer
        +invoke(serviceCall, input) Response
        +invokeAsync(serviceCall, input) CompletableFuture~Response~
        -selectEndpoint(service) Endpoint
        -handleFailure(service, error) void
    }

    class EventDispatcher {
        <<Service>>
        -EventBus eventBus
        -EventStore eventStore
        +dispatch(event) void
        +subscribe(eventType, handler) void
        +replay(fromTimestamp) void
        -routeEvent(event) void
    }

    OrchestrationEngine --> WorkflowExecutor : uses
    OrchestrationEngine --> StateManager : manages
    OrchestrationEngine --> ServiceInvoker : delegates
    OrchestrationEngine --> EventDispatcher : publishes
```

## Saga Pattern Implementation

```mermaid
classDiagram
    class SagaDefinition {
        <<Entity>>
        -String sagaId
        -String name
        -List~SagaStep~ steps
        -CompensationStrategy strategy
        +addStep(step, compensation) void
        +validate() boolean
    }

    class SagaInstance {
        <<Aggregate Root>>
        -String instanceId
        -String sagaDefinitionId
        -SagaStatus status
        -List~SagaStepExecution~ executions
        -int currentStepIndex
        -Map~String, Object~ sagaContext
        +execute() void
        +compensate() void
        +retry() void
        +markStepComplete(stepId) void
        +markStepFailed(stepId, error) void
    }

    class SagaStep {
        <<Entity>>
        -String stepId
        -String serviceName
        -String operation
        -CompensationAction compensation
        -boolean isPivot
        +execute(context) StepResult
        +compensate(context) void
    }

    class CompensationAction {
        <<Value Object>>
        -String serviceName
        -String operation
        -Map~String, Object~ parameters
        +execute(context) void
    }

    class SagaCoordinator {
        <<Domain Service>>
        -SagaRepository repository
        -MessageBus messageBus
        +startSaga(sagaId, input) SagaInstance
        +handleStepResult(instanceId, result) void
        +compensateSaga(instanceId) void
        -executeNextStep(instance) void
        -startCompensation(instance) void
    }

    SagaDefinition "1" --> "*" SagaStep : contains
    SagaInstance "1" --> "1" SagaDefinition : implements
    SagaStep "1" --> "1" CompensationAction : has
    SagaCoordinator --> SagaInstance : manages
```

## Service Registry and Discovery

```mermaid
classDiagram
    class ServiceRegistry {
        <<Service>>
        -Map~String, ServiceDefinition~ services
        -HealthChecker healthChecker
        +register(service) void
        +deregister(serviceId) void
        +discover(serviceName) List~ServiceInstance~
        +getHealthyInstances(serviceName) List~ServiceInstance~
        -checkHealth(instance) HealthStatus
    }

    class ServiceDefinition {
        <<Entity>>
        -String serviceId
        -String serviceName
        -String version
        -List~Endpoint~ endpoints
        -List~Operation~ operations
        -ServiceMetadata metadata
        +addEndpoint(endpoint) void
        +addOperation(operation) void
        +isCompatible(version) boolean
    }

    class ServiceInstance {
        <<Entity>>
        -String instanceId
        -String serviceId
        -String host
        -int port
        -InstanceStatus status
        -DateTime registeredAt
        -DateTime lastHeartbeat
        -LoadMetrics loadMetrics
        +updateStatus(status) void
        +recordHeartbeat() void
        +isHealthy() boolean
    }

    class LoadBalancer {
        <<Service>>
        -BalancingStrategy strategy
        -ServiceRegistry registry
        +selectInstance(serviceName) ServiceInstance
        +updateLoad(instanceId, metrics) void
        -applyStrategy(instances) ServiceInstance
    }

    ServiceRegistry "1" --> "*" ServiceDefinition : contains
    ServiceDefinition "1" --> "*" ServiceInstance : has
    LoadBalancer --> ServiceRegistry : queries
```

## Monitoring and Observability

```mermaid
classDiagram
    class WorkflowMonitor {
        <<Service>>
        -MetricsCollector metrics
        -TracingService tracing
        -AlertManager alerts
        +monitorInstance(instanceId) InstanceMetrics
        +trackPerformance(workflowId) PerformanceMetrics
        +detectAnomalies() List~Anomaly~
        +generateDashboard() Dashboard
    }

    class InstanceMetrics {
        <<Entity>>
        -String instanceId
        -Duration executionTime
        -int stepsCompleted
        -int stepsTotal
        -int retryCount
        -List~StepMetrics~ stepMetrics
        -ResourceUsage resources
        +calculateProgress() Percentage
        +estimateCompletion() DateTime
        +identifyBottlenecks() List~Bottleneck~
    }

    class TracingContext {
        <<Value Object>>
        -String traceId
        -String spanId
        -String parentSpanId
        -Map~String, String~ baggage
        +createChildSpan() TracingContext
        +addBaggage(key, value) void
    }

    class AlertRule {
        <<Entity>>
        -String ruleId
        -String name
        -AlertCondition condition
        -AlertSeverity severity
        -List~String~ recipients
        -AlertAction action
        +evaluate(metrics) boolean
        +trigger() void
    }

    class PerformanceAnalyzer {
        <<Service>>
        -HistoricalData history
        -MLPredictor predictor
        +analyzePerformance(workflowId) Analysis
        +predictDuration(workflow, input) Duration
        +recommendOptimizations() List~Optimization~
        +compareVersions(v1, v2) Comparison
    }

    WorkflowMonitor --> InstanceMetrics : collects
    WorkflowMonitor --> TracingContext : uses
    WorkflowMonitor --> AlertRule : evaluates
    WorkflowMonitor --> PerformanceAnalyzer : uses
```

## Error Handling and Recovery

```mermaid
classDiagram
    class ErrorHandler {
        <<Service>>
        -ErrorClassifier classifier
        -RecoveryStrategy strategy
        -CompensationManager compensator
        +handleError(error, context) ErrorResult
        +classifyError(error) ErrorType
        +selectRecovery(error) RecoveryAction
        +initiateCompensation(instanceId) void
    }

    class RetryPolicy {
        <<Value Object>>
        -int maxAttempts
        -Duration initialDelay
        -BackoffStrategy backoff
        -List~String~ retryableErrors
        +shouldRetry(error, attempt) boolean
        +calculateDelay(attempt) Duration
    }

    class CircuitBreaker {
        <<Service>>
        -CircuitState state
        -int failureThreshold
        -Duration timeout
        -int successThreshold
        +call(supplier) Result
        +recordSuccess() void
        +recordFailure() void
        -trip() void
        -reset() void
    }

    class CompensationManager {
        <<Service>>
        -CompensationLog log
        -CompensationExecutor executor
        +compensate(instanceId) CompensationResult
        +compensateStep(stepId) void
        +getCompensationChain(instanceId) List~CompensationAction~
        -executeCompensation(action) void
    }

    ErrorHandler --> RetryPolicy : applies
    ErrorHandler --> CircuitBreaker : uses
    ErrorHandler --> CompensationManager : delegates
```

## Domain Events

```mermaid
classDiagram
    class WorkflowEvent {
        <<Abstract Event>>
        -String eventId
        -String workflowId
        -String instanceId
        -DateTime occurredAt
        +getEventType() String
    }

    class WorkflowStartedEvent {
        <<Event>>
        -Map~String, Object~ input
        -String triggeredBy
        +getEventType() String
    }

    class StepCompletedEvent {
        <<Event>>
        -String stepId
        -Map~String, Object~ output
        -Duration duration
        +getEventType() String
    }

    class WorkflowCompletedEvent {
        <<Event>>
        -Map~String, Object~ output
        -Duration totalDuration
        -CompletionStatus status
        +getEventType() String
    }

    class WorkflowFailedEvent {
        <<Event>>
        -String failedStepId
        -Error error
        -boolean compensated
        +getEventType() String
    }

    class CompensationStartedEvent {
        <<Event>>
        -String reason
        -List~String~ stepsToCompensate
        +getEventType() String
    }

    WorkflowEvent <|-- WorkflowStartedEvent
    WorkflowEvent <|-- StepCompletedEvent
    WorkflowEvent <|-- WorkflowCompletedEvent
    WorkflowEvent <|-- WorkflowFailedEvent
    WorkflowEvent <|-- CompensationStartedEvent
```