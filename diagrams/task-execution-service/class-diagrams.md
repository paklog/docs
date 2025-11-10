# Task Execution Service - Class Diagrams

## Domain Model Overview

```mermaid
classDiagram
    class WorkTask {
        <<Aggregate Root>>
        -String taskId
        -TaskType type
        -TaskStatus status
        -Priority priority
        -String assignedTo
        -String assignedToName
        -TaskLocation location
        -TaskContext context
        -List~TaskInstruction~ instructions
        -TaskConstraints constraints
        -DateTime createdAt
        -DateTime assignedAt
        -DateTime startedAt
        -DateTime completedAt
        -Duration estimatedDuration
        -Duration actualDuration
        -TaskMetrics metrics
        +assign(operatorId) void
        +start() void
        +pause(reason) void
        +resume() void
        +complete(result) void
        +cancel(reason) void
        +reassign(newOperatorId) void
        +updateProgress(progress) void
        +addInstruction(instruction) void
        +validate() ValidationResult
        +calculatePriority() Priority
    }

    class TaskInstruction {
        <<Entity>>
        -String instructionId
        -int sequence
        -InstructionType type
        -String description
        -Map~String, Object~ parameters
        -boolean mandatory
        -boolean completed
        -DateTime completedAt
        +execute() void
        +skip(reason) void
        +validate() boolean
    }

    class TaskType {
        <<Enumeration>>
        PICK
        PACK
        PUT_AWAY
        REPLENISHMENT
        CYCLE_COUNT
        MOVE
        LOAD
        UNLOAD
        QUALITY_CHECK
        CONSOLIDATION
    }

    class TaskStatus {
        <<Enumeration>>
        CREATED
        QUEUED
        ASSIGNED
        ACCEPTED
        IN_PROGRESS
        PAUSED
        COMPLETED
        CANCELLED
        FAILED
    }

    class TaskQueue {
        <<Entity>>
        -String queueId
        -QueueType type
        -List~WorkTask~ tasks
        -PriorityStrategy priorityStrategy
        -int maxSize
        -QueueStatus status
        +enqueue(task) void
        +dequeue() WorkTask
        +peek() WorkTask
        +reorder() void
        +clear() void
        +getPosition(taskId) int
    }

    class TaskAssignment {
        <<Value Object>>
        -String assignmentId
        -String taskId
        -String operatorId
        -AssignmentMethod method
        -double score
        -DateTime assignedAt
        -AssignmentReason reason
        +isValid() boolean
        +calculateScore() double
    }

    WorkTask "1" --> "*" TaskInstruction : contains
    WorkTask "1" --> "1" TaskType : has
    WorkTask "1" --> "1" TaskStatus : has
    TaskQueue "1" --> "*" WorkTask : manages
    WorkTask "1" --> "1" TaskAssignment : has
```

## Task Assignment Engine

```mermaid
classDiagram
    class TaskAssignmentEngine {
        <<Domain Service>>
        -AssignmentStrategy strategy
        -OperatorMatcher matcher
        -LoadBalancer loadBalancer
        +assignTask(task) Assignment
        +assignBatch(tasks) List~Assignment~
        +reassignTask(taskId, reason) Assignment
        -findBestOperator(task) Operator
        -calculateAssignmentScore(task, operator) double
        -balanceWorkload(assignments) void
    }

    class AssignmentStrategy {
        <<Strategy Interface>>
        +assign(task, operators) Assignment
    }

    class SkillBasedAssignment {
        <<Strategy>>
        -SkillMatcher matcher
        +assign(task, operators) Assignment
        -matchSkills(task, operator) SkillMatch
        -scoreSkillMatch(match) double
    }

    class ProximityBasedAssignment {
        <<Strategy>>
        -LocationService locationService
        +assign(task, operators) Assignment
        -calculateDistance(operator, task) Distance
        -findNearestOperator(task, operators) Operator
    }

    class LoadBalancedAssignment {
        <<Strategy>>
        -WorkloadCalculator calculator
        +assign(task, operators) Assignment
        -getCurrentWorkload(operator) Workload
        -selectLeastLoaded(operators) Operator
    }

    class RoundRobinAssignment {
        <<Strategy>>
        -Queue~Operator~ operatorQueue
        +assign(task, operators) Assignment
        -getNextOperator() Operator
        -rotateQueue() void
    }

    class OperatorPool {
        <<Entity>>
        -List~Operator~ availableOperators
        -List~Operator~ busyOperators
        -Map~String, OperatorStatus~ statusMap
        +getAvailable(criteria) List~Operator~
        +markBusy(operatorId) void
        +markAvailable(operatorId) void
        +getOperatorLoad(operatorId) int
    }

    TaskAssignmentEngine --> AssignmentStrategy : uses
    AssignmentStrategy <|.. SkillBasedAssignment
    AssignmentStrategy <|.. ProximityBasedAssignment
    AssignmentStrategy <|.. LoadBalancedAssignment
    AssignmentStrategy <|.. RoundRobinAssignment
    TaskAssignmentEngine --> OperatorPool : queries
```

## Task Orchestration

```mermaid
classDiagram
    class TaskOrchestrator {
        <<Domain Service>>
        -TaskFactory factory
        -TaskQueue queue
        -TaskDispatcher dispatcher
        -EventPublisher publisher
        +orchestrateWave(wave) List~WorkTask~
        +generateTasks(source) List~WorkTask~
        +dispatchTasks(tasks) void
        +monitorProgress(tasks) Progress
        -createTasksFromWave(wave) List~WorkTask~
        -prioritizeTasks(tasks) void
        -publishTaskEvents(tasks) void
    }

    class TaskFactory {
        <<Factory>>
        -Map~TaskType, TaskBuilder~ builders
        +createTask(type, context) WorkTask
        +createPickTask(pickList) WorkTask
        +createPackTask(order) WorkTask
        +createPutAwayTask(receipt) WorkTask
        +createCountTask(location) WorkTask
        -selectBuilder(type) TaskBuilder
    }

    class TaskDispatcher {
        <<Service>>
        -AssignmentEngine assignmentEngine
        -NotificationService notifications
        -TaskRepository repository
        +dispatch(task) DispatchResult
        +dispatchBatch(tasks) BatchDispatchResult
        -notifyOperator(assignment) void
        -updateTaskStatus(task) void
    }

    class TaskCoordinator {
        <<Domain Service>>
        -DependencyManager dependencies
        -SequenceManager sequencer
        +coordinateTasks(tasks) CoordinatedPlan
        +resolveDependencies(tasks) DAG
        +sequenceTasks(tasks) List~WorkTask~
        -detectCycles(dependencies) boolean
        -topologicalSort(tasks) List~WorkTask~
    }

    class TaskProgressTracker {
        <<Service>>
        -Map~String, Progress~ progressMap
        -MetricsCollector metrics
        +trackProgress(taskId, progress) void
        +getProgress(taskId) Progress
        +calculateCompletion(taskId) Percentage
        +estimateRemaining(taskId) Duration
        -updateMetrics(task, progress) void
    }

    TaskOrchestrator --> TaskFactory : uses
    TaskOrchestrator --> TaskDispatcher : uses
    TaskOrchestrator --> TaskCoordinator : coordinates with
    TaskDispatcher --> TaskProgressTracker : updates
```

## Command and Query Handlers

```mermaid
classDiagram
    class CreateTaskCommand {
        <<Command>>
        -TaskType type
        -Priority priority
        -TaskContext context
        -List~Instruction~ instructions
        -Constraints constraints
        +validate() ValidationResult
    }

    class CreateTaskHandler {
        <<Command Handler>>
        -TaskFactory factory
        -TaskRepository repository
        -EventBus eventBus
        +handle(command) TaskId
        -buildTask(command) WorkTask
        -validateTask(task) void
        -saveTask(task) void
    }

    class AssignTaskCommand {
        <<Command>>
        -String taskId
        -String operatorId
        -boolean autoAssign
        +validate() ValidationResult
    }

    class AssignTaskHandler {
        <<Command Handler>>
        -TaskAssignmentEngine engine
        -TaskRepository repository
        -EventBus eventBus
        +handle(command) AssignmentResult
        -loadTask(taskId) WorkTask
        -performAssignment(task, operatorId) void
    }

    class CompleteTaskCommand {
        <<Command>>
        -String taskId
        -TaskResult result
        -Map~String, Object~ outputs
        +validate() ValidationResult
    }

    class CompleteTaskHandler {
        <<Command Handler>>
        -TaskRepository repository
        -TaskValidator validator
        -EventBus eventBus
        +handle(command) CompletionResult
        -validateCompletion(task, result) void
        -updateTask(task, result) void
    }

    class GetTaskQuery {
        <<Query>>
        -String taskId
        -boolean includeHistory
        -boolean includeMetrics
    }

    class GetTaskHandler {
        <<Query Handler>>
        -TaskReadModel readModel
        +handle(query) TaskDto
        -loadTask(taskId) TaskProjection
        -enrichWithHistory(task) void
    }

    class GetOperatorTasksQuery {
        <<Query>>
        -String operatorId
        -TaskStatus status
        -DateRange dateRange
    }

    class GetOperatorTasksHandler {
        <<Query Handler>>
        -TaskReadModel readModel
        +handle(query) List~TaskSummary~
        -findOperatorTasks(operatorId, criteria) List~Task~
    }

    CreateTaskHandler ..> CreateTaskCommand : handles
    AssignTaskHandler ..> AssignTaskCommand : handles
    CompleteTaskHandler ..> CompleteTaskCommand : handles
    GetTaskHandler ..> GetTaskQuery : handles
    GetOperatorTasksHandler ..> GetOperatorTasksQuery : handles
```

## Task Execution Tracking

```mermaid
classDiagram
    class TaskExecutionContext {
        <<Value Object>>
        -String waveId
        -String orderId
        -String customerId
        -Map~String, Object~ parameters
        -List~Reference~ references
        -ExecutionConstraints constraints
        +getValue(key) Object
        +addParameter(key, value) void
        +validate() boolean
    }

    class TaskPerformanceMetrics {
        <<Entity>>
        -String taskId
        -Duration plannedDuration
        -Duration actualDuration
        -int attemptCount
        -List~TaskError~ errors
        -double completionRate
        -QualityScore qualityScore
        +calculateEfficiency() double
        +recordError(error) void
        +updateScore(score) void
    }

    class OperatorPerformance {
        <<Entity>>
        -String operatorId
        -Map~TaskType, Metrics~ taskMetrics
        -double overallScore
        -int tasksCompleted
        -int tasksAssigned
        -Duration totalWorkTime
        +updateMetrics(task, result) void
        +calculateProductivity() double
        +getAverageTaskTime(type) Duration
    }

    class TaskAuditLog {
        <<Entity>>
        -String auditId
        -String taskId
        -String operatorId
        -AuditAction action
        -Map~String, Object~ changes
        -DateTime timestamp
        -String reason
        +log(action, details) void
        +getHistory(taskId) List~AuditEntry~
    }

    class TaskException {
        <<Entity>>
        -String exceptionId
        -String taskId
        -ExceptionType type
        -String description
        -Severity severity
        -ResolutionStatus status
        -String resolvedBy
        +report(exception) void
        +resolve(resolution) void
        +escalate() void
    }

    WorkTask "1" --> "1" TaskExecutionContext : has
    WorkTask "1" --> "1" TaskPerformanceMetrics : tracks
    OperatorPerformance "1" --> "*" WorkTask : measures
    TaskAuditLog "1" --> "*" WorkTask : audits
    WorkTask "1" --> "*" TaskException : may have
```

## Domain Events

```mermaid
classDiagram
    class TaskEvent {
        <<Abstract Event>>
        -String eventId
        -String taskId
        -DateTime occurredAt
        -String operatorId
        +getEventType() String
    }

    class TaskCreatedEvent {
        <<Event>>
        -TaskType type
        -Priority priority
        -String sourceId
        +getEventType() String
    }

    class TaskAssignedEvent {
        <<Event>>
        -String operatorId
        -AssignmentMethod method
        -double score
        +getEventType() String
    }

    class TaskStartedEvent {
        <<Event>>
        -DateTime startTime
        -Location startLocation
        +getEventType() String
    }

    class TaskCompletedEvent {
        <<Event>>
        -TaskResult result
        -Duration duration
        -Map~String, Object~ outputs
        +getEventType() String
    }

    class TaskFailedEvent {
        <<Event>>
        -FailureReason reason
        -String errorMessage
        -boolean retryable
        +getEventType() String
    }

    class TaskReassignedEvent {
        <<Event>>
        -String fromOperatorId
        -String toOperatorId
        -String reason
        +getEventType() String
    }

    TaskEvent <|-- TaskCreatedEvent
    TaskEvent <|-- TaskAssignedEvent
    TaskEvent <|-- TaskStartedEvent
    TaskEvent <|-- TaskCompletedEvent
    TaskEvent <|-- TaskFailedEvent
    TaskEvent <|-- TaskReassignedEvent
```

## Integration and External Services

```mermaid
classDiagram
    class TaskIntegrationService {
        <<Integration Service>>
        -WaveServiceClient waveClient
        -InventoryServiceClient inventoryClient
        -LocationServiceClient locationClient
        +fetchWaveDetails(waveId) WaveInfo
        +validateInventory(items) boolean
        +getLocationInfo(locationId) Location
        +updateTaskProgress(taskId, progress) void
    }

    class OperatorManagementService {
        <<Service>>
        -OperatorRepository repository
        -SkillMatrix skillMatrix
        -ShiftSchedule schedule
        +getAvailableOperators() List~Operator~
        +getOperatorSkills(operatorId) List~Skill~
        +isOperatorAvailable(operatorId) boolean
        +updateOperatorStatus(operatorId, status) void
    }

    class TaskNotificationService {
        <<Service>>
        -NotificationChannel channel
        -MessageTemplate templates
        +notifyAssignment(task, operator) void
        +notifyUrgentTask(task) void
        +notifyCompletion(task) void
        +sendAlert(alert) void
    }

    class TaskAnalyticsService {
        <<Analytics Service>>
        -DataCollector collector
        -AnalyticsEngine engine
        +analyzeTaskPerformance(period) Report
        +predictTaskDuration(task) Duration
        +identifyBottlenecks() List~Bottleneck~
        +generateKPIs() KPIReport
    }

    class MobileTaskAPI {
        <<API Service>>
        -TaskService taskService
        -AuthService authService
        +getNextTask(operatorId) TaskDto
        +acceptTask(taskId) Response
        +updateProgress(taskId, progress) Response
        +completeTask(taskId, result) Response
        +reportIssue(taskId, issue) Response
    }

    TaskIntegrationService --> WorkTask : enriches
    OperatorManagementService --> TaskAssignmentEngine : provides operators
    TaskNotificationService --> WorkTask : monitors
    TaskAnalyticsService --> TaskPerformanceMetrics : analyzes
    MobileTaskAPI --> WorkTask : exposes
```