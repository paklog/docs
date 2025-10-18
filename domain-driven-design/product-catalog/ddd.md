# Product Catalog Service - Domain Architecture & Business Capabilities

## Service Overview

The Product Catalog Service is the canonical source of truth for all product master data across the fulfillment ecosystem. It manages product information including SKUs, descriptions, dimensions, weights, and special handling requirements such as hazardous materials.

**Architecture Pattern**: Hexagonal Architecture with Domain-Driven Design (DDD)
**Technology Stack**: Spring Boot 3, Spring Data MongoDB, Spring Kafka, CQRS
**Integration Pattern**: Event-Driven Architecture with Published Language

---

## Domain Model & Bounded Context

### Bounded Context: Product Catalog

The Product Catalog bounded context is responsible for maintaining the master data for all products that flow through the fulfillment network.

#### Context Boundaries

**Responsibilities (What's IN)**:
- Maintain product master data (SKU, name, description)
- Manage product physical dimensions (item and package)
- Track product weight information
- Manage special product attributes (fragile, hazmat, etc.)
- Maintain hazardous materials compliance information
- Publish product lifecycle events (created, updated, deleted)
- Validate product data quality
- Manage product archival and lifecycle

**External Dependencies (What's OUT)**:
- Product pricing (Pricing context - external)
- Product inventory levels (Inventory context)
- Product images and media (Digital Asset Management - external)
- Product categories and taxonomy (Merchandising context - external)
- Vendor/supplier information (Procurement context - external)

#### Ubiquitous Language

**Core Domain Terms**:

- **SKU (Stock Keeping Unit)**: Unique identifier for a product
- **Product**: An item that can be ordered and fulfilled
- **Item Dimensions**: Physical dimensions of the product itself (L × W × H)
- **Package Dimensions**: Dimensions of the standard packaging for the product
- **Dimensional Weight**: Calculated weight based on package dimensions
- **Hazmat (Hazardous Materials)**: Products requiring special handling and compliance
- **UN Number**: United Nations identifier for hazardous materials
- **Proper Shipping Name**: Official name for hazmat shipping documents
- **Product Attributes**: Special characteristics (fragile, perishable, high-value, etc.)
- **Archived Product**: Product no longer active but retained for history

---

## Subdomain Classification

### Core Domain: Product Master Data Management

**Strategic Importance**: MEDIUM - Supporting domain but critical for operations

This is a supporting domain that enables fulfillment operations through:
- Providing accurate product information to all services
- Ensuring dimensional data accuracy for cartonization
- Managing compliance data for hazmat shipping
- Serving as single source of truth

**Subdomains**:

#### 1. **Product Information Management** (Supporting)
- **Complexity**: Low - CRUD operations with validation
- **Strategic Value**: Medium - Necessary but not differentiating
- **Volatility**: Medium - Product data changes regularly
- **Business Differentiation**: Standard capability
- **Investment Priority**: Medium - Maintain data quality

#### 2. **Dimensional Data Management** (Supporting)
- **Complexity**: Medium - Validation and calculations
- **Strategic Value**: High - Critical for cartonization and shipping
- **Volatility**: Low - Stable requirements
- **Business Differentiation**: Operational enabler
- **Investment Priority**: High - Data accuracy critical

#### 3. **Hazmat Compliance Management** (Supporting)
- **Complexity**: Medium - Regulatory compliance
- **Strategic Value**: High - Legal requirement
- **Volatility**: Medium - Regulations change
- **Business Differentiation**: Compliance necessity
- **Investment Priority**: High - Regulatory compliance

#### 4. **Product Data Synchronization** (Generic)
- **Complexity**: Low - Event publishing
- **Strategic Value**: Medium - Integration mechanism
- **Volatility**: Low - Stable patterns
- **Business Differentiation**: Standard capability
- **Investment Priority**: Low - Use standard patterns

---

## Domain Model

### Aggregates

#### 1. Product (Aggregate Root)

**Description**: The central aggregate representing a product with all its attributes and characteristics.

```java
@AggregateRoot
public class Product {
    private String sku; // Aggregate ID
    private String name;
    private String description;
    private Dimensions dimensions;
    private Weight weight;
    private ProductAttributes attributes;
    private boolean archived;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private int version; // Optimistic locking

    // Business methods
    public void updateDimensions(Dimensions newDimensions);
    public void updateWeight(Weight newWeight);
    public void updateAttributes(ProductAttributes newAttributes);
    public void archive();
    public void restore();
    public boolean isHazmat();
    public boolean isFragile();
    public boolean isOversized(Dimensions threshold);

    // Invariants
    private void ensureSkuIsValid();
    private void ensureItemDimensionsNotExceedPackage();
    private void ensureHazmatDataComplete();
    private void ensureWeightIsPositive();
}
```

**Invariants**:
- SKU must be unique and non-empty
- Name is required (max 200 characters)
- Item dimensions ≤ package dimensions (all axes)
- Weight > 0
- If hazmat, complete hazmat information required

**Domain Events**:
- `ProductCreatedEvent`
- `ProductUpdatedEvent`
- `ProductArchivedEvent`
- `ProductRestoredEvent`
- `ProductDeletedEvent`

---

### Value Objects

#### Dimensions

```java
@ValueObject
public class Dimensions {
    private ItemDimension item;
    private PackageDimension package_;

    public Volume getItemVolume();
    public Volume getPackageVolume();
    public double getPackageEfficiency(); // item volume / package volume
    public boolean itemFitsInPackage();
    public DimensionalWeight calculateDimensionalWeight(int dimFactor);
}

@ValueObject
public class ItemDimension {
    private BigDecimal length;
    private BigDecimal width;
    private BigDecimal height;
    private DimensionUnit unit; // INCHES, CENTIMETERS

    public Volume calculateVolume();
    public boolean fitsWithin(PackageDimension package_);
}

@ValueObject
public class PackageDimension {
    private BigDecimal length;
    private BigDecimal width;
    private BigDecimal height;
    private DimensionUnit unit;

    public Volume calculateVolume();
    public boolean canAccommodate(ItemDimension item);
}
```

#### Weight

```java
@ValueObject
public class Weight {
    private BigDecimal value;
    private WeightUnit unit; // POUNDS, KILOGRAMS, OUNCES

    public Weight convertTo(WeightUnit targetUnit);
    public boolean isHeavy(Weight threshold);
    public boolean exceedsLimit(Weight maxWeight);
}
```

#### ProductAttributes

```java
@ValueObject
public class ProductAttributes {
    private boolean fragile;
    private boolean perishable;
    private boolean highValue;
    private boolean oversized;
    private boolean batteryPowered;
    private boolean liquid;
    private HazmatInfo hazmat; // null if not hazmat

    public boolean requiresSpecialHandling();
    public Set<HandlingRequirement> getHandlingRequirements();
    public boolean hasShippingRestrictions();
}
```

#### HazmatInfo

```java
@ValueObject
public class HazmatInfo {
    private String unNumber; // UN1266
    private String hazardClass; // 3 (Flammable liquids)
    private String packingGroup; // II
    private String properShippingName;
    private boolean airEligible;
    private boolean groundOnly;
    private List<String> specialInstructions;

    public boolean isComplete();
    public boolean canShipVia(ShippingMethod method);
    public String formatForShippingLabel();
}
```

---

## Domain Services

### ProductValidationService

**Responsibility**: Validate product data for consistency and business rules.

```java
@DomainService
public class ProductValidationService {

    public ValidationResult validate(Product product);

    private ValidationResult validateSKU(String sku);
    private ValidationResult validateDimensions(Dimensions dimensions);
    private ValidationResult validateWeight(Weight weight);
    private ValidationResult validateHazmatInfo(HazmatInfo hazmat);
}
```

---

### DimensionalWeightCalculator

**Responsibility**: Calculate dimensional weight for shipping cost estimation.

```java
@DomainService
public class DimensionalWeightCalculator {

    public DimensionalWeight calculate(
        PackageDimension dimensions,
        int dimFactor // carrier-specific: FedEx=139, UPS=139
    );

    public Weight getChargeableWeight(
        Weight actualWeight,
        DimensionalWeight dimWeight
    ); // Returns greater of actual or dimensional
}
```

---

## Application Layer

### Ports (Interfaces)

#### Input Ports (Use Cases - CQRS Pattern)

```java
// Commands
public interface CreateProductCommand {
    Product execute(CreateProductRequest request);
}

public interface UpdateProductCommand {
    Product execute(UpdateProductRequest request);
}

public interface ArchiveProductCommand {
    void execute(String sku);
}

public interface RestoreProductCommand {
    void execute(String sku);
}

// Queries (Separate query services for CQRS)
public interface GetProductQuery {
    Product execute(String sku);
}

public interface ListProductsQuery {
    PagedResult<Product> execute(int offset, int limit, boolean includeArchived);
}

public interface SearchProductsQuery {
    List<Product> execute(String searchTerm);
}

public interface GetProductDimensionsQuery {
    Dimensions execute(String sku);
}
```

#### Output Ports (Dependencies)

```java
// Repository ports
public interface ProductRepository {
    Optional<Product> findBySku(String sku);
    List<Product> findAllActive(Pageable pageable);
    List<Product> findBySkus(List<String> skus);
    void save(Product product);
    void delete(String sku);
    boolean existsBySku(String sku);
}

// Event publishing
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
@RequestMapping("/api/v1/products")
public class ProductController {

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ResponseEntity<ProductResponse> createProduct(
        @Valid @RequestBody CreateProductRequest request
    );

    @GetMapping("/{sku}")
    public ResponseEntity<ProductResponse> getProduct(
        @PathVariable String sku
    );

    @GetMapping
    public ResponseEntity<PagedProductResponse> listProducts(
        @RequestParam(defaultValue = "0") int offset,
        @RequestParam(defaultValue = "20") int limit,
        @RequestParam(defaultValue = "false") boolean includeArchived
    );

    @PutMapping("/{sku}")
    public ResponseEntity<ProductResponse> updateProduct(
        @PathVariable String sku,
        @Valid @RequestBody UpdateProductRequest request
    );

    @DeleteMapping("/{sku}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public ResponseEntity<Void> archiveProduct(@PathVariable String sku);

    @PostMapping("/{sku}/restore")
    public ResponseEntity<ProductResponse> restoreProduct(@PathVariable String sku);
}
```

#### Outbound Adapters

**MongoDB Adapter**
```java
@Repository
public class MongoProductRepository implements ProductRepository {

    private final MongoTemplate mongoTemplate;

    @Override
    public Optional<Product> findBySku(String sku) {
        return Optional.ofNullable(
            mongoTemplate.findById(sku, Product.class)
        );
    }

    @Override
    public List<Product> findAllActive(Pageable pageable) {
        Query query = new Query(Criteria.where("archived").is(false))
            .with(pageable);
        return mongoTemplate.find(query, Product.class);
    }

    @Override
    public void save(Product product) {
        mongoTemplate.save(product);
    }
}
```

**Kafka Event Publisher**
```java
@Component
public class KafkaProductEventPublisher implements EventPublisher {

    private static final String TOPIC = "product.catalog.v1.events";
    private final KafkaTemplate<String, CloudEvent> kafkaTemplate;

    @Override
    public void publish(DomainEvent event) {
        CloudEvent cloudEvent = CloudEventBuilder.v1()
            .withId(event.getId())
            .withType(event.getType())
            .withSource(URI.create("product-catalog-service"))
            .withData(event.toJson().getBytes())
            .build();

        kafkaTemplate.send(TOPIC, cloudEvent);
    }
}
```

---

## Business Capabilities

### L1: Product Master Data Management

Canonical source of truth for all product information used across inventory, cartonization, warehouse operations, and shipment services.

---

### L2: Product Information Management

#### L3.1: Product Registration (Create)
- Register new products with complete information
- Unique SKU assignment
- Comprehensive validation
- Publish `ProductCreatedEvent`

#### L3.2: Product Retrieval (Read)
- Query by SKU (single product)
- Batch retrieval by SKU list
- List all products with pagination
- Search by name/description
- Filter active vs. archived

#### L3.3: Product Update
- Modify product attributes
- Update dimensions and weight
- Change hazmat information
- Version control (optimistic locking)
- Publish `ProductUpdatedEvent`

#### L3.4: Product Archival & Deletion
- Soft delete (archive) for historical retention
- Hard delete (rare, for never-used products)
- Restore archived products
- Prevent deletion with active inventory
- Publish `ProductArchivedEvent`

---

### L2: Dimensional Data Management

#### L3.5: Item Dimension Management
- Track actual product dimensions (L × W × H)
- Support multiple units (inches, cm)
- Validate dimension positivity
- Calculate item volume

#### L3.6: Package Dimension Management
- Standard packaging dimensions
- Validate package ≥ item dimensions
- Calculate package volume
- Package efficiency metrics

#### L3.7: Weight Management
- Product weight tracking
- Multiple weight units (lbs, kg, oz)
- Weight validation (positive values)
- Maximum weight limits

#### L3.8: Dimensional Validation
- Item fits in package validation
- Reasonable dimension limits
- Cross-field consistency checks
- Business rule validation

---

### L2: Special Handling & Attributes

#### L3.9: Hazardous Materials (Hazmat) Management
- UN number tracking
- Hazard class classification
- Packing group assignment
- Proper shipping name
- Air vs. ground eligibility
- Special handling instructions

#### L3.10: Product Attributes Management
- Fragile flag
- Perishable indicator
- High-value designation
- Oversized classification
- Battery/lithium restrictions
- Liquid indicator

---

### L2: Product Data Synchronization

#### L3.11: Product Event Publishing
- Publish lifecycle events
- CloudEvents format
- Product created/updated/deleted events
- Schema versioning

#### L3.12: Bulk Product Export
- Export product catalog
- Multiple formats (JSON, CSV)
- Pagination for large datasets
- Include/exclude archived products

---

### L2: Data Quality & Governance

#### L3.13: Data Validation
- Multi-layer validation (syntax, semantic, business)
- SKU format validation
- Dimensional constraint validation
- Hazmat completeness validation

#### L3.14: SKU Format Validation
- Enforce SKU naming conventions
- Uniqueness validation
- Case-insensitive checking
- Reserved prefix handling

#### L3.15: Duplicate Detection
- Prevent duplicate SKUs
- Fuzzy matching for similar products
- Manual review workflow

---

## Integration Patterns

### Context Mapping

#### Inventory (Downstream - Published Language)
- **Type**: Published Language (events)
- **Integration**: Event-driven via Kafka
- **Contract**: Product Catalog publishes, Inventory consumes
- **Events**: ProductCreated (initialize stock), ProductUpdated (update dimensions)

#### Cartonization (Downstream - Published Language)
- **Type**: Published Language (events)
- **Integration**: Event-driven + REST (dimension queries)
- **Contract**: Product dimensions queried synchronously
- **Events**: ProductUpdated (cache invalidation)

#### Warehouse Operations (Downstream - Published Language)
- **Type**: Published Language (events)
- **Integration**: Event-driven
- **Contract**: Product updates trigger warehouse sync
- **Events**: Product lifecycle events

#### Shipment & Transportation (Downstream - Published Language)
- **Type**: Published Language (events)
- **Integration**: REST (dimension/weight queries)
- **Contract**: Product data queried for shipping calculations

---

## Event Schemas

### ProductCreatedEvent

```json
{
  "specversion": "1.0",
  "type": "com.paklog.product.created",
  "source": "product-catalog-service",
  "id": "evt-prod-12345",
  "time": "2025-10-18T10:30:00Z",
  "datacontenttype": "application/json",
  "data": {
    "sku": "PROD-12345",
    "name": "Widget Pro",
    "description": "Premium widget with advanced features",
    "dimensions": {
      "item": {
        "length": 10.0,
        "width": 5.0,
        "height": 3.0,
        "unit": "INCHES"
      },
      "package": {
        "length": 12.0,
        "width": 7.0,
        "height": 5.0,
        "unit": "INCHES"
      }
    },
    "weight": {
      "value": 2.5,
      "unit": "POUNDS"
    },
    "attributes": {
      "fragile": false,
      "hazmat": false
    },
    "createdAt": "2025-10-18T10:30:00Z"
  }
}
```

### ProductUpdatedEvent

```json
{
  "specversion": "1.0",
  "type": "com.paklog.product.updated",
  "source": "product-catalog-service",
  "id": "evt-prod-update-456",
  "time": "2025-10-18T11:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "sku": "PROD-12345",
    "changes": {
      "dimensions": {
        "before": {"item": {"length": 10.0, "width": 5.0, "height": 3.0}},
        "after": {"item": {"length": 11.0, "width": 5.0, "height": 3.0}}
      }
    },
    "updatedAt": "2025-10-18T11:00:00Z"
  }
}
```

---

## Quality Attributes

### Data Quality
- **Accuracy**: >95% validation success rate
- **Consistency**: Single source of truth
- **Completeness**: All required fields validated
- **Uniqueness**: SKU uniqueness enforced

### Performance
- **Query Latency**: <50ms p95
- **Cache Hit Rate**: >90%
- **Throughput**: 1,000+ operations per second

### Availability
- **Uptime**: 99.9% SLA
- **Caching**: Product data cached downstream
- **Replication**: MongoDB replica sets

---

## Summary

The Product Catalog Service is a well-defined bounded context:

- **Single Source of Truth**: Canonical product master data
- **Published Language**: Events consumed by all downstream services
- **CQRS Pattern**: Separate read/write models
- **Data Quality**: Comprehensive validation framework
- **Dimensional Accuracy**: Critical for cartonization and shipping

Business Impact: Supports millions of SKUs, >95% data quality, <50ms query latency, >90% cache hit rate, real-time event propagation.
