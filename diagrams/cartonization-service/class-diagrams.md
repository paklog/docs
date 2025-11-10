# Cartonization Service - Class Diagrams

## Domain Model Overview

```mermaid
classDiagram
    class CartonizationRequest {
        <<Aggregate Root>>
        -String requestId
        -String orderId
        -List~Item~ items
        -ShippingConstraints constraints
        -PackingPreferences preferences
        -RequestStatus status
        -List~CartonizationResult~ results
        -DateTime requestedAt
        -DateTime completedAt
        +addItem(item) void
        +setConstraints(constraints) void
        +execute() CartonizationResult
        +optimize() void
        +validate() ValidationResult
    }

    class Item {
        <<Entity>>
        -String itemId
        -String skuCode
        -Dimensions dimensions
        -Weight weight
        -int quantity
        -Fragility fragility
        -StackabilityRules stackability
        -OrientationConstraints orientation
        -List~SpecialRequirement~ requirements
        +canStack() boolean
        +canRotate() boolean
        +requiresPadding() boolean
    }

    class Carton {
        <<Entity>>
        -String cartonId
        -String cartonType
        -Dimensions innerDimensions
        -Dimensions outerDimensions
        -Weight maxWeight
        -Weight tareWeight
        -Volume volume
        -Money cost
        -CartonMaterial material
        -List~String~ compatibleItems
        +canFit(items) boolean
        +calculateUtilization(items) Percentage
        +isWeightLimitExceeded(items) boolean
    }

    class CartonizationResult {
        <<Value Object>>
        -String resultId
        -List~PackedCarton~ cartons
        -PackingEfficiency efficiency
        -Money totalCost
        -List~UnpackedItem~ unpackedItems
        +getCartonCount() int
        +getTotalWeight() Weight
        +getTotalVolume() Volume
        +isComplete() boolean
    }

    class PackedCarton {
        <<Entity>>
        -Carton carton
        -List~PackedItem~ items
        -PackingArrangement arrangement
        -Weight totalWeight
        -UtilizationMetrics utilization
        -VoidFillRequirement voidFill
        +addItem(item, position) void
        +getFilledVolume() Volume
        +getRemainingCapacity() Capacity
    }

    CartonizationRequest "1" --> "*" Item : contains
    CartonizationRequest "1" --> "1" CartonizationResult : produces
    CartonizationResult "1" --> "*" PackedCarton : contains
    PackedCarton "1" --> "1" Carton : uses
    PackedCarton "1" --> "*" Item : packs
```

## Packing Algorithms

```mermaid
classDiagram
    class PackingAlgorithm {
        <<Strategy Interface>>
        +pack(items, cartons) PackingResult
        +optimize(result) OptimizedResult
    }

    class ThreeDimensionalBinPacking {
        <<Strategy>>
        -OrientationStrategy orientation
        -StabilityChecker stability
        +pack(items, cartons) PackingResult
        -findBestPosition(item, carton) Position3D
        -checkCollision(item, position) boolean
        -rotateItem(item) List~Orientation~
        -calculateStability(arrangement) StabilityScore
    }

    class FirstFitDecreasing {
        <<Strategy>>
        +pack(items, cartons) PackingResult
        -sortByVolume(items) List~Item~
        -findFirstFit(item, cartons) Carton
        -createNewCarton(item) Carton
    }

    class BestFitAlgorithm {
        <<Strategy>>
        -WasteCalculator wasteCalculator
        +pack(items, cartons) PackingResult
        -findBestFit(item, cartons) Carton
        -calculateWaste(item, carton) double
        -minimizeDeadSpace(arrangement) void
    }

    class GeneticAlgorithmPacking {
        <<Strategy>>
        -PopulationSize populationSize
        -MutationRate mutationRate
        -Generations generations
        +pack(items, cartons) PackingResult
        -createInitialPopulation() Population
        -crossover(parent1, parent2) Chromosome
        -mutate(chromosome) void
        -fitness(solution) double
        -selectBest(population) Solution
    }

    class LayerBuildingAlgorithm {
        <<Strategy>>
        -LayerStrategy layerStrategy
        +pack(items, cartons) PackingResult
        -buildLayers(items) List~Layer~
        -stackLayers(layers, carton) Arrangement
        -optimizeLayerOrder(layers) List~Layer~
    }

    PackingAlgorithm <|.. ThreeDimensionalBinPacking
    PackingAlgorithm <|.. FirstFitDecreasing
    PackingAlgorithm <|.. BestFitAlgorithm
    PackingAlgorithm <|.. GeneticAlgorithmPacking
    PackingAlgorithm <|.. LayerBuildingAlgorithm
```

## Optimization Engine

```mermaid
classDiagram
    class CartonizationOptimizer {
        <<Domain Service>>
        -OptimizationStrategy strategy
        -CostCalculator costCalculator
        -ConstraintValidator validator
        +optimize(request) OptimizedResult
        +minimizeCartons(items) PackingPlan
        +minimizeCost(items) PackingPlan
        +maximizeUtilization(items) PackingPlan
        -evaluateSolution(solution) Score
        -applyConstraints(solution) void
    }

    class MultiObjectiveOptimizer {
        <<Service>>
        -List~ObjectiveFunction~ objectives
        -ParetoOptimizer pareto
        +optimize(items, objectives) ParetoFront
        -evaluateObjectives(solution) List~Score~
        -findParetoOptimal(solutions) List~Solution~
        -selectBestCompromise(pareto) Solution
    }

    class ConstraintValidator {
        <<Service>>
        -List~Constraint~ constraints
        +validate(solution) ValidationResult
        -checkWeightConstraints(carton) boolean
        -checkDimensionConstraints(carton) boolean
        -checkOrientationConstraints(items) boolean
        -checkFragilityRules(arrangement) boolean
        -checkStackingRules(items) boolean
    }

    class CostOptimizer {
        <<Service>>
        -RateCalculator rateCalculator
        -CarrierRates carrierRates
        +calculateShippingCost(cartons) Money
        +optimizeForCost(items) PackingPlan
        -selectOptimalCartonMix(items) List~Carton~
        -considerDimensionalWeight(carton) Weight
    }

    class VoidFillOptimizer {
        <<Service>>
        -MaterialLibrary materials
        +calculateVoidFill(carton) VoidFillPlan
        +selectFillMaterial(voidVolume, items) Material
        +minimizeFillCost(carton) FillStrategy
        +ensureProtection(fragileItems) ProtectionPlan
    }

    CartonizationOptimizer --> MultiObjectiveOptimizer : uses
    CartonizationOptimizer --> ConstraintValidator : validates
    CartonizationOptimizer --> CostOptimizer : optimizes cost
    CartonizationOptimizer --> VoidFillOptimizer : minimizes void
```

## Carton Selection and Management

```mermaid
classDiagram
    class CartonSelector {
        <<Domain Service>>
        -CartonLibrary library
        -SelectionStrategy strategy
        -CompatibilityChecker checker
        +selectCartons(items) List~Carton~
        +recommendCarton(items) Carton
        +getAlternatives(carton) List~Carton~
        -filterCompatible(items, cartons) List~Carton~
        -rankCartons(cartons, items) List~RankedCarton~
    }

    class CartonLibrary {
        <<Repository>>
        -Map~String, Carton~ cartons
        -List~CartonCategory~ categories
        +addCarton(carton) void
        +removeCarton(cartonId) void
        +findByDimensions(min, max) List~Carton~
        +findByWeight(maxWeight) List~Carton~
        +getStandardCartons() List~Carton~
        +getCustomCartons() List~Carton~
    }

    class CartonInventory {
        <<Entity>>
        -Map~String, Integer~ availability
        -Map~String, Location~ locations
        -ReorderRules reorderRules
        +checkAvailability(cartonId) int
        +reserve(cartonId, quantity) void
        +consume(cartonId, quantity) void
        +needsReorder(cartonId) boolean
    }

    class CustomCartonDesigner {
        <<Service>>
        -DimensionCalculator calculator
        -MaterialSelector selector
        +designCustomCarton(items) Carton
        +calculateOptimalDimensions(items) Dimensions
        +selectMaterial(requirements) Material
        +estimateCost(design) Money
    }

    CartonSelector --> CartonLibrary : queries
    CartonSelector --> CartonInventory : checks
    CartonSelector --> CustomCartonDesigner : may use
```

## Simulation and Testing

```mermaid
classDiagram
    class PackingSimulator {
        <<Service>>
        -SimulationEngine engine
        -Visualizer3D visualizer
        +simulate(packingPlan) SimulationResult
        +visualize(arrangement) Visualization3D
        +testStability(arrangement) StabilityTest
        +animatePacking(steps) Animation
    }

    class SimulationResult {
        <<Value Object>>
        -List~SimulatedCarton~ cartons
        -List~Issue~ issues
        -PerformanceMetrics metrics
        -StabilityAnalysis stability
        +hasIssues() boolean
        +getRecommendations() List~Recommendation~
    }

    class StressTestEngine {
        <<Service>>
        -PhysicsEngine physics
        -LoadTester loadTester
        +testCompression(carton) CompressionResult
        +testVibration(carton) VibrationResult
        +testDropImpact(carton, height) ImpactResult
        +testStackingStrength(stack) StrengthResult
    }

    class PackingValidator {
        <<Service>>
        -RuleEngine rules
        -ComplianceChecker compliance
        +validate(packingPlan) ValidationReport
        +checkCompliance(carton) ComplianceResult
        +verifyShippingRequirements(plan) boolean
    }

    PackingSimulator --> SimulationResult : produces
    PackingSimulator --> StressTestEngine : uses
    PackingSimulator --> PackingValidator : validates
```

## Analytics and Reporting

```mermaid
classDiagram
    class CartonizationAnalytics {
        <<Analytics Service>>
        -MetricsCollector collector
        -TrendAnalyzer trends
        +analyzeEfficiency(period) EfficiencyReport
        +calculateKPIs() KPIReport
        +identifyOptimizations() List~Optimization~
        +compareAlgorithms(algorithms) Comparison
    }

    class PerformanceMetrics {
        <<Entity>>
        -double utilizationRate
        -int cartonsUsed
        -Money shippingCost
        -Duration processingTime
        -double voidPercentage
        -List~AlgorithmMetric~ algorithmMetrics
        +calculateEfficiency() double
        +getCostPerPackage() Money
    }

    class HistoricalAnalysis {
        <<Service>>
        -DataWarehouse warehouse
        -MLPredictor predictor
        +analyzeTrends(period) TrendReport
        +predictCartonUsage(forecast) UsagePrediction
        +identifyPatterns() List~Pattern~
        +recommendInventory() InventoryRecommendation
    }

    class OptimizationRecommender {
        <<Service>>
        -MachineLearning ml
        -RuleEngine rules
        +recommendSettings(context) Settings
        +suggestAlgorithm(items) Algorithm
        +predictOutcome(plan) Prediction
        +learnFromResults(results) void
    }

    CartonizationAnalytics --> PerformanceMetrics : collects
    CartonizationAnalytics --> HistoricalAnalysis : uses
    CartonizationAnalytics --> OptimizationRecommender : consults
```

## Integration and Events

```mermaid
classDiagram
    class CartonizationEvent {
        <<Abstract Event>>
        -String eventId
        -String requestId
        -DateTime occurredAt
        +getEventType() String
    }

    class CartonizationCompletedEvent {
        <<Event>>
        -CartonizationResult result
        -Duration processingTime
        +getEventType() String
    }

    class CartonizationFailedEvent {
        <<Event>>
        -String reason
        -List~String~ failedItems
        +getEventType() String
    }

    class CartonSelectionChangedEvent {
        <<Event>>
        -String oldCartonId
        -String newCartonId
        -String reason
        +getEventType() String
    }

    class CartonizationIntegrationService {
        <<Integration Service>>
        -OrderServiceClient orderService
        -InventoryServiceClient inventory
        -ShippingServiceClient shipping
        +fetchOrderItems(orderId) List~Item~
        +validateInventory(items) boolean
        +calculateShippingRates(cartons) List~Rate~
        +updatePackingInstructions(orderId, plan) void
    }

    CartonizationEvent <|-- CartonizationCompletedEvent
    CartonizationEvent <|-- CartonizationFailedEvent
    CartonizationEvent <|-- CartonSelectionChangedEvent
    CartonizationIntegrationService ..> CartonizationEvent : publishes
```