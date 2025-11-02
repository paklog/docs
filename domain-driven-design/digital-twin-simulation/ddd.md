# Digital Twin & Simulation - Domain-Driven Design

## Bounded Context: Warehouse Simulation & Predictive Optimization

The Digital Twin & Simulation service provides a virtual replica of the warehouse for scenario testing, capacity planning, and predictive analytics. It enables risk-free experimentation and optimization of warehouse operations.

## Domain Model

### Aggregates

#### SimulationScenario (Aggregate Root)
**Purpose**: Defines the parameters and configuration for a what-if simulation.

**Properties**:
```java
public class SimulationScenario {
    private ScenarioId scenarioId;
    private String name;
    private String description;
    private SimulationParameters parameters;
    private WarehouseState initialState;
    private List<SimulationRun> runs;
}
```

#### SimulationRun (Aggregate Root)
**Purpose**: Represents a single execution of a simulation scenario, capturing its results and metrics.

**Properties**:
```java
public class SimulationRun {
    private RunId runId;
    private ScenarioId scenarioId;
    private RunStatus status;
    private LocalDateTime startTime;
    private LocalDateTime endTime;
    private SimulationResult results;
    private List<SimulatedEvent> eventLog;
}
```

### Value Objects
- **SimulationParameters**: Input variables for a scenario (e.g., order volume, worker count, robot speed).
- **WarehouseState**: A snapshot of the digital twin's state at a point in time.
- **SimulationResult**: The outcome of a simulation, including KPIs like throughput, utilization, and bottleneck analysis.
- **SimulatedEvent**: An event that occurred within the simulation timeline.

### Domain Services
- **DiscreteEventSimulator**: The core engine that runs the simulation based on a scenario.
- **TwinSynchronizer**: Consumes real-world events to keep the digital twin's state up-to-date.
- **ScenarioAnalyzer**: Compares results from different simulation runs to provide insights.

### Domain Events

#### Events Published
- `SimulationStarted`
- `SimulationCompleted`
- `SimulationFailed`
- `ScenarioAnalysisComplete`
- `TwinStateUpdated`

#### Events Consumed
- Consumes events from nearly all other services (e.g., `OrderCreated`, `TaskCompleted`, `AssetMoved`) to update the digital twin's state.

### Integration
- **Upstream**: Consumes event streams from the entire PakLog ecosystem to build its state.
- **Downstream**: Publishes simulation results and predictive insights to the Performance Intelligence and Predictive Analytics services.
- **Pattern**: The digital twin is a real-time projection of the state of the entire warehouse.

## Business Rules
1.  **Synchronization Latency**: The digital twin state must not be more than 2 seconds behind the real-world state.
2.  **Scenario Validation**: Simulation scenarios must be validated for logical consistency before execution.
3.  **Simulation Fidelity**: Simulation models must be calibrated to achieve at least 95% accuracy against historical data.
4.  **Resource Limits**: Simulations are resource-intensive and are queued to run during off-peak hours unless prioritized.
