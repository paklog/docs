# Detailed Implementation Plan: WMS/WES Decoupling
## Implementation Tickets & API Specifications

**Document Version**: 1.0.0
**Created**: 2025-01-18
**Type**: Technical Implementation Guide

---

## Table of Contents

1. [Wave Planning Service - Implementation Tickets & APIs](#1-wave-planning-service-wms)
2. [Task Execution Service - Implementation Tickets & APIs](#2-task-execution-service-wes)
3. [Location Master Service - Implementation Tickets & APIs](#3-location-master-service-wms)
4. [Physical Tracking Service - Implementation Tickets & APIs](#4-physical-tracking-service-wes)
5. [Pick Execution Service - Implementation Tickets & APIs](#5-pick-execution-service-wes)
6. [Pack & Ship Service - Implementation Tickets & APIs](#6-pack--ship-service-wes)

---

## 1. Wave Planning Service (WMS)

### Implementation Tickets

#### Sprint 1: Foundation (Week 1-2)

##### WAVE-001: Service Bootstrap
**Type**: Technical Setup
**Priority**: P0 - Critical
**Estimation**: 5 points

**Description**:
Create the initial Spring Boot service structure for Wave Planning Service with all necessary dependencies and configurations.

**Acceptance Criteria**:
- [ ] Spring Boot 3.2 project created with required dependencies
- [ ] MongoDB configuration for wave data persistence
- [ ] Kafka configuration for event publishing/consuming
- [ ] Health check endpoints operational
- [ ] Docker containerization configured
- [ ] CI/CD pipeline setup in Jenkins/GitLab

**Technical Details**:
```yaml
dependencies:
  - spring-boot-starter-web: 3.2.0
  - spring-boot-starter-data-mongodb: 3.2.0
  - spring-kafka: 3.0.0
  - spring-cloud-starter-openfeign: 4.0.0
  - micrometer-registry-prometheus: 1.11.0
```

---

##### WAVE-002: Domain Model Implementation
**Type**: Feature
**Priority**: P0 - Critical
**Estimation**: 8 points

**Description**:
Implement the core Wave aggregate and related domain models including value objects and entities.

**Acceptance Criteria**:
- [ ] Wave aggregate root implemented with state machine
- [ ] WaveStrategy value object created
- [ ] WaveMetrics entity implemented
- [ ] CarrierCutoff entity created
- [ ] All invariants enforced in domain model
- [ ] Unit tests with >90% coverage

**Code Template**:
```java
@AggregateRoot
@Document(collection = "waves")
public class Wave {
    @Id
    private String waveId;
    private WaveStatus status;
    private List<String> orderIds;
    private WavePriority priority;
    private WaveStrategy strategy;
    private LocalDateTime plannedReleaseTime;
    private LocalDateTime actualReleaseTime;

    // State transitions with invariants
    public void release() {
        if (status != WaveStatus.PLANNED) {
            throw new InvalidStateException("Wave must be PLANNED to release");
        }
        if (!hasAllocatedInventory()) {
            throw new BusinessException("Cannot release wave without inventory allocation");
        }
        this.status = WaveStatus.RELEASED;
        this.actualReleaseTime = LocalDateTime.now();
        registerEvent(new WaveReleasedEvent(this));
    }
}
```

---

##### WAVE-003: Repository Layer
**Type**: Feature
**Priority**: P0 - Critical
**Estimation**: 5 points

**Description**:
Implement MongoDB repository layer with custom queries for wave management.

**Acceptance Criteria**:
- [ ] WaveRepository interface defined
- [ ] Custom queries for finding waves by status
- [ ] Optimistic locking implemented
- [ ] Aggregation pipelines for metrics
- [ ] Integration tests with embedded MongoDB

**Implementation**:
```java
@Repository
public interface WaveRepository extends MongoRepository<Wave, String> {

    @Query("{'status': ?0, 'plannedReleaseTime': {$lte: ?1}}")
    List<Wave> findReadyToRelease(WaveStatus status, LocalDateTime time);

    @Aggregation(pipeline = {
        "{ $match: { warehouseId: ?0 } }",
        "{ $group: { _id: '$status', count: { $sum: 1 } } }"
    })
    List<WaveStatusCount> getStatusDistribution(String warehouseId);
}
```

---

#### Sprint 2: Core Business Logic (Week 3-4)

##### WAVE-004: Wave Planning Service
**Type**: Feature
**Priority**: P0 - Critical
**Estimation**: 13 points

**Description**:
Implement the core wave planning business logic including different strategies and capacity calculations.

**Acceptance Criteria**:
- [ ] Wave planning strategies implemented (Time, Carrier, Zone, Priority)
- [ ] Capacity-based wave sizing logic
- [ ] Order grouping algorithms
- [ ] Carrier cutoff time enforcement
- [ ] Wave optimization logic
- [ ] Performance: Planning <500ms for 100 orders

**Strategy Implementations**:
```java
@Component
public class TimeBasedWaveStrategy implements WaveStrategy {

    @Override
    public List<Wave> planWaves(List<Order> orders, WaveConfig config) {
        Map<LocalDateTime, List<Order>> timeGroups = orders.stream()
            .collect(Collectors.groupingBy(
                order -> roundToWaveInterval(order.getSla(), config.getInterval())
            ));

        return timeGroups.entrySet().stream()
            .map(entry -> Wave.builder()
                .orders(entry.getValue())
                .plannedReleaseTime(entry.getKey())
                .strategy(StrategyType.TIME_BASED)
                .build())
            .collect(Collectors.toList());
    }
}

@Component
public class CarrierBasedWaveStrategy implements WaveStrategy {

    @Override
    public List<Wave> planWaves(List<Order> orders, WaveConfig config) {
        Map<String, List<Order>> carrierGroups = orders.stream()
            .collect(Collectors.groupingBy(Order::getCarrier));

        return carrierGroups.entrySet().stream()
            .map(entry -> createCarrierWave(entry.getKey(), entry.getValue()))
            .collect(Collectors.toList());
    }
}
```

---

##### WAVE-005: Event Publishing Infrastructure
**Type**: Technical
**Priority**: P1 - High
**Estimation**: 5 points

**Description**:
Implement event publishing infrastructure using CloudEvents specification.

**Acceptance Criteria**:
- [ ] CloudEvents format implementation
- [ ] Transactional outbox pattern
- [ ] Event versioning support
- [ ] Failed event retry logic
- [ ] Event schema registry integration

**Implementation**:
```java
@Component
public class WaveEventPublisher {

    private final KafkaTemplate<String, CloudEvent> kafkaTemplate;
    private final OutboxRepository outboxRepository;

    @Transactional
    public void publishWaveReleased(Wave wave) {
        // Save to outbox in same transaction
        OutboxEvent outboxEvent = OutboxEvent.builder()
            .aggregateId(wave.getWaveId())
            .eventType("WaveReleasedEvent")
            .payload(toJson(wave))
            .status(OutboxStatus.PENDING)
            .build();

        outboxRepository.save(outboxEvent);

        // Async publish from outbox
        schedulePublish(outboxEvent);
    }
}
```

---

##### WAVE-006: Integration with Order Management
**Type**: Integration
**Priority**: P1 - High
**Estimation**: 8 points

**Description**:
Implement integration with Order Management Service for order validation and updates.

**Acceptance Criteria**:
- [ ] Feign client for Order Service API
- [ ] Circuit breaker configuration
- [ ] Retry logic with exponential backoff
- [ ] Fallback mechanisms
- [ ] Integration tests with WireMock

---

#### Sprint 3: Advanced Features (Week 5-6)

##### WAVE-007: Workload Forecasting
**Type**: Feature
**Priority**: P2 - Medium
**Estimation**: 8 points

**Description**:
Implement workload forecasting and capacity planning features.

**Acceptance Criteria**:
- [ ] Historical data analysis
- [ ] Predictive workload calculation
- [ ] Resource requirement estimation
- [ ] Capacity constraint validation
- [ ] Alert generation for capacity issues

---

##### WAVE-008: Wave Release Orchestration
**Type**: Feature
**Priority**: P1 - High
**Estimation**: 8 points

**Description**:
Implement wave release orchestration with inventory validation and task generation triggering.

**Acceptance Criteria**:
- [ ] Pre-release validation checks
- [ ] Inventory allocation verification
- [ ] Wave release event publishing
- [ ] Rollback mechanism for failures
- [ ] Idempotent release operation

---

##### WAVE-009: Monitoring & Metrics
**Type**: Technical
**Priority**: P2 - Medium
**Estimation**: 5 points

**Description**:
Implement comprehensive monitoring and metrics collection.

**Acceptance Criteria**:
- [ ] Prometheus metrics exposed
- [ ] Custom business metrics (waves/hour, avg size, etc.)
- [ ] Distributed tracing with OpenTelemetry
- [ ] Performance metrics (p50, p95, p99)
- [ ] Grafana dashboards configured

---

### API Specifications

```yaml
openapi: 3.0.3
info:
  title: Wave Planning Service API
  version: 1.0.0
  description: WMS service for wave planning and workload management
servers:
  - url: https://api.paklog.com/wms/wave-planning/v1
    description: Production server
  - url: https://staging-api.paklog.com/wms/wave-planning/v1
    description: Staging server

paths:
  /waves:
    post:
      summary: Create new wave
      operationId: createWave
      tags:
        - Wave Management
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateWaveRequest'
      responses:
        '201':
          description: Wave created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WaveResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '500':
          $ref: '#/components/responses/InternalError'

    get:
      summary: List waves with filters
      operationId: listWaves
      tags:
        - Wave Management
      parameters:
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/WaveStatus'
        - name: warehouseId
          in: query
          schema:
            type: string
        - name: fromDate
          in: query
          schema:
            type: string
            format: date-time
        - name: toDate
          in: query
          schema:
            type: string
            format: date-time
        - name: page
          in: query
          schema:
            type: integer
            default: 0
        - name: size
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: List of waves
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WaveListResponse'

  /waves/{waveId}:
    get:
      summary: Get wave details
      operationId: getWave
      tags:
        - Wave Management
      parameters:
        - name: waveId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Wave details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WaveResponse'
        '404':
          $ref: '#/components/responses/NotFound'

    patch:
      summary: Update wave
      operationId: updateWave
      tags:
        - Wave Management
      parameters:
        - name: waveId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateWaveRequest'
      responses:
        '200':
          description: Wave updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WaveResponse'

  /waves/{waveId}/release:
    post:
      summary: Release wave for execution
      operationId: releaseWave
      tags:
        - Wave Operations
      parameters:
        - name: waveId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                force:
                  type: boolean
                  default: false
                  description: Force release even with warnings
      responses:
        '200':
          description: Wave released successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WaveReleaseResponse'
        '409':
          description: Wave cannot be released
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /waves/{waveId}/cancel:
    post:
      summary: Cancel wave
      operationId: cancelWave
      tags:
        - Wave Operations
      parameters:
        - name: waveId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                reason:
                  type: string
                  required: true
      responses:
        '200':
          description: Wave cancelled

  /waves/plan:
    post:
      summary: Plan waves for orders
      operationId: planWaves
      tags:
        - Wave Planning
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PlanWavesRequest'
      responses:
        '200':
          description: Waves planned successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WavePlanResponse'

  /waves/strategies:
    get:
      summary: Get available wave strategies
      operationId: getStrategies
      tags:
        - Configuration
      responses:
        '200':
          description: List of strategies
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/WaveStrategy'

  /workload/forecast:
    get:
      summary: Get workload forecast
      operationId: getWorkloadForecast
      tags:
        - Workload Management
      parameters:
        - name: warehouseId
          in: query
          required: true
          schema:
            type: string
        - name: startTime
          in: query
          required: true
          schema:
            type: string
            format: date-time
        - name: endTime
          in: query
          required: true
          schema:
            type: string
            format: date-time
      responses:
        '200':
          description: Workload forecast
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WorkloadForecast'

  /metrics:
    get:
      summary: Get wave metrics
      operationId: getMetrics
      tags:
        - Analytics
      parameters:
        - name: warehouseId
          in: query
          schema:
            type: string
        - name: fromDate
          in: query
          schema:
            type: string
            format: date
        - name: toDate
          in: query
          schema:
            type: string
            format: date
      responses:
        '200':
          description: Wave metrics
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WaveMetrics'

components:
  schemas:
    CreateWaveRequest:
      type: object
      required:
        - orderIds
        - strategy
        - warehouseId
      properties:
        orderIds:
          type: array
          items:
            type: string
          minItems: 1
        strategy:
          $ref: '#/components/schemas/WaveStrategyType'
        warehouseId:
          type: string
        priority:
          $ref: '#/components/schemas/Priority'
        plannedReleaseTime:
          type: string
          format: date-time
        metadata:
          type: object
          additionalProperties: true

    WaveResponse:
      type: object
      properties:
        waveId:
          type: string
        status:
          $ref: '#/components/schemas/WaveStatus'
        orderIds:
          type: array
          items:
            type: string
        orderCount:
          type: integer
        lineCount:
          type: integer
        unitCount:
          type: integer
        strategy:
          $ref: '#/components/schemas/WaveStrategyType'
        priority:
          $ref: '#/components/schemas/Priority'
        warehouseId:
          type: string
        assignedZone:
          type: string
        plannedReleaseTime:
          type: string
          format: date-time
        actualReleaseTime:
          type: string
          format: date-time
        completedAt:
          type: string
          format: date-time
        metrics:
          $ref: '#/components/schemas/WaveMetrics'
        createdAt:
          type: string
          format: date-time
        updatedAt:
          type: string
          format: date-time

    WaveStatus:
      type: string
      enum:
        - PLANNED
        - RELEASED
        - IN_PROGRESS
        - COMPLETED
        - CANCELLED

    WaveStrategyType:
      type: string
      enum:
        - TIME_BASED
        - CARRIER_BASED
        - ZONE_BASED
        - PRIORITY_BASED
        - CUSTOM

    Priority:
      type: string
      enum:
        - CRITICAL
        - HIGH
        - NORMAL
        - LOW

    WaveMetrics:
      type: object
      properties:
        plannedPickTime:
          type: number
          format: double
        actualPickTime:
          type: number
          format: double
        pickAccuracy:
          type: number
          format: double
        laborEfficiency:
          type: number
          format: double
        orderFillRate:
          type: number
          format: double

    PlanWavesRequest:
      type: object
      required:
        - orderIds
        - strategy
        - config
      properties:
        orderIds:
          type: array
          items:
            type: string
        strategy:
          $ref: '#/components/schemas/WaveStrategyType'
        config:
          type: object
          properties:
            maxWaveSize:
              type: integer
            maxOrders:
              type: integer
            maxLines:
              type: integer
            interval:
              type: string
              format: duration

    WorkloadForecast:
      type: object
      properties:
        warehouseId:
          type: string
        timeSlots:
          type: array
          items:
            type: object
            properties:
              startTime:
                type: string
                format: date-time
              endTime:
                type: string
                format: date-time
              expectedOrders:
                type: integer
              expectedUnits:
                type: integer
              requiredPickers:
                type: integer
              requiredPackers:
                type: integer
              utilization:
                type: number
                format: double
```

---

## 2. Task Execution Service (WES)

### Implementation Tickets

#### Sprint 1: Foundation (Week 1-2)

##### TASK-001: Service Bootstrap
**Type**: Technical Setup
**Priority**: P0 - Critical
**Estimation**: 5 points

**Description**:
Create Task Execution Service with unified task model for all warehouse work types.

**Acceptance Criteria**:
- [ ] Spring Boot service initialized
- [ ] MongoDB configuration for tasks
- [ ] Kafka consumer/producer setup
- [ ] Redis cache for task queues
- [ ] WebSocket support for real-time updates

---

##### TASK-002: Unified Task Model
**Type**: Feature
**Priority**: P0 - Critical
**Estimation**: 13 points

**Description**:
Implement unified task model that can handle all types of warehouse work.

**Acceptance Criteria**:
- [ ] WorkTask aggregate with polymorphic support
- [ ] Task state machine implementation
- [ ] Task type registry (PICK, PACK, PUTAWAY, COUNT, etc.)
- [ ] Task context for type-specific data
- [ ] Priority calculation logic
- [ ] SLA tracking

**Implementation**:
```java
@AggregateRoot
@Document(collection = "work_tasks")
@TypeAlias("WorkTask")
public class WorkTask {
    @Id
    private String taskId;
    private TaskType type;
    private TaskStatus status;
    private Priority priority;
    private String assignedTo;
    private String warehouseId;
    private String zone;
    private Location taskLocation;
    private LocalDateTime createdAt;
    private LocalDateTime assignedAt;
    private LocalDateTime startedAt;
    private LocalDateTime completedAt;
    private Duration estimatedDuration;
    private Duration actualDuration;
    private String referenceId;

    @DBRef
    private TaskContext taskContext;

    // Polymorphic task contexts
    @JsonTypeInfo(use = JsonTypeInfo.Id.NAME, property = "type")
    @JsonSubTypes({
        @JsonSubTypes.Type(value = PickTaskContext.class, name = "PICK"),
        @JsonSubTypes.Type(value = PackTaskContext.class, name = "PACK"),
        @JsonSubTypes.Type(value = PutawayTaskContext.class, name = "PUTAWAY")
    })
    public interface TaskContext {
        void validate();
        Map<String, Object> getMetadata();
    }

    @Document
    public static class PickTaskContext implements TaskContext {
        private List<PickInstruction> instructions;
        private String waveId;
        private PickStrategy strategy;
        // Implementation...
    }
}
```

---

##### TASK-003: Task Queue Management
**Type**: Feature
**Priority**: P0 - Critical
**Estimation**: 8 points

**Description**:
Implement multi-queue task management system with priority handling.

**Acceptance Criteria**:
- [ ] Redis-backed priority queues
- [ ] Queue per task type
- [ ] Queue per zone/area
- [ ] Fair work distribution
- [ ] Queue monitoring APIs
- [ ] Starvation prevention

**Implementation**:
```java
@Service
public class TaskQueueManager {

    private final RedisTemplate<String, WorkTask> redisTemplate;

    public void enqueue(WorkTask task) {
        String queueKey = buildQueueKey(task);
        double score = calculatePriorityScore(task);
        redisTemplate.opsForZSet().add(queueKey, task, score);
    }

    public Optional<WorkTask> dequeue(String workerId, Set<TaskType> capabilities) {
        List<String> queues = getEligibleQueues(workerId, capabilities);

        for (String queue : queues) {
            Set<WorkTask> tasks = redisTemplate.opsForZSet()
                .rangeWithScores(queue, 0, 0);

            if (!tasks.isEmpty()) {
                WorkTask task = tasks.iterator().next();
                if (tryAssign(task, workerId)) {
                    redisTemplate.opsForZSet().remove(queue, task);
                    return Optional.of(task);
                }
            }
        }

        return Optional.empty();
    }

    private double calculatePriorityScore(WorkTask task) {
        // Lower score = higher priority
        double base = task.getPriority().getValue() * 1000;
        double aging = Duration.between(task.getCreatedAt(), Instant.now())
            .toMinutes();
        return base - aging; // Tasks get higher priority as they age
    }
}
```

---

#### Sprint 2: Task Assignment (Week 3-4)

##### TASK-004: Assignment Engine
**Type**: Feature
**Priority**: P0 - Critical
**Estimation**: 13 points

**Description**:
Implement intelligent task assignment engine with worker scoring.

**Acceptance Criteria**:
- [ ] Worker capability matching
- [ ] Distance-based scoring
- [ ] Workload balancing
- [ ] Performance history consideration
- [ ] Real-time assignment
- [ ] Assignment rejection handling

**Scoring Algorithm**:
```java
@Service
public class TaskAssignmentEngine {

    public AssignmentResult assignTask(WorkTask task, List<Worker> availableWorkers) {

        List<WorkerScore> scores = availableWorkers.stream()
            .filter(worker -> worker.canPerform(task.getType()))
            .map(worker -> calculateScore(worker, task))
            .sorted(Comparator.reverseOrder())
            .collect(Collectors.toList());

        if (scores.isEmpty()) {
            return AssignmentResult.noEligibleWorker();
        }

        // Try assignment with best workers
        for (WorkerScore score : scores) {
            if (tryAssign(task, score.getWorker())) {
                return AssignmentResult.success(score.getWorker());
            }
        }

        return AssignmentResult.failed("All workers rejected");
    }

    private WorkerScore calculateScore(Worker worker, WorkTask task) {
        double score = 100.0;

        // Distance score (0-30 points)
        double distance = calculateDistance(
            worker.getCurrentLocation(),
            task.getTaskLocation()
        );
        score += Math.max(0, 30 - (distance / 10));

        // Current workload (0-20 points)
        int currentTasks = worker.getActiveTasks().size();
        score += Math.max(0, 20 - (currentTasks * 5));

        // Performance score (0-30 points)
        double performanceRate = worker.getPerformanceMetrics()
            .getCompletionRate(task.getType());
        score += performanceRate * 30;

        // Skill match (0-20 points)
        if (worker.hasSpecialization(task.getType())) {
            score += 20;
        }

        return new WorkerScore(worker, score);
    }
}
```

---

##### TASK-005: Event-Driven Task Generation
**Type**: Integration
**Priority**: P1 - High
**Estimation**: 8 points

**Description**:
Implement event handlers for automatic task generation from various triggers.

**Acceptance Criteria**:
- [ ] Wave release → Pick task generation
- [ ] Receipt completion → Putaway task generation
- [ ] Low stock → Replenishment task generation
- [ ] Order packed → Ship task generation
- [ ] Idempotent task creation

---

##### TASK-006: Mobile Task API
**Type**: Feature
**Priority**: P1 - High
**Estimation**: 8 points

**Description**:
Create mobile-optimized API for warehouse associates.

**Acceptance Criteria**:
- [ ] Get next task endpoint
- [ ] Task acceptance/rejection
- [ ] Progress updates
- [ ] Exception reporting
- [ ] Offline capability support
- [ ] WebSocket for real-time updates

---

#### Sprint 3: Advanced Features (Week 5-6)

##### TASK-007: Task Optimization
**Type**: Feature
**Priority**: P2 - Medium
**Estimation**: 13 points

**Description**:
Implement task batching and interleaving optimization.

**Acceptance Criteria**:
- [ ] Batch similar tasks
- [ ] Interleave different task types
- [ ] Zone-based batching
- [ ] Travel distance minimization
- [ ] Dynamic re-optimization

---

##### TASK-008: Performance Tracking
**Type**: Feature
**Priority**: P2 - Medium
**Estimation**: 5 points

**Description**:
Implement comprehensive performance tracking and analytics.

**Acceptance Criteria**:
- [ ] Task completion rates
- [ ] Average task duration by type
- [ ] Worker productivity metrics
- [ ] Queue wait times
- [ ] Real-time dashboards

---

### API Specifications

```yaml
openapi: 3.0.3
info:
  title: Task Execution Service API
  version: 1.0.0
  description: WES service for unified task management and execution
servers:
  - url: https://api.paklog.com/wes/task-execution/v1

paths:
  /tasks:
    post:
      summary: Create new task
      operationId: createTask
      tags:
        - Task Management
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateTaskRequest'
      responses:
        '201':
          description: Task created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TaskResponse'

    get:
      summary: Query tasks
      operationId: queryTasks
      tags:
        - Task Management
      parameters:
        - name: type
          in: query
          schema:
            $ref: '#/components/schemas/TaskType'
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/TaskStatus'
        - name: assignedTo
          in: query
          schema:
            type: string
        - name: warehouseId
          in: query
          schema:
            type: string
        - name: zone
          in: query
          schema:
            type: string
      responses:
        '200':
          description: List of tasks
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/TaskResponse'

  /tasks/{taskId}:
    get:
      summary: Get task details
      operationId: getTask
      parameters:
        - name: taskId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Task details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TaskResponse'

  /tasks/{taskId}/assign:
    post:
      summary: Assign task to worker
      operationId: assignTask
      parameters:
        - name: taskId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                workerId:
                  type: string
                force:
                  type: boolean
      responses:
        '200':
          description: Task assigned

  /tasks/{taskId}/start:
    post:
      summary: Start task execution
      operationId: startTask
      parameters:
        - name: taskId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Task started

  /tasks/{taskId}/complete:
    post:
      summary: Complete task
      operationId: completeTask
      parameters:
        - name: taskId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CompleteTaskRequest'
      responses:
        '200':
          description: Task completed

  /tasks/{taskId}/exception:
    post:
      summary: Report task exception
      operationId: reportException
      parameters:
        - name: taskId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                exceptionType:
                  type: string
                description:
                  type: string
                resolution:
                  type: string
      responses:
        '200':
          description: Exception reported

  /mobile/next-task:
    get:
      summary: Get next task for worker
      operationId: getNextTask
      tags:
        - Mobile API
      security:
        - bearerAuth: []
      responses:
        '200':
          description: Next task
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MobileTaskResponse'
        '204':
          description: No tasks available

  /mobile/my-tasks:
    get:
      summary: Get worker's assigned tasks
      operationId: getMyTasks
      tags:
        - Mobile API
      security:
        - bearerAuth: []
      responses:
        '200':
          description: Worker's tasks
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/MobileTaskResponse'

  /mobile/task/{taskId}/accept:
    post:
      summary: Accept task assignment
      operationId: acceptTask
      tags:
        - Mobile API
      parameters:
        - name: taskId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Task accepted

  /mobile/task/{taskId}/reject:
    post:
      summary: Reject task assignment
      operationId: rejectTask
      tags:
        - Mobile API
      parameters:
        - name: taskId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                reason:
                  type: string
      responses:
        '200':
          description: Task rejected

  /mobile/task/{taskId}/progress:
    post:
      summary: Update task progress
      operationId: updateProgress
      tags:
        - Mobile API
      parameters:
        - name: taskId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                percentComplete:
                  type: integer
                currentStep:
                  type: string
                metadata:
                  type: object
      responses:
        '200':
          description: Progress updated

  /queues:
    get:
      summary: Get queue status
      operationId: getQueueStatus
      tags:
        - Queue Management
      parameters:
        - name: warehouseId
          in: query
          schema:
            type: string
        - name: zone
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Queue status
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/QueueStatus'

  /workers/{workerId}/performance:
    get:
      summary: Get worker performance metrics
      operationId: getWorkerPerformance
      tags:
        - Analytics
      parameters:
        - name: workerId
          in: path
          required: true
          schema:
            type: string
        - name: fromDate
          in: query
          schema:
            type: string
            format: date
        - name: toDate
          in: query
          schema:
            type: string
            format: date
      responses:
        '200':
          description: Performance metrics
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WorkerPerformance'

  /ws/tasks:
    get:
      summary: WebSocket endpoint for real-time task updates
      operationId: taskWebSocket
      tags:
        - WebSocket
      responses:
        '101':
          description: Switching Protocols

components:
  schemas:
    TaskType:
      type: string
      enum:
        - PICK
        - PACK
        - PUTAWAY
        - REPLENISH
        - COUNT
        - MOVE
        - SHIP

    TaskStatus:
      type: string
      enum:
        - PENDING
        - QUEUED
        - ASSIGNED
        - ACCEPTED
        - IN_PROGRESS
        - COMPLETED
        - CANCELLED
        - FAILED

    Priority:
      type: string
      enum:
        - CRITICAL
        - HIGH
        - NORMAL
        - LOW

    CreateTaskRequest:
      type: object
      required:
        - type
        - warehouseId
        - referenceId
      properties:
        type:
          $ref: '#/components/schemas/TaskType'
        warehouseId:
          type: string
        zone:
          type: string
        location:
          type: object
          properties:
            aisle:
              type: string
            bay:
              type: string
            level:
              type: string
        priority:
          $ref: '#/components/schemas/Priority'
        referenceId:
          type: string
        estimatedDuration:
          type: integer
          description: Duration in seconds
        deadline:
          type: string
          format: date-time
        context:
          type: object
          description: Type-specific task data

    TaskResponse:
      type: object
      properties:
        taskId:
          type: string
        type:
          $ref: '#/components/schemas/TaskType'
        status:
          $ref: '#/components/schemas/TaskStatus'
        priority:
          $ref: '#/components/schemas/Priority'
        assignedTo:
          type: string
        warehouseId:
          type: string
        zone:
          type: string
        location:
          type: object
        referenceId:
          type: string
        estimatedDuration:
          type: integer
        actualDuration:
          type: integer
        deadline:
          type: string
          format: date-time
        createdAt:
          type: string
          format: date-time
        assignedAt:
          type: string
          format: date-time
        startedAt:
          type: string
          format: date-time
        completedAt:
          type: string
          format: date-time
        context:
          type: object

    MobileTaskResponse:
      type: object
      properties:
        taskId:
          type: string
        type:
          $ref: '#/components/schemas/TaskType'
        priority:
          $ref: '#/components/schemas/Priority'
        location:
          type: object
          properties:
            zone:
              type: string
            aisle:
              type: string
            bay:
              type: string
            level:
              type: string
            navigationPath:
              type: array
              items:
                type: object
                properties:
                  instruction:
                    type: string
                  distance:
                    type: number
        instructions:
          type: array
          items:
            type: object
        estimatedTime:
          type: integer
        deadline:
          type: string
          format: date-time

    CompleteTaskRequest:
      type: object
      properties:
        completionCode:
          type: string
          enum:
            - SUCCESS
            - PARTIAL
            - FAILED
        results:
          type: object
        exceptions:
          type: array
          items:
            type: object
            properties:
              type:
                type: string
              description:
                type: string

    QueueStatus:
      type: object
      properties:
        queueName:
          type: string
        taskType:
          $ref: '#/components/schemas/TaskType'
        zone:
          type: string
        pendingTasks:
          type: integer
        assignedTasks:
          type: integer
        averageWaitTime:
          type: integer
          description: Average wait time in seconds
        oldestTaskAge:
          type: integer
          description: Age of oldest task in seconds

    WorkerPerformance:
      type: object
      properties:
        workerId:
          type: string
        period:
          type: object
          properties:
            from:
              type: string
              format: date
            to:
              type: string
              format: date
        metrics:
          type: object
          properties:
            tasksCompleted:
              type: integer
            averageTaskTime:
              type: number
            productivity:
              type: number
            accuracy:
              type: number
            utilizationRate:
              type: number
        breakdown:
          type: array
          items:
            type: object
            properties:
              taskType:
                $ref: '#/components/schemas/TaskType'
              count:
                type: integer
              averageTime:
                type: number
```

---

## 3. Location Master Service (WMS)

### Implementation Tickets

#### Sprint 1: Foundation (Week 1-2)

##### LOC-001: Service Bootstrap
**Type**: Technical Setup
**Priority**: P0 - Critical
**Estimation**: 5 points

**Description**:
Create Location Master Service for warehouse location configuration and management.

**Acceptance Criteria**:
- [ ] Spring Boot service setup
- [ ] PostgreSQL for location hierarchy
- [ ] Event publishing infrastructure
- [ ] Location hierarchy validation

---

##### LOC-002: Location Hierarchy Model
**Type**: Feature
**Priority**: P0 - Critical
**Estimation**: 8 points

**Description**:
Implement hierarchical location structure with validation rules.

**Acceptance Criteria**:
- [ ] Warehouse → Zone → Aisle → Bay → Level → Bin hierarchy
- [ ] Location code generation
- [ ] Capacity constraints
- [ ] Location types (PICK, RESERVE, STAGE, DOCK)
- [ ] Restriction management

**Implementation**:
```java
@Entity
@Table(name = "location_masters")
public class LocationMaster {

    @Id
    private String locationId;

    @ManyToOne
    @JoinColumn(name = "warehouse_id")
    private Warehouse warehouse;

    @ManyToOne
    @JoinColumn(name = "parent_location_id")
    private LocationMaster parent;

    @OneToMany(mappedBy = "parent")
    private Set<LocationMaster> children;

    @Enumerated(EnumType.STRING)
    private LocationLevel level; // WAREHOUSE, ZONE, AISLE, BAY, LEVEL, BIN

    @Enumerated(EnumType.STRING)
    private LocationType type;

    @Embedded
    private Dimensions dimensions;

    @Embedded
    private Capacity capacity;

    @ElementCollection
    @Enumerated(EnumType.STRING)
    private Set<LocationRestriction> restrictions;

    @Enumerated(EnumType.STRING)
    private SlottingClass slottingClass;

    private boolean active;

    public String getFullLocationCode() {
        if (parent == null) {
            return code;
        }
        return parent.getFullLocationCode() + "-" + code;
    }

    public void validateHierarchy() {
        // Ensure proper parent-child relationships
        // Validate level consistency
        // Check for circular references
    }
}
```

---

##### LOC-003: Slotting Configuration
**Type**: Feature
**Priority**: P1 - High
**Estimation**: 8 points

**Description**:
Implement slotting rules and velocity classification.

**Acceptance Criteria**:
- [ ] ABC velocity classification
- [ ] Slotting rules engine
- [ ] Product-location affinity
- [ ] Zone assignment rules
- [ ] Optimization suggestions

---

#### Sprint 2: Advanced Features (Week 3-4)

##### LOC-004: Capacity Management
**Type**: Feature
**Priority**: P1 - High
**Estimation**: 5 points

**Description**:
Implement comprehensive capacity tracking and management.

**Acceptance Criteria**:
- [ ] Weight capacity
- [ ] Volume capacity
- [ ] Unit capacity
- [ ] Capacity utilization calculations
- [ ] Overflow handling rules

---

##### LOC-005: Integration with Physical Tracking
**Type**: Integration
**Priority**: P1 - High
**Estimation**: 8 points

**Description**:
Implement bi-directional sync with Physical Tracking Service.

**Acceptance Criteria**:
- [ ] Location creation events
- [ ] Capacity update events
- [ ] Status change notifications
- [ ] Consistency validation
- [ ] Reconciliation support

---

### API Specifications

```yaml
openapi: 3.0.3
info:
  title: Location Master Service API
  version: 1.0.0
  description: WMS service for warehouse location configuration

paths:
  /locations:
    post:
      summary: Create location
      operationId: createLocation
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateLocationRequest'
      responses:
        '201':
          description: Location created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LocationResponse'

    get:
      summary: Search locations
      operationId: searchLocations
      parameters:
        - name: warehouseId
          in: query
          schema:
            type: string
        - name: zone
          in: query
          schema:
            type: string
        - name: type
          in: query
          schema:
            $ref: '#/components/schemas/LocationType'
        - name: slottingClass
          in: query
          schema:
            type: string
        - name: available
          in: query
          schema:
            type: boolean
      responses:
        '200':
          description: Location list
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/LocationResponse'

  /locations/{locationId}:
    get:
      summary: Get location details
      operationId: getLocation
      parameters:
        - name: locationId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Location details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LocationResponse'

    patch:
      summary: Update location
      operationId: updateLocation
      parameters:
        - name: locationId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateLocationRequest'
      responses:
        '200':
          description: Location updated

  /locations/{locationId}/activate:
    post:
      summary: Activate location
      operationId: activateLocation
      parameters:
        - name: locationId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Location activated

  /locations/{locationId}/deactivate:
    post:
      summary: Deactivate location
      operationId: deactivateLocation
      parameters:
        - name: locationId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                reason:
                  type: string
      responses:
        '200':
          description: Location deactivated

  /locations/hierarchy:
    get:
      summary: Get location hierarchy
      operationId: getLocationHierarchy
      parameters:
        - name: warehouseId
          in: query
          required: true
          schema:
            type: string
        - name: depth
          in: query
          schema:
            type: integer
            default: 3
      responses:
        '200':
          description: Location hierarchy tree
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LocationHierarchy'

  /slotting/optimize:
    post:
      summary: Generate slotting optimization
      operationId: optimizeSlotting
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SlottingOptimizationRequest'
      responses:
        '200':
          description: Optimization recommendations
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SlottingRecommendations'

  /slotting/rules:
    get:
      summary: Get slotting rules
      operationId: getSlottingRules
      responses:
        '200':
          description: Slotting rules
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/SlottingRule'

    post:
      summary: Create slotting rule
      operationId: createSlottingRule
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateSlottingRuleRequest'
      responses:
        '201':
          description: Rule created

components:
  schemas:
    LocationType:
      type: string
      enum:
        - PICK_PRIMARY
        - PICK_SECONDARY
        - RESERVE
        - BULK
        - STAGING
        - SHIPPING_DOCK
        - RECEIVING_DOCK
        - QUARANTINE
        - RETURNS
        - DAMAGED

    LocationLevel:
      type: string
      enum:
        - WAREHOUSE
        - ZONE
        - AISLE
        - BAY
        - LEVEL
        - BIN

    CreateLocationRequest:
      type: object
      required:
        - code
        - level
        - type
        - warehouseId
      properties:
        code:
          type: string
        name:
          type: string
        level:
          $ref: '#/components/schemas/LocationLevel'
        type:
          $ref: '#/components/schemas/LocationType'
        warehouseId:
          type: string
        parentLocationId:
          type: string
        dimensions:
          type: object
          properties:
            length:
              type: number
            width:
              type: number
            height:
              type: number
            unit:
              type: string
        capacity:
          type: object
          properties:
            weight:
              type: number
            weightUnit:
              type: string
            volume:
              type: number
            volumeUnit:
              type: string
            units:
              type: integer
        restrictions:
          type: array
          items:
            type: string
            enum:
              - HAZMAT
              - FROZEN
              - REFRIGERATED
              - FRAGILE
              - HIGH_VALUE
              - CONTROLLED

    LocationResponse:
      type: object
      properties:
        locationId:
          type: string
        code:
          type: string
        fullCode:
          type: string
        name:
          type: string
        level:
          $ref: '#/components/schemas/LocationLevel'
        type:
          $ref: '#/components/schemas/LocationType'
        warehouseId:
          type: string
        parentLocationId:
          type: string
        dimensions:
          type: object
        capacity:
          type: object
        restrictions:
          type: array
          items:
            type: string
        slottingClass:
          type: string
        active:
          type: boolean
        createdAt:
          type: string
          format: date-time
        updatedAt:
          type: string
          format: date-time
```

---

## 4. Physical Tracking Service (WES)

### Implementation Tickets

#### Sprint 1: Foundation (Week 1-2)

##### PHYS-001: Service Bootstrap
**Type**: Technical Setup
**Priority**: P0 - Critical
**Estimation**: 5 points

**Description**:
Create Physical Tracking Service for real-time location state and movement tracking.

**Acceptance Criteria**:
- [ ] Spring Boot service setup
- [ ] MongoDB for state tracking
- [ ] Kafka event streaming
- [ ] MQTT for IoT integration
- [ ] Time-series data support

---

##### PHYS-002: Location State Model
**Type**: Feature
**Priority**: P0 - Critical
**Estimation**: 8 points

**Description**:
Implement location state tracking with real-time updates.

**Acceptance Criteria**:
- [ ] Current occupancy tracking
- [ ] Status management (AVAILABLE, OCCUPIED, BLOCKED)
- [ ] License plate associations
- [ ] Movement history
- [ ] Real-time state updates

**Implementation**:
```java
@Document(collection = "location_states")
public class LocationState {

    @Id
    private String locationId;

    private OccupancyStatus occupancyStatus;
    private int currentItemCount;
    private double currentWeight;
    private double currentVolume;

    @DBRef
    private List<LicensePlate> licensePlates;

    private LocationStatus status;
    private String blockedReason;
    private LocalDateTime blockedUntil;

    private LocalDateTime lastMovementIn;
    private LocalDateTime lastMovementOut;
    private LocalDateTime lastCycleCount;
    private LocalDateTime lastStateChange;

    @Version
    private Long version;

    public void addLicensePlate(LicensePlate lp) {
        if (!canAccommodate(lp)) {
            throw new CapacityExceededException();
        }
        licensePlates.add(lp);
        updateOccupancy();
        registerEvent(new LicensePlateAddedEvent(locationId, lp.getId()));
    }

    public void removeLicensePlate(String lpId) {
        licensePlates.removeIf(lp -> lp.getId().equals(lpId));
        updateOccupancy();
        registerEvent(new LicensePlateRemovedEvent(locationId, lpId));
    }

    private void updateOccupancy() {
        currentItemCount = licensePlates.stream()
            .mapToInt(LicensePlate::getItemCount)
            .sum();
        currentWeight = licensePlates.stream()
            .mapToDouble(LicensePlate::getTotalWeight)
            .sum();
        occupancyStatus = calculateOccupancyStatus();
    }
}
```

---

##### PHYS-003: License Plate Management
**Type**: Feature
**Priority**: P0 - Critical
**Estimation**: 13 points

**Description**:
Implement comprehensive license plate lifecycle management.

**Acceptance Criteria**:
- [ ] LP generation with unique IDs
- [ ] LP content tracking
- [ ] Nested LP support (pallets → cases)
- [ ] LP movement tracking
- [ ] LP status management
- [ ] Barcode generation

**License Plate Model**:
```java
@Document(collection = "license_plates")
public class LicensePlate {

    @Id
    private String licensePlateId;

    @Enumerated(EnumType.STRING)
    private LicensePlateType type;

    @DBRef
    private List<LPItem> contents;

    private String currentLocationId;

    @DBRef
    private LicensePlate parentLP; // For nesting

    @DBRef
    private List<LicensePlate> childLPs;

    private LPStatus status;
    private LocalDateTime createdAt;
    private LocalDateTime lastMovedAt;

    public void addItem(String sku, int quantity, double weight) {
        LPItem item = new LPItem(sku, quantity, weight);
        contents.add(item);
        updateMetrics();
        registerEvent(new ItemAddedToLPEvent(licensePlateId, item));
    }

    public void moveTo(String newLocationId) {
        String previousLocation = this.currentLocationId;
        this.currentLocationId = newLocationId;
        this.lastMovedAt = LocalDateTime.now();

        registerEvent(new LicensePlateMovedEvent(
            licensePlateId,
            previousLocation,
            newLocationId
        ));

        // Move child LPs as well
        if (childLPs != null) {
            childLPs.forEach(child -> child.moveTo(newLocationId));
        }
    }

    public void nest(LicensePlate childLP) {
        if (this.type.ordinal() <= childLP.type.ordinal()) {
            throw new InvalidNestingException(
                "Cannot nest " + childLP.type + " in " + this.type
            );
        }
        childLP.parentLP = this;
        this.childLPs.add(childLP);
    }
}
```

---

#### Sprint 2: Movement Tracking (Week 3-4)

##### PHYS-004: Movement Service
**Type**: Feature
**Priority**: P0 - Critical
**Estimation**: 8 points

**Description**:
Implement movement tracking and validation service.

**Acceptance Criteria**:
- [ ] Movement validation rules
- [ ] Movement history tracking
- [ ] Batch movement support
- [ ] Movement reversal capability
- [ ] Audit trail

---

##### PHYS-005: RTLS Integration
**Type**: Integration
**Priority**: P2 - Medium
**Estimation**: 13 points

**Description**:
Integrate with Real-Time Location System for automated tracking.

**Acceptance Criteria**:
- [ ] MQTT broker setup
- [ ] RTLS event consumption
- [ ] Location triangulation
- [ ] Movement detection
- [ ] Alert generation for anomalies

---

### API Specifications

```yaml
openapi: 3.0.3
info:
  title: Physical Tracking Service API
  version: 1.0.0
  description: WES service for physical location state and movement tracking

paths:
  /location-states/{locationId}:
    get:
      summary: Get location state
      operationId: getLocationState
      parameters:
        - name: locationId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Location state
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LocationState'

    patch:
      summary: Update location state
      operationId: updateLocationState
      parameters:
        - name: locationId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateLocationStateRequest'
      responses:
        '200':
          description: State updated

  /location-states/{locationId}/block:
    post:
      summary: Block location
      operationId: blockLocation
      parameters:
        - name: locationId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                reason:
                  type: string
                until:
                  type: string
                  format: date-time
      responses:
        '200':
          description: Location blocked

  /license-plates:
    post:
      summary: Create license plate
      operationId: createLicensePlate
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateLicensePlateRequest'
      responses:
        '201':
          description: License plate created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LicensePlate'

    get:
      summary: Search license plates
      operationId: searchLicensePlates
      parameters:
        - name: locationId
          in: query
          schema:
            type: string
        - name: sku
          in: query
          schema:
            type: string
        - name: type
          in: query
          schema:
            type: string
      responses:
        '200':
          description: License plates
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/LicensePlate'

  /license-plates/{lpId}:
    get:
      summary: Get license plate details
      operationId: getLicensePlate
      parameters:
        - name: lpId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: License plate details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LicensePlate'

  /license-plates/{lpId}/add-item:
    post:
      summary: Add item to license plate
      operationId: addItemToLP
      parameters:
        - name: lpId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                sku:
                  type: string
                quantity:
                  type: integer
                weight:
                  type: number
      responses:
        '200':
          description: Item added

  /license-plates/{lpId}/move:
    post:
      summary: Move license plate
      operationId: moveLicensePlate
      parameters:
        - name: lpId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                toLocationId:
                  type: string
                reason:
                  type: string
      responses:
        '200':
          description: License plate moved

  /movements:
    post:
      summary: Record movement
      operationId: recordMovement
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MovementRequest'
      responses:
        '201':
          description: Movement recorded

    get:
      summary: Query movements
      operationId: queryMovements
      parameters:
        - name: locationId
          in: query
          schema:
            type: string
        - name: lpId
          in: query
          schema:
            type: string
        - name: fromDate
          in: query
          schema:
            type: string
            format: date-time
        - name: toDate
          in: query
          schema:
            type: string
            format: date-time
      responses:
        '200':
          description: Movement history
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Movement'

components:
  schemas:
    LocationState:
      type: object
      properties:
        locationId:
          type: string
        occupancyStatus:
          type: string
          enum:
            - EMPTY
            - PARTIAL
            - FULL
            - OVER_CAPACITY
        currentItemCount:
          type: integer
        currentWeight:
          type: number
        currentVolume:
          type: number
        licensePlates:
          type: array
          items:
            type: string
        status:
          type: string
          enum:
            - AVAILABLE
            - OCCUPIED
            - BLOCKED
            - MAINTENANCE
        blockedReason:
          type: string
        lastMovementIn:
          type: string
          format: date-time
        lastMovementOut:
          type: string
          format: date-time

    LicensePlate:
      type: object
      properties:
        licensePlateId:
          type: string
        type:
          type: string
          enum:
            - PALLET
            - CASE
            - CARTON
            - TOTE
            - EACH
        contents:
          type: array
          items:
            type: object
            properties:
              sku:
                type: string
              quantity:
                type: integer
              weight:
                type: number
        currentLocationId:
          type: string
        parentLPId:
          type: string
        childLPIds:
          type: array
          items:
            type: string
        status:
          type: string
          enum:
            - ACTIVE
            - CLOSED
            - IN_TRANSIT
            - CONSUMED
        createdAt:
          type: string
          format: date-time
        lastMovedAt:
          type: string
          format: date-time
```

---

## 5. Pick Execution Service (WES)

### Implementation Tickets

#### Sprint 1: Foundation (Week 1-2)

##### PICK-001: Service Bootstrap
**Type**: Technical Setup
**Priority**: P0 - Critical
**Estimation**: 5 points

**Description**:
Create Pick Execution Service for pick list execution and path optimization.

**Acceptance Criteria**:
- [ ] Spring Boot service setup
- [ ] MongoDB for pick sessions
- [ ] Redis for active sessions cache
- [ ] WebSocket for real-time updates
- [ ] Mobile API structure

---

##### PICK-002: Pick Session Management
**Type**: Feature
**Priority**: P0 - Critical
**Estimation**: 13 points

**Description**:
Implement pick session lifecycle management with state tracking.

**Acceptance Criteria**:
- [ ] Pick session creation from tasks
- [ ] Session assignment to pickers
- [ ] Progress tracking
- [ ] Exception handling
- [ ] Session suspension/resume
- [ ] Performance metrics

**Pick Session Model**:
```java
@Document(collection = "pick_sessions")
public class PickSession {

    @Id
    private String sessionId;
    private String pickerId;
    private String waveId;
    private SessionStatus status;

    private List<PickInstruction> instructions;
    private PickPath optimizedPath;
    private PickStrategy strategy;

    private int totalItems;
    private int pickedItems;
    private int shortPickedItems;

    private LocalDateTime startedAt;
    private LocalDateTime completedAt;
    private LocalDateTime lastActivityAt;

    private Location currentLocation;
    private int currentInstructionIndex;

    private List<PickConfirmation> confirmations;
    private List<PickException> exceptions;

    public PickInstruction getNextInstruction() {
        if (currentInstructionIndex >= instructions.size()) {
            return null;
        }
        return instructions.get(currentInstructionIndex);
    }

    public void confirmPick(String barcode, int quantity) {
        PickInstruction current = getNextInstruction();

        // Validate barcode
        if (!current.validateBarcode(barcode)) {
            throw new WrongItemException();
        }

        // Handle quantity
        if (quantity < current.getQuantityRequired()) {
            handleShortPick(current, quantity);
        } else {
            current.setQuantityPicked(quantity);
            current.setStatus(InstructionStatus.COMPLETED);
        }

        // Record confirmation
        confirmations.add(new PickConfirmation(
            current.getInstructionId(),
            quantity,
            barcode,
            LocalDateTime.now()
        ));

        // Move to next
        currentInstructionIndex++;
        pickedItems += quantity;

        // Update location
        currentLocation = current.getLocation();
        lastActivityAt = LocalDateTime.now();

        // Check completion
        if (currentInstructionIndex >= instructions.size()) {
            complete();
        }
    }

    private void handleShortPick(PickInstruction instruction, int actualQuantity) {
        int shortQuantity = instruction.getQuantityRequired() - actualQuantity;

        exceptions.add(new PickException(
            ExceptionType.SHORT_PICK,
            instruction.getInstructionId(),
            "Short " + shortQuantity + " units",
            LocalDateTime.now()
        ));

        instruction.setQuantityPicked(actualQuantity);
        instruction.setStatus(InstructionStatus.SHORT);
        shortPickedItems += shortQuantity;

        // Trigger replenishment if needed
        registerEvent(new ShortPickEvent(
            instruction.getSku(),
            instruction.getLocation(),
            shortQuantity
        ));
    }
}
```

---

##### PICK-003: Path Optimization Engine
**Type**: Feature
**Priority**: P0 - Critical
**Estimation**: 21 points

**Description**:
Implement sophisticated pick path optimization algorithms.

**Acceptance Criteria**:
- [ ] Multiple optimization strategies (S-shape, return, midpoint, largest gap)
- [ ] TSP solver for batch picking
- [ ] Zone-based optimization
- [ ] Congestion avoidance
- [ ] Dynamic re-optimization
- [ ] Performance: <500ms for 50 locations

**Optimization Implementation**:
```java
@Service
public class PickPathOptimizer {

    public PickPath optimize(
        List<PickLocation> locations,
        WarehouseGraph warehouse,
        PickStrategy strategy
    ) {
        return switch (strategy) {
            case S_SHAPE -> sShapeOptimization(locations, warehouse);
            case RETURN -> returnOptimization(locations, warehouse);
            case MIDPOINT -> midpointOptimization(locations, warehouse);
            case LARGEST_GAP -> largestGapOptimization(locations, warehouse);
            case OPTIMAL -> tspOptimization(locations, warehouse);
        };
    }

    private PickPath sShapeOptimization(
        List<PickLocation> locations,
        WarehouseGraph warehouse
    ) {
        // Sort locations by aisle and position
        Map<String, List<PickLocation>> byAisle = locations.stream()
            .collect(Collectors.groupingBy(PickLocation::getAisle));

        List<PickLocation> optimized = new ArrayList<>();
        boolean traverseForward = true;

        for (String aisle : byAisle.keySet().stream().sorted().toList()) {
            List<PickLocation> aisleLocations = byAisle.get(aisle);

            if (traverseForward) {
                aisleLocations.sort(Comparator.comparing(PickLocation::getPosition));
            } else {
                aisleLocations.sort(Comparator.comparing(PickLocation::getPosition).reversed());
            }

            optimized.addAll(aisleLocations);
            traverseForward = !traverseForward;
        }

        return new PickPath(
            optimized,
            calculateDistance(optimized, warehouse),
            estimateTime(optimized)
        );
    }

    private PickPath tspOptimization(
        List<PickLocation> locations,
        WarehouseGraph warehouse
    ) {
        // Build distance matrix
        double[][] distances = buildDistanceMatrix(locations, warehouse);

        // Apply 2-opt improvement
        List<Integer> tour = nearestNeighbor(distances);
        tour = twoOpt(tour, distances);

        // Convert back to locations
        List<PickLocation> optimized = tour.stream()
            .map(locations::get)
            .collect(Collectors.toList());

        return new PickPath(
            optimized,
            calculateTourDistance(tour, distances),
            estimateTime(optimized)
        );
    }

    private List<Integer> twoOpt(List<Integer> tour, double[][] distances) {
        boolean improved = true;

        while (improved) {
            improved = false;

            for (int i = 1; i < tour.size() - 2; i++) {
                for (int j = i + 1; j < tour.size() - 1; j++) {
                    double currentDistance =
                        distances[tour.get(i-1)][tour.get(i)] +
                        distances[tour.get(j)][tour.get(j+1)];

                    double newDistance =
                        distances[tour.get(i-1)][tour.get(j)] +
                        distances[tour.get(i)][tour.get(j+1)];

                    if (newDistance < currentDistance) {
                        // Reverse segment
                        Collections.reverse(tour.subList(i, j+1));
                        improved = true;
                    }
                }
            }
        }

        return tour;
    }
}
```

---

#### Sprint 2: Put Wall Operations (Week 3-4)

##### PICK-004: Put Wall Management
**Type**: Feature
**Priority**: P1 - High
**Estimation**: 13 points

**Description**:
Implement put wall sortation for batch picking.

**Acceptance Criteria**:
- [ ] Put wall configuration
- [ ] Slot assignment algorithm
- [ ] Order-to-slot mapping
- [ ] Item sorting workflow
- [ ] Completion detection
- [ ] Light integration support

---

##### PICK-005: Mobile Picking API
**Type**: Feature
**Priority**: P0 - Critical
**Estimation**: 8 points

**Description**:
Create comprehensive mobile API for picking operations.

**Acceptance Criteria**:
- [ ] Next pick instruction
- [ ] Barcode scanning validation
- [ ] Short pick reporting
- [ ] Navigation assistance
- [ ] Offline mode support
- [ ] Voice picking support

---

### API Specifications

```yaml
openapi: 3.0.3
info:
  title: Pick Execution Service API
  version: 1.0.0
  description: WES service for pick execution and path optimization

paths:
  /pick-sessions:
    post:
      summary: Create pick session
      operationId: createPickSession
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreatePickSessionRequest'
      responses:
        '201':
          description: Session created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PickSession'

  /pick-sessions/{sessionId}:
    get:
      summary: Get pick session
      operationId: getPickSession
      parameters:
        - name: sessionId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Session details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PickSession'

  /pick-sessions/{sessionId}/start:
    post:
      summary: Start pick session
      operationId: startPickSession
      parameters:
        - name: sessionId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Session started

  /pick-sessions/{sessionId}/confirm:
    post:
      summary: Confirm pick
      operationId: confirmPick
      parameters:
        - name: sessionId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PickConfirmationRequest'
      responses:
        '200':
          description: Pick confirmed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PickConfirmationResponse'

  /pick-sessions/{sessionId}/exception:
    post:
      summary: Report pick exception
      operationId: reportPickException
      parameters:
        - name: sessionId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PickExceptionRequest'
      responses:
        '200':
          description: Exception reported

  /pick-sessions/{sessionId}/complete:
    post:
      summary: Complete pick session
      operationId: completePickSession
      parameters:
        - name: sessionId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Session completed

  /mobile/pick/next:
    get:
      summary: Get next pick instruction
      operationId: getNextPick
      tags:
        - Mobile API
      security:
        - bearerAuth: []
      responses:
        '200':
          description: Next pick instruction
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MobilePickInstruction'

  /mobile/pick/scan:
    post:
      summary: Validate scan
      operationId: validateScan
      tags:
        - Mobile API
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                barcode:
                  type: string
                location:
                  type: string
      responses:
        '200':
          description: Scan valid
          content:
            application/json:
              schema:
                type: object
                properties:
                  valid:
                    type: boolean
                  message:
                    type: string

  /put-wall/slots:
    get:
      summary: Get put wall slots
      operationId: getPutWallSlots
      parameters:
        - name: wallId
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Put wall slots
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/PutWallSlot'

  /put-wall/slots/{slotId}/assign:
    post:
      summary: Assign order to slot
      operationId: assignSlot
      parameters:
        - name: slotId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                orderId:
                  type: string
      responses:
        '200':
          description: Slot assigned

  /put-wall/slots/{slotId}/sort:
    post:
      summary: Sort item to slot
      operationId: sortToSlot
      parameters:
        - name: slotId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                sku:
                  type: string
                quantity:
                  type: integer
      responses:
        '200':
          description: Item sorted

  /path/optimize:
    post:
      summary: Optimize pick path
      operationId: optimizePath
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PathOptimizationRequest'
      responses:
        '200':
          description: Optimized path
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OptimizedPath'

components:
  schemas:
    PickStrategy:
      type: string
      enum:
        - DISCRETE
        - BATCH
        - ZONE
        - CLUSTER
        - WAVE

    PathStrategy:
      type: string
      enum:
        - S_SHAPE
        - RETURN
        - MIDPOINT
        - LARGEST_GAP
        - OPTIMAL

    CreatePickSessionRequest:
      type: object
      required:
        - taskIds
        - pickerId
      properties:
        taskIds:
          type: array
          items:
            type: string
        pickerId:
          type: string
        strategy:
          $ref: '#/components/schemas/PickStrategy'

    PickSession:
      type: object
      properties:
        sessionId:
          type: string
        pickerId:
          type: string
        waveId:
          type: string
        status:
          type: string
          enum:
            - CREATED
            - ASSIGNED
            - STARTED
            - IN_PROGRESS
            - COMPLETED
            - SUSPENDED
        instructions:
          type: array
          items:
            $ref: '#/components/schemas/PickInstruction'
        totalItems:
          type: integer
        pickedItems:
          type: integer
        shortPickedItems:
          type: integer
        startedAt:
          type: string
          format: date-time
        estimatedCompletionTime:
          type: string
          format: date-time

    PickInstruction:
      type: object
      properties:
        instructionId:
          type: string
        sequence:
          type: integer
        sku:
          type: string
        description:
          type: string
        location:
          type: object
          properties:
            zone:
              type: string
            aisle:
              type: string
            bay:
              type: string
            level:
              type: string
        quantityRequired:
          type: integer
        quantityPicked:
          type: integer
        status:
          type: string
        imageUrl:
          type: string

    MobilePickInstruction:
      type: object
      properties:
        instruction:
          $ref: '#/components/schemas/PickInstruction'
        navigation:
          type: object
          properties:
            currentLocation:
              type: string
            targetLocation:
              type: string
            distance:
              type: number
            directions:
              type: array
              items:
                type: object
                properties:
                  instruction:
                    type: string
                  distance:
                    type: number

    PutWallSlot:
      type: object
      properties:
        slotId:
          type: string
        slotNumber:
          type: integer
        wallId:
          type: string
        assignedOrderId:
          type: string
        status:
          type: string
          enum:
            - EMPTY
            - ASSIGNED
            - IN_PROGRESS
            - COMPLETE
        expectedItems:
          type: integer
        currentItems:
          type: integer
        lightColor:
          type: string
```

---

## 6. Pack & Ship Service (WES)

### Implementation Tickets

#### Sprint 1: Foundation (Week 1-2)

##### PACK-001: Service Bootstrap
**Type**: Technical Setup
**Priority**: P0 - Critical
**Estimation**: 5 points

**Description**:
Create Pack & Ship Service for packing operations and shipping preparation.

**Acceptance Criteria**:
- [ ] Spring Boot service setup
- [ ] MongoDB for packing sessions
- [ ] Integration with shipping providers
- [ ] Label printing service
- [ ] Weight scale integration

---

##### PACK-002: Packing Workflow
**Type**: Feature
**Priority**: P0 - Critical
**Estimation**: 13 points

**Description**:
Implement comprehensive packing station workflow.

**Acceptance Criteria**:
- [ ] Packing session management
- [ ] Item scanning and verification
- [ ] Carton recommendation
- [ ] Packing material calculation
- [ ] Weight verification
- [ ] Quality checks

**Packing Session Model**:
```java
@Document(collection = "packing_sessions")
public class PackingSession {

    @Id
    private String sessionId;
    private String orderId;
    private String packerId;
    private String stationId;

    private List<ItemToScan> itemsToScan;
    private List<ScannedItem> scannedItems;

    private String recommendedCarton;
    private String selectedCarton;

    private Weight estimatedWeight;
    private Weight actualWeight;

    private PackingStatus status;
    private QualityCheck qualityCheck;

    private LocalDateTime startedAt;
    private LocalDateTime completedAt;

    public void scanItem(String barcode) {
        ItemToScan item = findItemByBarcode(barcode);

        if (item == null) {
            throw new UnexpectedItemException(barcode);
        }

        if (item.isScanned()) {
            throw new AlreadyScannedException(barcode);
        }

        item.markScanned();
        scannedItems.add(new ScannedItem(item, LocalDateTime.now()));

        if (allItemsScanned()) {
            status = PackingStatus.READY_FOR_CARTON;
            recommendCarton();
        }
    }

    public void selectCarton(String cartonType) {
        if (!isCartonSuitable(cartonType)) {
            throw new UnsuitableCartonException();
        }

        this.selectedCarton = cartonType;
        this.status = PackingStatus.READY_TO_PACK;

        // Calculate packing materials
        calculatePackingMaterials();
    }

    public void performQualityCheck(QualityCheckRequest request) {
        this.qualityCheck = new QualityCheck(
            request.getChecker(),
            request.getCheckpoints(),
            LocalDateTime.now()
        );

        if (qualityCheck.hasFailed()) {
            status = PackingStatus.QC_FAILED;
            handleQualityFailure();
        } else {
            status = PackingStatus.QC_PASSED;
        }
    }

    public void weighAndClose(Weight weight) {
        this.actualWeight = weight;

        // Verify weight is within tolerance
        double tolerance = 0.05; // 5%
        double difference = Math.abs(
            weight.getValue() - estimatedWeight.getValue()
        ) / estimatedWeight.getValue();

        if (difference > tolerance) {
            throw new WeightDiscrepancyException(
                estimatedWeight,
                actualWeight
            );
        }

        status = PackingStatus.READY_TO_SHIP;
        completedAt = LocalDateTime.now();

        registerEvent(new PackingCompletedEvent(this));
    }
}
```

---

##### PACK-003: Quality Control Integration
**Type**: Feature
**Priority**: P1 - High
**Estimation**: 8 points

**Description**:
Implement quality control checkpoints in packing flow.

**Acceptance Criteria**:
- [ ] Configurable QC checkpoints
- [ ] Random QC selection
- [ ] QC workflow integration
- [ ] Defect tracking
- [ ] Photo capture support
- [ ] QC metrics tracking

---

#### Sprint 2: Shipping Integration (Week 3-4)

##### PACK-004: Shipping Label Generation
**Type**: Integration
**Priority**: P0 - Critical
**Estimation**: 8 points

**Description**:
Integrate with shipping services for label generation.

**Acceptance Criteria**:
- [ ] Multi-carrier support
- [ ] Label generation API
- [ ] Label printing service
- [ ] Manifest generation
- [ ] Tracking number management
- [ ] Rate shopping

---

##### PACK-005: Cartonization Optimization
**Type**: Feature
**Priority**: P2 - Medium
**Estimation**: 13 points

**Description**:
Implement carton selection and optimization logic.

**Acceptance Criteria**:
- [ ] 3D bin packing algorithm
- [ ] Multi-box optimization
- [ ] Fragility considerations
- [ ] Weight distribution
- [ ] Cost optimization
- [ ] Sustainability metrics

---

### API Specifications

```yaml
openapi: 3.0.3
info:
  title: Pack & Ship Service API
  version: 1.0.0
  description: WES service for packing operations and shipping preparation

paths:
  /packing-sessions:
    post:
      summary: Create packing session
      operationId: createPackingSession
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreatePackingSessionRequest'
      responses:
        '201':
          description: Session created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PackingSession'

  /packing-sessions/{sessionId}:
    get:
      summary: Get packing session
      operationId: getPackingSession
      parameters:
        - name: sessionId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Session details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PackingSession'

  /packing-sessions/{sessionId}/scan:
    post:
      summary: Scan item
      operationId: scanItem
      parameters:
        - name: sessionId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                barcode:
                  type: string
      responses:
        '200':
          description: Item scanned
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ScanResponse'

  /packing-sessions/{sessionId}/carton:
    post:
      summary: Select carton
      operationId: selectCarton
      parameters:
        - name: sessionId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                cartonType:
                  type: string
      responses:
        '200':
          description: Carton selected

  /packing-sessions/{sessionId}/quality-check:
    post:
      summary: Perform quality check
      operationId: performQualityCheck
      parameters:
        - name: sessionId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/QualityCheckRequest'
      responses:
        '200':
          description: Quality check completed

  /packing-sessions/{sessionId}/weigh:
    post:
      summary: Weigh package
      operationId: weighPackage
      parameters:
        - name: sessionId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                weight:
                  type: number
                unit:
                  type: string
                  enum:
                    - KG
                    - LB
      responses:
        '200':
          description: Weight recorded

  /packing-sessions/{sessionId}/complete:
    post:
      summary: Complete packing
      operationId: completePacking
      parameters:
        - name: sessionId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Packing completed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PackingCompletionResponse'

  /shipping/labels:
    post:
      summary: Generate shipping label
      operationId: generateShippingLabel
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ShippingLabelRequest'
      responses:
        '201':
          description: Label generated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ShippingLabel'

  /shipping/rates:
    post:
      summary: Get shipping rates
      operationId: getShippingRates
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RateRequest'
      responses:
        '200':
          description: Available rates
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/ShippingRate'

  /cartons/recommend:
    post:
      summary: Get carton recommendation
      operationId: recommendCarton
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CartonRecommendationRequest'
      responses:
        '200':
          description: Carton recommendations
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CartonRecommendation'

components:
  schemas:
    PackingStatus:
      type: string
      enum:
        - CREATED
        - SCANNING
        - READY_FOR_CARTON
        - READY_TO_PACK
        - PACKING
        - QC_REQUIRED
        - QC_PASSED
        - QC_FAILED
        - READY_TO_WEIGH
        - READY_TO_SHIP
        - COMPLETED

    CreatePackingSessionRequest:
      type: object
      required:
        - orderId
        - packerId
        - stationId
      properties:
        orderId:
          type: string
        packerId:
          type: string
        stationId:
          type: string
        items:
          type: array
          items:
            type: object
            properties:
              sku:
                type: string
              quantity:
                type: integer

    PackingSession:
      type: object
      properties:
        sessionId:
          type: string
        orderId:
          type: string
        packerId:
          type: string
        stationId:
          type: string
        status:
          $ref: '#/components/schemas/PackingStatus'
        itemsToScan:
          type: array
          items:
            type: object
            properties:
              sku:
                type: string
              quantity:
                type: integer
              scanned:
                type: boolean
        recommendedCarton:
          type: string
        selectedCarton:
          type: string
        estimatedWeight:
          type: object
          properties:
            value:
              type: number
            unit:
              type: string
        actualWeight:
          type: object
          properties:
            value:
              type: number
            unit:
              type: string
        startedAt:
          type: string
          format: date-time
        completedAt:
          type: string
          format: date-time

    QualityCheckRequest:
      type: object
      required:
        - checker
        - checkpoints
      properties:
        checker:
          type: string
        checkpoints:
          type: array
          items:
            type: object
            properties:
              name:
                type: string
              passed:
                type: boolean
              notes:
                type: string
        photos:
          type: array
          items:
            type: string
            format: uri

    ShippingLabelRequest:
      type: object
      required:
        - orderId
        - carrier
        - service
        - fromAddress
        - toAddress
        - packages
      properties:
        orderId:
          type: string
        carrier:
          type: string
          enum:
            - UPS
            - FEDEX
            - USPS
            - DHL
        service:
          type: string
        fromAddress:
          $ref: '#/components/schemas/Address'
        toAddress:
          $ref: '#/components/schemas/Address'
        packages:
          type: array
          items:
            type: object
            properties:
              weight:
                type: number
              dimensions:
                type: object
                properties:
                  length:
                    type: number
                  width:
                    type: number
                  height:
                    type: number

    ShippingLabel:
      type: object
      properties:
        labelId:
          type: string
        trackingNumber:
          type: string
        carrier:
          type: string
        service:
          type: string
        labelUrl:
          type: string
          format: uri
        labelFormat:
          type: string
          enum:
            - PDF
            - ZPL
            - PNG
        cost:
          type: object
          properties:
            amount:
              type: number
            currency:
              type: string

    Address:
      type: object
      properties:
        name:
          type: string
        company:
          type: string
        street1:
          type: string
        street2:
          type: string
        city:
          type: string
        state:
          type: string
        postalCode:
          type: string
        country:
          type: string
        phone:
          type: string
        email:
          type: string
          format: email
```

---

## Common Event Schemas

### WMS Events

```json
{
  "WaveReleasedEvent": {
    "specversion": "1.0",
    "type": "com.paklog.wms.wave.released.v1",
    "source": "wave-planning-service",
    "data": {
      "waveId": "string",
      "orderIds": ["string"],
      "warehouseId": "string",
      "zone": "string",
      "priority": "string",
      "releasedAt": "datetime",
      "expectedCompletion": "datetime"
    }
  },

  "LocationConfiguredEvent": {
    "specversion": "1.0",
    "type": "com.paklog.wms.location.configured.v1",
    "source": "location-master-service",
    "data": {
      "locationId": "string",
      "type": "string",
      "capacity": {},
      "restrictions": [],
      "slottingClass": "string"
    }
  }
}
```

### WES Events

```json
{
  "TaskCompletedEvent": {
    "specversion": "1.0",
    "type": "com.paklog.wes.task.completed.v1",
    "source": "task-execution-service",
    "data": {
      "taskId": "string",
      "taskType": "string",
      "completedBy": "string",
      "completedAt": "datetime",
      "duration": "number",
      "results": {}
    }
  },

  "PickingCompletedEvent": {
    "specversion": "1.0",
    "type": "com.paklog.wes.picking.completed.v1",
    "source": "pick-execution-service",
    "data": {
      "sessionId": "string",
      "waveId": "string",
      "pickerId": "string",
      "itemsPicked": "number",
      "shortPicks": "number",
      "completedAt": "datetime"
    }
  },

  "PackingCompletedEvent": {
    "specversion": "1.0",
    "type": "com.paklog.wes.packing.completed.v1",
    "source": "pack-ship-service",
    "data": {
      "orderId": "string",
      "packages": [],
      "trackingNumbers": [],
      "completedAt": "datetime"
    }
  },

  "LicensePlateMovedEvent": {
    "specversion": "1.0",
    "type": "com.paklog.wes.lp.moved.v1",
    "source": "physical-tracking-service",
    "data": {
      "licensePlateId": "string",
      "fromLocationId": "string",
      "toLocationId": "string",
      "movedBy": "string",
      "movedAt": "datetime"
    }
  }
}
```

---

## Integration Test Suites

### End-to-End Test Example

```java
@SpringBootTest
@TestPropertySource(properties = {
    "spring.kafka.bootstrap-servers=${spring.embedded.kafka.brokers}"
})
@EmbeddedKafka(partitions = 1, topics = {
    "wms.wave.events",
    "wes.task.events",
    "wes.pick.events"
})
class WmsWesIntegrationTest {

    @Test
    void fullFulfillmentFlow() {
        // 1. Create and release wave (WMS)
        Wave wave = waveService.createWave(
            Arrays.asList("ORD-001", "ORD-002"),
            WaveStrategy.TIME_BASED
        );

        waveService.release(wave.getWaveId());

        // 2. Verify task generation (WES)
        await().atMost(5, SECONDS).until(() -> {
            List<WorkTask> tasks = taskService.findByWaveId(wave.getWaveId());
            return tasks.size() > 0;
        });

        // 3. Assign and execute pick tasks
        WorkTask pickTask = taskService.getNextTask("picker-001");
        taskService.start(pickTask.getTaskId());

        PickSession session = pickService.createSession(pickTask);
        pickService.startSession(session.getSessionId());

        // 4. Complete picking
        session.getInstructions().forEach(instruction -> {
            pickService.confirmPick(
                session.getSessionId(),
                instruction.getSku(),
                instruction.getQuantity()
            );
        });

        pickService.completeSession(session.getSessionId());

        // 5. Verify packing task creation
        await().atMost(5, SECONDS).until(() -> {
            WorkTask packTask = taskService.findByTypeAndReference(
                TaskType.PACK,
                "ORD-001"
            );
            return packTask != null;
        });

        // 6. Execute packing
        PackingSession packSession = packService.createSession("ORD-001");
        packService.scanAllItems(packSession);
        packService.selectCarton(packSession, "SMALL-BOX");
        packService.weighAndClose(packSession, new Weight(5.2, "KG"));

        // 7. Verify order completion
        Order order = orderService.getOrder("ORD-001");
        assertThat(order.getStatus()).isEqualTo(OrderStatus.PACKED);
    }
}
```

---

## Performance Requirements

### Service-Level Performance Targets

| Service | Operation | Target Latency (p95) | Throughput |
|---------|-----------|---------------------|------------|
| Wave Planning | Wave creation | <500ms | 100/min |
| Wave Planning | Wave release | <1s | 50/min |
| Task Execution | Task assignment | <100ms | 1000/min |
| Task Execution | Task update | <50ms | 5000/min |
| Location Master | Location query | <50ms | 10000/min |
| Physical Tracking | Movement update | <100ms | 2000/min |
| Pick Execution | Path optimization | <500ms | 100/min |
| Pick Execution | Pick confirmation | <100ms | 3000/min |
| Pack & Ship | Scan validation | <50ms | 5000/min |
| Pack & Ship | Label generation | <2s | 100/min |

---

## Deployment Strategy

### Kubernetes Deployment Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wave-planning-service
  namespace: wms
spec:
  replicas: 3
  selector:
    matchLabels:
      app: wave-planning-service
  template:
    metadata:
      labels:
        app: wave-planning-service
        version: v1.0.0
    spec:
      containers:
      - name: wave-planning
        image: paklog/wave-planning-service:1.0.0
        ports:
        - containerPort: 8080
        env:
        - name: SPRING_PROFILES_ACTIVE
          value: "production"
        - name: MONGODB_URI
          valueFrom:
            secretKeyRef:
              name: mongodb-secret
              key: uri
        - name: KAFKA_BOOTSTRAP_SERVERS
          value: "kafka-cluster:9092"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /actuator/health/liveness
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /actuator/health/readiness
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: wave-planning-service
  namespace: wms
spec:
  selector:
    app: wave-planning-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP
```

---

## Monitoring & Alerting

### Prometheus Metrics

```yaml
metrics:
  wms:
    wave_planning:
      - wave_creation_duration_seconds
      - wave_release_duration_seconds
      - waves_per_hour
      - wave_size_distribution
      - wave_completion_rate

    location_master:
      - location_queries_per_second
      - location_update_duration_seconds
      - slotting_optimization_duration_seconds

  wes:
    task_execution:
      - task_creation_rate
      - task_assignment_duration_seconds
      - task_completion_rate
      - queue_depth_by_type
      - worker_utilization

    pick_execution:
      - picks_per_hour_per_worker
      - pick_accuracy_rate
      - path_optimization_duration_seconds
      - short_pick_rate

    physical_tracking:
      - movements_per_hour
      - license_plate_creation_rate
      - location_state_updates_per_second
```

### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "WMS/WES Service Metrics",
    "panels": [
      {
        "title": "Wave Release Rate",
        "targets": [
          {
            "expr": "rate(wave_release_total[5m])"
          }
        ]
      },
      {
        "title": "Task Assignment Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, task_assignment_duration_seconds)"
          }
        ]
      },
      {
        "title": "Pick Accuracy",
        "targets": [
          {
            "expr": "1 - (rate(pick_errors_total[1h]) / rate(picks_total[1h]))"
          }
        ]
      }
    ]
  }
}
```

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-01-18 | Architecture Team | Initial detailed plan |

---

**END OF DOCUMENT**