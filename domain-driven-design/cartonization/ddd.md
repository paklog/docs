# Cartonization Service - Domain Architecture & Business Capabilities

## Service Overview

The Cartonization Service is a critical component of the PakLog fulfillment ecosystem, responsible for optimizing shipment packaging through advanced 3D bin-packing algorithms. It minimizes shipping costs, reduces material waste, and ensures optimal space utilization.

**Architecture Pattern**: Hexagonal Architecture (Ports & Adapters)
**Technology Stack**: Spring Boot 3.2, MongoDB, Apache Kafka, Redis
**Integration Pattern**: Event-Driven Architecture with CloudEvents

---

## Domain Model & Bounded Context

### Bounded Context: Cartonization

The Cartonization bounded context encompasses all aspects of determining optimal packaging solutions for shipments.

#### Context Boundaries

**Responsibilities (What's IN)**:
- Calculate optimal packing solutions using 3D bin-packing algorithms
- Manage carton type catalog and specifications
- Select appropriate cartons based on items and constraints
- Optimize multi-carton solutions for large orders
- Publish packing solution events for downstream consumption
- Cache and optimize packing calculations for performance

**External Dependencies (What's OUT)**:
- Product dimensions and weights (Product Catalog context)
- Order items requiring packing (Order Management context)
- Actual packing execution (Warehouse Operations context)
- Carrier weight brackets and restrictions (Shipment context)

#### Ubiquitous Language

**Core Domain Terms**:

- **Packing Solution**: The optimal arrangement of items within one or more cartons
- **Carton Type**: A specific box/container specification with dimensions and capacity
- **Bin Packing**: Algorithm for placing items into containers with minimal waste
- **Space Utilization**: Percentage of carton volume occupied by items
- **Dimensional Weight**: Calculated weight based on package dimensions
- **Multi-Carton Solution**: Distribution of items across multiple cartons
- **Carton Selection Strategy**: Business rules for choosing optimal carton
- **Void Fill**: Empty space in carton requiring packing materials

---

## Subdomain Classification

### Core Domain: Packing Optimization

**Strategic Importance**: HIGH - Core competitive differentiator

This is the heart of the cartonization service and provides significant business value through:
- Cost reduction via optimal carton selection
- Sustainability through waste reduction
- Operational efficiency through automation

**Subdomains**:

#### 1. **3D Bin-Packing Computation** (Core)
- **Complexity**: High - Advanced algorithms
- **Strategic Value**: High - Competitive advantage
- **Volatility**: Low - Stable algorithms with incremental improvements
- **Business Differentiation**: PRIMARY differentiator
- **Investment Priority**: High - Continuous optimization needed

#### 2. **Carton Catalog Management** (Supporting)
- **Complexity**: Low - CRUD operations
- **Strategic Value**: Medium - Necessary but not differentiating
- **Volatility**: Medium - Carton types change periodically
- **Business Differentiation**: Standard capability
- **Investment Priority**: Medium - Maintain and enhance as needed

#### 3. **Performance Optimization** (Supporting)
- **Complexity**: Medium - Caching and async processing
- **Strategic Value**: High - Enables real-time operations
- **Volatility**: Low - Infrastructure concern
- **Business Differentiation**: Operational enabler
- **Investment Priority**: High - Critical for scale

---

## Domain Model

### Aggregates

#### 1. PackingSolution (Aggregate Root)

**Description**: Represents the complete solution for packing a set of items, including all selected cartons and item placements.

```java
@AggregateRoot
public class PackingSolution {
    private String solutionId;
    private String orderId;
    private List<CartonAssignment> cartonAssignments;
    private UtilizationMetrics utilizationMetrics;
    private BigDecimal totalCost;
    private SolutionStatus status;
    private LocalDateTime calculatedAt;

    // Business methods
    public void addCartonAssignment(CartonAssignment assignment);
    public BigDecimal calculateTotalCost();
    public double calculateAverageUtilization();
    public boolean meetsBusinessRules();
}
```

**Invariants**:
- At least one carton assignment required
- All items must be assigned to a carton
- Total item volume ≤ total carton volume
- Total item weight ≤ total carton weight capacity

**Domain Events**:
- `PackingSolutionCalculatedEvent`
- `SolutionValidatedEvent`
- `SolutionAppliedEvent`

---

#### 2. Carton (Aggregate Root)

**Description**: Represents a carton type available for packing with specifications and constraints.

```java
@AggregateRoot
public class Carton {
    private String cartonTypeId;
    private String name;
    private Dimensions internalDimensions;
    private Dimensions externalDimensions;
    private Weight maxWeight;
    private BigDecimal cost;
    private CartonAttributes attributes;
    private boolean active;

    // Business methods
    public boolean canAccommodate(List<Item> items);
    public double calculateUtilization(List<Item> items);
    public boolean isHeavyDuty();
    public boolean supportsFragileItems();
}
```

**Invariants**:
- Internal dimensions < external dimensions
- Max weight > 0
- Cost ≥ 0
- Unique carton type ID

**Domain Events**:
- `CartonTypeCreatedEvent`
- `CartonTypeUpdatedEvent`
- `CartonTypeDeprecatedEvent`

---

### Entities

#### CartonAssignment

**Description**: Represents the assignment of items to a specific carton within a packing solution.

```java
@Entity
public class CartonAssignment {
    private String assignmentId;
    private String cartonTypeId;
    private List<ItemPlacement> itemPlacements;
    private double utilizationPercentage;
    private BigDecimal cartonCost;

    public void addItemPlacement(ItemPlacement placement);
    public boolean hasCapacityFor(Item item);
    public Volume remainingVolume();
}
```

---

#### ItemPlacement

**Description**: Represents the specific placement of an item within a carton.

```java
@Entity
public class ItemPlacement {
    private String sku;
    private int quantity;
    private Position position; // 3D coordinates
    private Orientation orientation; // rotation
    private Volume occupiedVolume;
}
```

---

### Value Objects

#### Dimensions

```java
@ValueObject
public class Dimensions {
    private BigDecimal length;
    private BigDecimal width;
    private BigDecimal height;
    private DimensionUnit unit;

    public Volume calculateVolume();
    public boolean fitsWithin(Dimensions container);
    public DimensionalWeight calculateDimensionalWeight(int dimFactor);
}
```

#### UtilizationMetrics

```java
@ValueObject
public class UtilizationMetrics {
    private double spaceUtilization; // percentage
    private double weightUtilization; // percentage
    private int numberOfCartons;
    private BigDecimal totalCost;
    private BigDecimal costPerItem;
}
```

#### CartonAttributes

```java
@ValueObject
public class CartonAttributes {
    private boolean heavyDuty;
    private boolean fragileApproved;
    private boolean hazmatApproved;
    private boolean insulated;
    private String material; // cardboard, plastic, etc.
}
```

---

## Domain Services

### PackingSolutionService

**Responsibility**: Orchestrate the calculation of optimal packing solutions.

```java
@DomainService
public class PackingSolutionService {

    public PackingSolution calculateOptimalSolution(
        List<Item> items,
        List<Carton> availableCartons,
        PackingConstraints constraints
    );

    public PackingSolution calculateMultiCartonSolution(
        List<Item> items,
        List<Carton> availableCartons
    );

    public void validateSolution(PackingSolution solution);
}
```

---

### BinPackingAlgorithm

**Responsibility**: Core 3D bin-packing algorithm implementation.

```java
@DomainService
public interface BinPackingAlgorithm {

    PackingResult packItems(
        List<Item> items,
        Carton carton,
        PackingStrategy strategy
    );

    List<ItemPlacement> optimizePlacements(
        List<Item> items,
        Dimensions containerDimensions
    );
}
```

**Implementations**:
- `FirstFitDecreasingAlgorithm`
- `BestFitAlgorithm`
- `GeneticAlgorithm` (future)

---

### CartonSelectionStrategy

**Responsibility**: Select the most appropriate carton based on business rules.

```java
@DomainService
public interface CartonSelectionStrategy {

    Carton selectOptimalCarton(
        List<Item> items,
        List<Carton> candidates,
        SelectionCriteria criteria
    );
}
```

**Strategies**:
- `MinimumCostStrategy` - Lowest cost carton
- `MinimumSizeStrategy` - Smallest viable carton
- `MinimumWasteStrategy` - Best utilization
- `WeightOptimizedStrategy` - Optimize for carrier weight brackets

---

## Application Layer

### Ports (Interfaces)

#### Input Ports (Use Cases)

```java
// Commands
public interface CalculatePackingSolutionCommand {
    PackingSolution execute(CalculatePackingRequest request);
}

public interface CreateCartonCommand {
    Carton execute(CreateCartonRequest request);
}

public interface UpdateCartonCommand {
    Carton execute(UpdateCartonRequest request);
}
```

#### Output Ports (Dependencies)

```java
// Repository ports
public interface CartonRepository {
    Optional<Carton> findById(String cartonTypeId);
    List<Carton> findAllActive();
    void save(Carton carton);
}

public interface PackingSolutionRepository {
    Optional<PackingSolution> findById(String solutionId);
    void save(PackingSolution solution);
}

// External service ports
public interface ProductCatalogClient {
    ProductDimensions getProductDimensions(String sku);
    List<ProductDimensions> getProductDimensions(List<String> skus);
}

public interface EventPublisher {
    void publish(DomainEvent event);
}
```

---

## Infrastructure Layer

### Adapters

#### Inbound Adapters

**REST Controller**
```java
@RestController
@RequestMapping("/api/v1/cartonization")
public class CartonizationController {

    @PostMapping("/calculate")
    public ResponseEntity<PackingSolutionResponse> calculatePacking(
        @RequestBody CalculatePackingRequest request
    );

    @GetMapping("/solutions/{solutionId}")
    public ResponseEntity<PackingSolutionResponse> getSolution(
        @PathVariable String solutionId
    );
}
```

**Event Listener**
```java
@Component
public class OrderEventListener {

    @KafkaListener(topics = "fulfillment.order.v1.events")
    public void handleOrderValidated(FulfillmentOrderValidatedEvent event) {
        // Automatically calculate packing solution
    }
}
```

#### Outbound Adapters

**MongoDB Adapter**
```java
@Repository
public class MongoCartonRepository implements CartonRepository {
    // Implementation using Spring Data MongoDB
}
```

**Kafka Event Publisher**
```java
@Component
public class KafkaEventPublisher implements EventPublisher {

    @Override
    public void publish(DomainEvent event) {
        // Publish CloudEvents format to Kafka
    }
}
```

**Product Catalog Client**
```java
@Component
public class RestProductCatalogClient implements ProductCatalogClient {

    @Override
    public ProductDimensions getProductDimensions(String sku) {
        // REST call to Product Catalog service
    }
}
```

**Redis Cache Adapter**
```java
@Component
public class PackingSolutionCacheService {

    public Optional<PackingSolution> getCachedSolution(String cacheKey);
    public void cacheSolution(String cacheKey, PackingSolution solution);
    public void invalidate(String cacheKey);
}
```

---

## Business Capabilities

### L1: Shipment Optimization

Optimize packaging and cartonization for shipments to minimize costs, reduce waste, and maximize efficiency in the fulfillment process.

---

### L2: Packing Solution Calculation

#### L3.1: 3D Bin-Packing Algorithm
- Core algorithm for optimal item placement
- Supports rotation and orientation constraints
- Considers weight distribution
- Handles irregular shapes (future)

#### L3.2: Multi-Carton Optimization
- Distributes items across multiple cartons
- Minimizes total number of cartons
- Balances weight across packages
- Considers carrier restrictions

#### L3.3: Carton Selection Strategy
- Evaluates available carton types
- Selects smallest viable carton
- Considers cost optimization
- Handles special requirements (fragile, hazmat)

#### L3.4: Weight-Based Optimization
- Calculates total package weight
- Considers carrier weight brackets
- Optimizes dimensional weight
- Accounts for packaging materials

#### L3.5: Packing Solution Caching
- Redis-based caching layer
- Cache key from item SKUs and quantities
- TTL-based expiration
- Cache warming for common combinations

---

### L2: Carton Catalog Management

#### L3.6: Carton Type Registration
- Register new carton types
- Define dimensions and capacities
- Set cost information
- Manage carton attributes

#### L3.7: Carton Specification Retrieval
- Query carton specifications
- Filter by dimensions/capacity/cost
- Support bulk retrieval
- Version management

#### L3.8: Carton Cost Management
- Manage carton costs
- Historical cost tracking
- Cost-based optimization
- Multi-currency support (future)

---

### L2: Event-Driven Integration

#### L3.9: Packing Solution Calculated Event
- Publish solution details
- Include utilization metrics
- Provide cost information
- Enable downstream workflows

#### L3.10: Carton Catalog Change Events
- Notify of carton type changes
- Trigger cache invalidation
- Update dependent systems
- Maintain data consistency

---

### L2: Performance & Scalability

#### L3.11: Asynchronous Processing
- Spring @Async for non-blocking execution
- Thread pool management
- CompletableFuture for results
- Priority-based processing

#### L3.12: Multi-Layer Caching
- Redis for distributed cache
- In-memory cache for hot data
- Cache-aside pattern
- Intelligent cache warming

#### L3.13: Solution Pre-calculation
- Background job processing
- Pattern analysis
- Bulk calculation
- Proactive caching

---

## Integration Patterns

### Upstream Integration (Consumers)

**Order Management Service**
- **Event**: `FulfillmentOrderValidatedEvent`
- **Action**: Calculate packing solution
- **Protocol**: Kafka event consumption

**Product Catalog Service**
- **API**: REST calls for product dimensions
- **Pattern**: Synchronous request/response
- **Caching**: Product dimensions cached locally

### Downstream Integration (Producers)

**Warehouse Operations Service**
- **Event**: `PackingSolutionCalculatedEvent`
- **Purpose**: Trigger packing instructions
- **Protocol**: Kafka event publishing

**Order Management Service**
- **Event**: `PackingSolutionCalculatedEvent`
- **Purpose**: Update order with carton details
- **Protocol**: Kafka event publishing

---

## Context Mapping

### Relationship with Other Bounded Contexts

#### Product Catalog (Upstream - Customer/Supplier)
- **Type**: Conformist relationship
- **Integration**: REST API calls
- **Dependency**: Product dimensions are authoritative from Product Catalog
- **Protection**: Local caching to reduce coupling

#### Order Management (Upstream - Published Language)
- **Type**: Published Language (CloudEvents)
- **Integration**: Event-driven via Kafka
- **Contract**: AsyncAPI specification
- **Evolution**: Versioned events for backward compatibility

#### Warehouse Operations (Downstream - Customer/Supplier)
- **Type**: Customer/Supplier
- **Integration**: Event-driven via Kafka
- **Contract**: Cartonization publishes packing solutions
- **Collaboration**: Joint schema definition

#### Shipment & Transportation (Downstream - Customer/Supplier)
- **Type**: Customer/Supplier
- **Integration**: Event-driven via Kafka
- **Purpose**: Provide package dimensions for carrier rating

---

## Anti-Corruption Layer

### Product Catalog Integration

To protect the Cartonization domain from changes in Product Catalog:

```java
@Component
public class ProductCatalogAntiCorruptionLayer {

    private final ProductCatalogClient client;
    private final ProductDimensionMapper mapper;

    public Dimensions getItemDimensions(String sku) {
        // Call external service
        ProductCatalogResponse response = client.getProduct(sku);

        // Map to our domain model
        return mapper.toDomainDimensions(response);
    }

    public List<Dimensions> getItemDimensions(List<String> skus) {
        // Batch retrieval with mapping
        List<ProductCatalogResponse> responses = client.getProducts(skus);
        return responses.stream()
            .map(mapper::toDomainDimensions)
            .collect(toList());
    }
}
```

---

## Event Schemas

### PackingSolutionCalculatedEvent

```json
{
  "specversion": "1.0",
  "type": "com.paklog.cartonization.solution.calculated",
  "source": "cartonization-service",
  "id": "solution-12345",
  "time": "2025-10-18T10:30:00Z",
  "datacontenttype": "application/json",
  "data": {
    "solutionId": "solution-12345",
    "orderId": "ORD-67890",
    "cartonAssignments": [
      {
        "cartonTypeId": "SMALL-BOX-001",
        "items": [
          {"sku": "PROD-123", "quantity": 2},
          {"sku": "PROD-456", "quantity": 1}
        ],
        "utilizationPercentage": 0.85,
        "cartonCost": 2.50
      }
    ],
    "totalCost": 2.50,
    "averageUtilization": 0.85,
    "calculatedAt": "2025-10-18T10:30:00Z"
  }
}
```

### CartonTypeCreatedEvent

```json
{
  "specversion": "1.0",
  "type": "com.paklog.cartonization.carton.created",
  "source": "cartonization-service",
  "id": "carton-type-update-123",
  "time": "2025-10-18T10:30:00Z",
  "datacontenttype": "application/json",
  "data": {
    "cartonTypeId": "LARGE-BOX-002",
    "name": "Large Shipping Box",
    "internalDimensions": {
      "length": 40.0,
      "width": 30.0,
      "height": 20.0,
      "unit": "CM"
    },
    "maxWeight": {
      "value": 25.0,
      "unit": "KG"
    },
    "cost": 3.50,
    "attributes": {
      "heavyDuty": true,
      "fragileApproved": true,
      "hazmatApproved": false
    }
  }
}
```

---

## Quality Attributes

### Performance
- **Target**: Sub-second packing solution calculation for 95% of orders
- **Caching**: >80% cache hit rate for common item combinations
- **Throughput**: 10,000+ calculations per hour

### Scalability
- **Horizontal**: Stateless service design enables horizontal scaling
- **Caching**: Redis for shared cache across instances
- **Async**: Background processing for non-urgent calculations

### Reliability
- **Availability**: 99.9% uptime SLA
- **Fault Tolerance**: Circuit breakers for external dependencies
- **Retry Logic**: Exponential backoff for transient failures

### Maintainability
- **Clean Architecture**: Clear separation of concerns
- **Domain Model**: Rich domain model with business logic encapsulation
- **Testing**: Comprehensive unit and integration tests

---

## Summary

The Cartonization Service is a well-defined bounded context within the PakLog ecosystem, focused on optimal packaging solutions. It demonstrates:

- **Clear Boundaries**: Well-defined responsibilities and external dependencies
- **Rich Domain Model**: Aggregates, entities, value objects with business invariants
- **Strategic Classification**: Core domain for packing optimization
- **Clean Architecture**: Hexagonal architecture with ports and adapters
- **Event-Driven Integration**: CloudEvents for loose coupling
- **Anti-Corruption Layers**: Protection from external system changes
- **Performance Optimization**: Multi-layer caching and async processing

The service provides significant business value through cost reduction (15-30%), waste reduction (25-40%), and operational efficiency (sub-second calculations).
