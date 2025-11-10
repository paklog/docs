# Pack & Ship Service - Class Diagrams

## Domain Model Overview

```mermaid
classDiagram
    class PackingSession {
        <<Aggregate Root>>
        -String sessionId
        -String packerId
        -String stationId
        -String orderId
        -SessionStatus status
        -List~PackItem~ itemsToPack
        -Carton selectedCarton
        -PackingMaterials materials
        -Weight actualWeight
        -Dimensions actualDimensions
        -QualityCheck qualityCheck
        -ShippingLabel shippingLabel
        -DateTime startTime
        -DateTime endTime
        -PackMetrics metrics
        +start() void
        +scanItem(barcode) ScanResult
        +selectCarton(cartonId) void
        +addPackingMaterial(material) void
        +weighPackage() Weight
        +performQualityCheck() QCResult
        +generateLabel() ShippingLabel
        +complete() void
        +cancel(reason) void
        +validatePacking() ValidationResult
    }

    class PackItem {
        <<Entity>>
        -String itemId
        -String skuCode
        -String description
        -int quantity
        -int packedQuantity
        -Dimensions dimensions
        -Weight weight
        -FragilityLevel fragility
        -List~PackingRequirement~ requirements
        -ItemStatus status
        +scan() void
        +pack(quantity) void
        +markDamaged(reason) void
        +requiresSpecialHandling() boolean
    }

    class Carton {
        <<Entity>>
        -String cartonId
        -CartonType type
        -Dimensions innerDimensions
        -Dimensions outerDimensions
        -Weight maxWeight
        -Weight tareWeight
        -Money cost
        -List~String~ compatibleItems
        -boolean isReusable
        +canFit(items) boolean
        +calculateUtilization(items) Percentage
        +isWeightLimitExceeded(weight) boolean
    }

    class PackingMaterials {
        <<Value Object>>
        -List~Material~ materials
        -VoidFillType voidFill
        -double voidFillAmount
        -List~ProtectiveMaterial~ protective
        -Money totalCost
        +addMaterial(material) void
        +calculateVoidFill(carton, items) double
        +getCost() Money
    }

    class ShippingLabel {
        <<Entity>>
        -String trackingNumber
        -Carrier carrier
        -ServiceLevel service
        -Address fromAddress
        -Address toAddress
        -Weight packageWeight
        -Dimensions packageDimensions
        -Money shippingCost
        -byte[] labelImage
        -String labelFormat
        +generate() byte[]
        +print(printer) void
        +void voidLabel() void
    }

    class QualityCheck {
        <<Entity>>
        -String qcId
        -List~QCCheckpoint~ checkpoints
        -QCStatus status
        -String performedBy
        -DateTime performedAt
        -List~QCIssue~ issues
        -byte[] photoEvidence
        +perform() QCResult
        +recordIssue(issue) void
        +approve() void
        +reject(reason) void
    }

    PackingSession "1" --> "*" PackItem : contains
    PackingSession "1" --> "1" Carton : uses
    PackingSession "1" --> "1" PackingMaterials : uses
    PackingSession "1" --> "1" ShippingLabel : generates
    PackingSession "1" --> "1" QualityCheck : includes
```

## Cartonization and Optimization

```mermaid
classDiagram
    class CartonizationEngine {
        <<Domain Service>>
        -PackingAlgorithm algorithm
        -CartonLibrary cartonLibrary
        -CostOptimizer costOptimizer
        +selectOptimalCarton(items) CartonRecommendation
        +optimizePacking(items, cartons) PackingPlan
        +calculateDimensions(items) Dimensions
        -runBinPacking(items, carton) PackingResult
        -evaluateFit(items, carton) FitScore
    }

    class PackingAlgorithm {
        <<Strategy Interface>>
        +pack(items, container) PackingResult
    }

    class FirstFitDecreasing {
        <<Strategy>>
        +pack(items, container) PackingResult
        -sortBySize(items) List~Item~
        -placeItem(item, container) Placement
    }

    class BestFitAlgorithm {
        <<Strategy>>
        +pack(items, container) PackingResult
        -findBestPosition(item, container) Position
        -calculateWaste(placement) double
    }

    class ThreeDimensionalPacking {
        <<Strategy>>
        -RotationStrategy rotation
        +pack(items, container) PackingResult
        -buildLayrs(items) List~Layer~
        -optimizeOrientation(item) Orientation
        -checkStability(placement) boolean
    }

    class VoidFillCalculator {
        <<Service>>
        -DensityCalculator density
        +calculateVoidFill(carton, items) VoidFillRequirement
        +selectFillMaterial(requirement) Material
        +estimateAmount(volume) Quantity
        +calculateCost(material, amount) Money
    }

    class PackingOptimizer {
        <<Domain Service>>
        -SimulationEngine simulator
        +optimizeMultiBox(items) List~PackingPlan~
        +minimizeCartons(items) PackingStrategy
        +balanceWeight(items, cartons) void
        -simulatePacking(plan) SimulationResult
    }

    CartonizationEngine --> PackingAlgorithm : uses
    PackingAlgorithm <|.. FirstFitDecreasing
    PackingAlgorithm <|.. BestFitAlgorithm
    PackingAlgorithm <|.. ThreeDimensionalPacking
    CartonizationEngine --> VoidFillCalculator : uses
    CartonizationEngine --> PackingOptimizer : delegates
```

## Shipping Integration

```mermaid
classDiagram
    class ShippingService {
        <<Domain Service>>
        -Map~String, CarrierAdapter~ carriers
        -RateEngine rateEngine
        -LabelGenerator labelGenerator
        +calculateRates(shipment) List~Rate~
        +createShipment(order, package) Shipment
        +generateLabel(shipment) ShippingLabel
        +trackShipment(trackingNumber) TrackingInfo
        +voidShipment(shipmentId) void
        -selectCarrier(shipment) Carrier
    }

    class CarrierAdapter {
        <<Adapter Interface>>
        +getRates(request) List~Rate~
        +createShipment(details) ShipmentResponse
        +generateLabel(shipment) LabelData
        +track(trackingNumber) TrackingInfo
        +void(shipmentId) VoidResponse
    }

    class FedExAdapter {
        <<Adapter>>
        -FedExClient client
        -CredentialManager credentials
        +getRates(request) List~Rate~
        +createShipment(details) ShipmentResponse
        +generateLabel(shipment) LabelData
    }

    class UPSAdapter {
        <<Adapter>>
        -UPSWebService service
        -AuthToken token
        +getRates(request) List~Rate~
        +createShipment(details) ShipmentResponse
        +generateLabel(shipment) LabelData
    }

    class USPSAdapter {
        <<Adapter>>
        -USPSApi api
        +getRates(request) List~Rate~
        +createShipment(details) ShipmentResponse
        +generateLabel(shipment) LabelData
    }

    class ManifestGenerator {
        <<Service>>
        -List~Shipment~ dailyShipments
        +generateManifest(date) Manifest
        +closeManifest(manifestId) void
        +getPickupSchedule() Schedule
        +consolidateShipments(shipments) ConsolidatedManifest
    }

    ShippingService --> CarrierAdapter : uses
    CarrierAdapter <|.. FedExAdapter
    CarrierAdapter <|.. UPSAdapter
    CarrierAdapter <|.. USPSAdapter
    ShippingService --> ManifestGenerator : coordinates
```

## Quality Control System

```mermaid
classDiagram
    class QualityControlService {
        <<Domain Service>>
        -QCRules rules
        -InspectionCriteria criteria
        -ImageAnalyzer imageAnalyzer
        +performQualityCheck(package) QCResult
        +validatePacking(session) ValidationResult
        +analyzePackageImage(image) ImageAnalysis
        -checkCompliance(package) ComplianceResult
    }

    class QCCheckpoint {
        <<Entity>>
        -String checkpointId
        -String name
        -CheckpointType type
        -boolean mandatory
        -List~QCCriterion~ criteria
        -PassFailStatus status
        +evaluate(package) CheckResult
        +recordResult(result) void
    }

    class PackageInspector {
        <<Service>>
        -List~InspectionRule~ rules
        -DamageDetector damageDetector
        +inspectPackage(package) InspectionReport
        +checkForDamage(items) List~Damage~
        +validateContents(package) boolean
        +verifySealing(package) SealingQuality
    }

    class PhotoDocumentation {
        <<Entity>>
        -String documentId
        -String packageId
        -List~Photo~ photos
        -PhotoType type
        -DateTime capturedAt
        -String capturedBy
        +addPhoto(photo) void
        +validate() boolean
        +compress() void
        +archive() void
    }

    class ComplianceValidator {
        <<Service>>
        -RegulationLibrary regulations
        -HazmatChecker hazmat
        +validateCompliance(shipment) ComplianceResult
        +checkHazmat(items) HazmatStatus
        +validateInternational(shipment) CustomsCompliance
        +generateDocuments(shipment) List~Document~
    }

    QualityControlService --> QCCheckpoint : executes
    QualityControlService --> PackageInspector : uses
    QualityControlService --> PhotoDocumentation : creates
    QualityControlService --> ComplianceValidator : validates
```

## Packing Station Management

```mermaid
classDiagram
    class PackingStation {
        <<Entity>>
        -String stationId
        -StationType type
        -Location location
        -List~Equipment~ equipment
        -StationStatus status
        -Operator assignedOperator
        -Queue~Order~ orderQueue
        -StationMetrics metrics
        +activate() void
        +deactivate() void
        +assignOperator(operator) void
        +queueOrder(order) void
        +processNext() PackingSession
    }

    class StationEquipment {
        <<Entity>>
        -String equipmentId
        -EquipmentType type
        -EquipmentStatus status
        -CalibrationStatus calibration
        +use() void
        +calibrate() void
        +reportIssue(issue) void
    }

    class Scale {
        <<Entity>>
        -String scaleId
        -WeightRange range
        -Precision precision
        -CalibrationDate lastCalibration
        +weigh() Weight
        +tare() void
        +calibrate() CalibrationResult
    }

    class LabelPrinter {
        <<Entity>>
        -String printerId
        -PrinterType type
        -PrinterStatus status
        -MediaType currentMedia
        -int labelCount
        +print(label) void
        +checkMedia() MediaStatus
        +reportJam() void
    }

    class Scanner {
        <<Entity>>
        -String scannerId
        -ScannerType type
        -List~BarcodeFormat~ supportedFormats
        +scan() ScanResult
        +configure(settings) void
    }

    PackingStation "1" --> "*" StationEquipment : has
    StationEquipment <|-- Scale
    StationEquipment <|-- LabelPrinter
    StationEquipment <|-- Scanner
```

## Command and Event Handling

```mermaid
classDiagram
    class StartPackingCommand {
        <<Command>>
        -String orderId
        -String packerId
        -String stationId
        +validate() ValidationResult
    }

    class CompletePackingCommand {
        <<Command>>
        -String sessionId
        -PackingResult result
        -QCResult qualityCheck
        +validate() ValidationResult
    }

    class GenerateLabelCommand {
        <<Command>>
        -String sessionId
        -CarrierCode carrier
        -ServiceLevel service
        +validate() ValidationResult
    }

    class PackingEvent {
        <<Abstract Event>>
        -String eventId
        -String sessionId
        -DateTime occurredAt
        +getEventType() String
    }

    class PackingStartedEvent {
        <<Event>>
        -String orderId
        -String packerId
        -String stationId
        +getEventType() String
    }

    class ItemPackedEvent {
        <<Event>>
        -String itemId
        -int quantity
        -String cartonId
        +getEventType() String
    }

    class PackingCompletedEvent {
        <<Event>>
        -String trackingNumber
        -Weight finalWeight
        -ShippingCost cost
        +getEventType() String
    }

    class QualityCheckFailedEvent {
        <<Event>>
        -List~QCIssue~ issues
        -String failureReason
        +getEventType() String
    }

    PackingEvent <|-- PackingStartedEvent
    PackingEvent <|-- ItemPackedEvent
    PackingEvent <|-- PackingCompletedEvent
    PackingEvent <|-- QualityCheckFailedEvent
```

## Performance Analytics

```mermaid
classDiagram
    class PackingAnalytics {
        <<Analytics Service>>
        -MetricsCollector collector
        -PerformanceAnalyzer analyzer
        +analyzePackingEfficiency(period) EfficiencyReport
        +calculatePackRate(operator) PackRate
        +identifyBottlenecks() List~Bottleneck~
        +compareStations(stations) Comparison
    }

    class PackMetrics {
        <<Entity>>
        -String sessionId
        -int itemsPacked
        -Duration packTime
        -int cartonUsed
        -double fillRate
        -Money materialCost
        -Money shippingCost
        -int qualityIssues
        +calculateEfficiency() double
        +calculateCostPerPackage() Money
    }

    class CartonUtilizationAnalyzer {
        <<Service>>
        -HistoricalData history
        +analyzeUtilization(period) UtilizationReport
        +identifyOversizedCartons() List~Waste~
        +recommendOptimization() List~Recommendation~
    }

    PackingAnalytics --> PackMetrics : analyzes
    PackingAnalytics --> CartonUtilizationAnalyzer : uses
```