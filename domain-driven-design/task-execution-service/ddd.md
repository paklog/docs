# Task Execution Service - Domain-Driven Design

## Bounded Context: Task Orchestration & Queue Management

The Task Execution Service provides unified task management across all warehouse operations, implementing priority-based queuing, intelligent worker assignment, and real-time task orchestration.

## Domain Model

### Aggregates

#### WorkTask (Aggregate Root)
**Purpose**: Universal task model supporting all warehouse work types

**Properties**:
```java
public class WorkTask {
    private TaskId taskId;
    private TaskType taskType;
    private TaskStatus status;
    private Priority priority;
    private TaskContext context; // Polymorphic
    private AssignmentInfo assignment;
    private ExecutionMetrics metrics;
    private List<TaskDependency> dependencies;
    private RetryPolicy retryPolicy;
    private TaskConstraints constraints;
}
```

**Invariants**:
- Task must be assigned before execution
- Cannot complete without required confirmations
- Dependencies must be resolved before starting
- Priority must be between 0-100
- Failed tasks must be reassigned within SLA

**State Transitions**:
```
CREATED -> QUEUED -> ASSIGNED -> IN_PROGRESS -> COMPLETED
    |         |          |            |
    |         |          |            +-> FAILED -> REASSIGNED
    |         |          |                            |
    |         |          +----------------------------+
    |         |
    +-------> CANCELLED
```

#### TaskQueue (Entity)
**Purpose**: Priority-based queue for task management

**Properties**:
```java
public class TaskQueue {
    private QueueId queueId;
    private QueueType type;
    private PriorityQueue<WorkTask> tasks;
    private QueueCapacity capacity;
    private ThrottlingPolicy throttling;
    private QueueMetrics metrics;
}
```

#### WorkerAssignment (Entity)
**Purpose**: Tracks task-to-worker allocations

**Properties**:
```java
public class WorkerAssignment {
    private AssignmentId assignmentId;
    private WorkerId workerId;
    private TaskId taskId;
    private AssignmentStatus status;
    private LocalDateTime assignedAt;
    private LocalDateTime startedAt;
    private LocalDateTime completedAt;
    private PerformanceMetrics performance;
}
```

### Value Objects

#### TaskContext (Polymorphic)
Base class for task-specific contexts:

```java
public abstract class TaskContext {
    private String contextType;
    private Map<String, Object> attributes;
}

public class PickTaskContext extends TaskContext {
    private List<PickItem> items;
    private List<Location> locations;
    private RouteOptimization route;
}

public class PutAwayTaskContext extends TaskContext {
    private LicensePlate licensePlate;
    private Location targetLocation;
    private List<Item> items;
}

public class ReplenishmentTaskContext extends TaskContext {
    private Location sourceLocation;
    private Location targetLocation;
    private SKU sku;
    private Quantity quantity;
}

public class CycleCountTaskContext extends TaskContext {
    private Location location;
    private List<ExpectedItem> expectedItems;
    private CountType countType;
}

public class MoveTaskContext extends TaskContext {
    private Location fromLocation;
    private Location toLocation;
    private List<LicensePlate> licensePlates;
}

public class PackTaskContext extends TaskContext {
    private PackingStation station;
    private List<OrderLine> items;
    private CartonType suggestedCarton;
}

public class ShipTaskContext extends TaskContext {
    private List<Package> packages;
    private Carrier carrier;
    private ShippingMethod method;
}
```

#### Priority
```java
public class Priority {
    private Integer value; // 0-100
    private PriorityFactors factors;

    public static Priority calculate(PriorityFactors factors) {
        // Complex priority calculation based on multiple factors
        return new Priority(calculatedValue, factors);
    }
}

public class PriorityFactors {
    private OrderPriority orderPriority;
    private LocalDateTime dueTime;
    private Integer taskAge;
    private CustomerTier customerTier;
    private Boolean expedited;
}
```

#### TaskType
```java
public enum TaskType {
    PICK,
    PUT_AWAY,
    REPLENISHMENT,
    CYCLE_COUNT,
    MOVE,
    PACK,
    SHIP,
    RECEIVE,
    QUALITY_CHECK,
    CONSOLIDATION
}
```

#### TaskStatus
```java
public enum TaskStatus {
    CREATED,
    QUEUED,
    ASSIGNED,
    ACCEPTED,
    IN_PROGRESS,
    PAUSED,
    COMPLETED,
    FAILED,
    CANCELLED,
    REASSIGNED
}
```

#### TaskConstraints
```java
public class TaskConstraints {
    private List<SkillRequirement> requiredSkills;
    private List<EquipmentRequirement> requiredEquipment;
    private TimeWindow executionWindow;
    private LocationRestrictions locationRestrictions;
    private Integer maxAttempts;
}
```

### Domain Services

#### TaskPriorityService
**Purpose**: Calculates and manages task priorities

```java
public interface TaskPriorityService {
    Priority calculatePriority(WorkTask task);
    void recalculatePriorities(List<WorkTask> tasks);
    List<WorkTask> reorderByPriority(List<WorkTask> tasks);
    void escalatePriority(TaskId taskId, EscalationReason reason);
}
```

#### TaskAssignmentService
**Purpose**: Intelligent task-to-worker assignment

```java
public interface TaskAssignmentService {
    WorkerAssignment assignTask(WorkTask task, List<Worker> available);
    void reassignTask(TaskId taskId, ReassignmentReason reason);
    List<Worker> findEligibleWorkers(WorkTask task);
    Double calculateWorkerScore(Worker worker, WorkTask task);
}
```

**Assignment Algorithm**:
- Skill matching score (40%)
- Location proximity score (30%)
- Worker performance history (20%)
- Current workload balance (10%)

#### TaskOrchestrationService
**Purpose**: Coordinates task execution flow

```java
public interface TaskOrchestrationService {
    void orchestrateTaskFlow(Wave wave);
    void handleTaskCompletion(TaskId taskId);
    void handleTaskFailure(TaskId taskId, FailureReason reason);
    void resolveDependencies(WorkTask task);
}
```

### Domain Events

#### Task Lifecycle Events
```java
public class TaskCreated extends DomainEvent {
    private TaskId taskId;
    private TaskType taskType;
    private Priority priority;
    private String createdBy;
}

public class TaskQueued extends DomainEvent {
    private TaskId taskId;
    private QueueId queueId;
    private Integer queuePosition;
}

public class TaskAssigned extends DomainEvent {
    private TaskId taskId;
    private WorkerId workerId;
    private LocalDateTime assignedAt;
}

public class TaskStarted extends DomainEvent {
    private TaskId taskId;
    private WorkerId workerId;
    private LocalDateTime startedAt;
    private Location startLocation;
}

public class TaskCompleted extends DomainEvent {
    private TaskId taskId;
    private WorkerId workerId;
    private LocalDateTime completedAt;
    private ExecutionMetrics metrics;
}

public class TaskFailed extends DomainEvent {
    private TaskId taskId;
    private FailureReason reason;
    private Integer attemptNumber;
    private Boolean willRetry;
}

public class TaskReassigned extends DomainEvent {
    private TaskId taskId;
    private WorkerId previousWorker;
    private WorkerId newWorker;
    private ReassignmentReason reason;
}
```

### Repository Interfaces

```java
public interface WorkTaskRepository {
    WorkTask save(WorkTask task);
    Optional<WorkTask> findById(TaskId taskId);
    List<WorkTask> findByStatus(TaskStatus status);
    List<WorkTask> findByWorker(WorkerId workerId);
    List<WorkTask> findPendingTasks();
    List<WorkTask> findByPriorityRange(Integer min, Integer max);
}

public interface TaskQueueRepository {
    void enqueue(WorkTask task);
    Optional<WorkTask> dequeue(QueueType type);
    List<WorkTask> peekQueue(QueueType type, int limit);
    Integer getQueueDepth(QueueType type);
}
```

## Integration Patterns

### Upstream Dependencies
- **Wave Planning**: Receives waves for task generation
- **WES Orchestration**: Receives complex workflow tasks
- **Robotics Fleet**: Receives robot task completions

### Downstream Dependencies
- **Pick Execution**: Sends pick tasks
- **Pack & Ship**: Sends packing tasks
- **Physical Tracking**: Updates on movements

### Events Published
- TaskCreated
- TaskAssigned
- TaskStarted
- TaskCompleted
- TaskFailed
- TaskReassigned

### Events Subscribed
- WaveReleased (from Wave Planning)
- RobotMissionCompleted (from Robotics Fleet)
- WorkflowStepReady (from WES Orchestration)

## Business Rules

### Priority Calculation Rules
1. **Base Priority**: Order priority (LOW=0, NORMAL=25, HIGH=50, URGENT=75)
2. **Time Factor**: +1 point per hour until due
3. **Age Factor**: +1 point per hour in queue
4. **Customer Tier**: PLATINUM +20, GOLD +10, SILVER +5
5. **Maximum Priority**: 100 (system expedite)

### Assignment Rules
1. **Skill Match**: Worker must have required skills
2. **Equipment**: Worker must have access to required equipment
3. **Location Proximity**: Prefer workers near task location
4. **Workload Balance**: Distribute tasks evenly
5. **Performance History**: Prefer high-performing workers for priority tasks

### Execution Rules
1. **Timeout**: Tasks timeout after 2 hours of inactivity
2. **Retry Policy**: Max 3 attempts with exponential backoff
3. **Escalation**: Priority +10 after each failed attempt
4. **Dependency Check**: All dependencies must be completed
5. **Concurrent Limit**: Max 5 active tasks per worker

## Performance Optimization

### Queue Management
```java
public class RedisTaskQueue implements TaskQueuePort {
    // Uses Redis sorted sets for O(log n) priority operations
    public void enqueue(WorkTask task) {
        redis.zadd(QUEUE_KEY, task.getPriority(), task);
    }

    public WorkTask dequeue() {
        return redis.zpopmax(QUEUE_KEY);
    }
}
```

### Caching Strategy
- Cache worker skills and certifications
- Cache task templates
- Cache location distances
- Cache worker performance scores

### Batch Processing
- Batch task creation from waves
- Batch priority recalculation
- Batch event publishing

## Monitoring & Metrics

### Key Metrics
- Task completion rate
- Average task duration by type
- Queue depth by priority
- Worker utilization rate
- Task failure rate
- Reassignment frequency

### SLA Targets
- Task assignment: < 2 seconds
- Priority calculation: < 100ms
- Queue operation: < 50ms
- Event publishing: < 100ms
- Task timeout: 2 hours