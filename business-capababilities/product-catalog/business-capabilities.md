# Product Catalog Service - Business Capabilities

**Service Overview**: The Product Catalog Service is the canonical source of truth for all product master data across the fulfillment ecosystem. It manages product information including SKUs, descriptions, dimensions, weights, and special handling requirements such as hazardous materials.

**Architecture**: Hexagonal Architecture with Domain-Driven Design (DDD)
**Technology Stack**: Spring Boot 3, Spring Data MongoDB, Spring Kafka, CQRS
**Domain Model**: Product aggregate as the root entity with value objects for dimensions and attributes

---

## L1: Product Master Data Management

### L1.1: Description
Manage comprehensive product master data serving as the single source of truth for all product information used across inventory, cartonization, warehouse operations, and shipment services.

### L1.2: Strategic Value
- **Data Consistency**: Single source of truth eliminates data discrepancies
- **Operational Efficiency**: Centralized product data management reduces duplication
- **Accuracy**: Ensure dimensional and attribute accuracy for downstream operations
- **Compliance**: Manage hazmat and regulatory information centrally
- **Integration**: Enable seamless product data synchronization across services

---

## L2: Product Information Management

### L2.1: Description
Create, read, update, and delete product information including basic attributes, physical dimensions, and descriptive information.

### L2.2: Business Value
- Centralized product data governance
- Support for product lifecycle management
- Enable accurate product representation across all channels
- Maintain product data quality and consistency

### L2.3: L3 Capabilities

#### L3.1.1: Product Registration
**Description**: Register new products in the catalog with complete product information.

**Technical Implementation**:
- RESTful API for product creation
- `CreateProductCommand` processed via application service
- Product aggregate instantiation
- MongoDB persistence
- Event publishing via Kafka

**Business Rules**:
- SKU must be unique across entire catalog
- SKU cannot be empty or null
- Product name is required
- At least basic dimensions must be provided
- SKU format validation (alphanumeric, max 50 characters)

**Domain Model**:
```java
@AggregateRoot
class Product {
  @Id
  private String sku; // Unique identifier
  private String name;
  private String description;
  private Dimensions dimensions; // Value Object
  private ProductAttributes attributes; // Value Object
  private BigDecimal weight;
  private LocalDateTime createdAt;
  private LocalDateTime updatedAt;
  private boolean archived;
}
```

**Key Metrics**:
- Products created per day
- Product creation success rate
- Average time to create product
- SKU collision rate (rejections)

**API Endpoints**:
- `POST /api/v1/products` - Create new product

**Request Example**:
```json
{
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
  "weight": 2.5,
  "weightUnit": "POUNDS"
}
```

**Domain Events**:
- `ProductCreatedEvent` - Published to Kafka topic

**Related Services**:
- Inventory (initialize stock records)
- Cartonization (update dimension cache)

---

#### L3.1.2: Product Retrieval
**Description**: Query product information by SKU or other criteria.

**Technical Implementation**:
- CQRS pattern with separate query service
- Optimized read models for different access patterns
- Support for single and batch retrieval
- Pagination for list queries

**Business Rules**:
- Only return non-archived products by default
- Support filtering by archived status
- Include all product attributes in response
- Case-insensitive SKU lookup

**Query Types**:
1. **Single Product Query**: Get product by exact SKU
2. **Batch Query**: Get multiple products by SKU list
3. **List Query**: Paginated list of all products
4. **Search Query**: Search by name, description (optional)

**Key Metrics**:
- Query response time (p95 < 50ms)
- Cache hit rate (target: >90%)
- Query volume by type
- Most frequently accessed SKUs

**API Endpoints**:
- `GET /api/v1/products/{sku}` - Get product by SKU
- `GET /api/v1/products?offset=0&limit=20` - List products with pagination
- `GET /api/v1/products/batch?skus=PROD-1,PROD-2` - Batch retrieval

**Response Example**:
```json
{
  "sku": "PROD-12345",
  "name": "Widget Pro",
  "description": "Premium widget",
  "dimensions": {
    "item": {"length": 10.0, "width": 5.0, "height": 3.0, "unit": "INCHES"},
    "package": {"length": 12.0, "width": 7.0, "height": 5.0, "unit": "INCHES"}
  },
  "weight": 2.5,
  "weightUnit": "POUNDS",
  "attributes": {},
  "createdAt": "2025-01-15T10:00:00Z",
  "updatedAt": "2025-01-15T10:00:00Z"
}
```

**Related Services**: All services (product data consumers)

---

#### L3.1.3: Product Update
**Description**: Update existing product information while maintaining data integrity.

**Technical Implementation**:
- RESTful API for product updates
- `UpdateProductCommand` processed via application service
- Optimistic locking for concurrency control
- Validation of updated attributes
- Event publishing for downstream sync

**Business Rules**:
- SKU cannot be changed (immutable identifier)
- All validation rules re-applied on update
- Dimensional constraints validated (item ≤ package)
- Update timestamp automatically maintained
- Version control for concurrent updates

**Updatable Fields**:
- Name
- Description
- Dimensions (both item and package)
- Weight
- Attributes (hazmat info, etc.)

**Key Metrics**:
- Updates per product (average)
- Update frequency
- Update conflicts (optimistic locking failures)
- Most frequently updated fields

**API Endpoints**:
- `PUT /api/v1/products/{sku}` - Update complete product
- `PATCH /api/v1/products/{sku}` - Partial update (optional)

**Domain Events**:
- `ProductUpdatedEvent` - Published with before/after values

**Related Services**:
- Inventory (dimension updates affect space calculations)
- Cartonization (cache invalidation)
- Warehouse (picking instructions update)

---

#### L3.1.4: Product Deletion/Archival
**Description**: Remove products from active catalog or mark as archived.

**Technical Implementation**:
- Soft delete via `archived` flag (recommended)
- Hard delete option for truly obsolete products
- Validation checks before deletion
- Cascade considerations for dependent data
- Event publishing for cleanup

**Business Rules**:
- Cannot delete products with active inventory (QOH > 0)
- Cannot delete products with pending orders
- Archived products excluded from default queries
- Archived products can be restored
- Hard delete only for products never used

**Deletion Types**:
1. **Soft Delete (Archive)**: Set `archived = true`, retained in database
2. **Hard Delete**: Physical removal from database (rare)

**Key Metrics**:
- Archival rate
- Archive retention period
- Products with zero inventory
- Restoration rate (unarchive)

**API Endpoints**:
- `DELETE /api/v1/products/{sku}` - Archive product
- `POST /api/v1/products/{sku}/archive` - Explicit archive
- `POST /api/v1/products/{sku}/restore` - Restore archived product

**Domain Events**:
- `ProductDeletedEvent` / `ProductArchivedEvent`

**Related Services**:
- Inventory (inventory must be zero)
- Order Management (no pending orders)

---

## L2: Dimensional Data Management

### L2.1: Description
Manage physical dimensions for both the item itself and its packaging, critical for cartonization, storage optimization, and shipping calculations.

### L2.2: Business Value
- Enable accurate carton selection for packing
- Support warehouse space planning
- Calculate dimensional weight for shipping
- Optimize storage locations

### L2.3: L3 Capabilities

#### L3.2.1: Item Dimension Management
**Description**: Manage the actual physical dimensions of the product item itself.

**Technical Implementation**:
- `Dimensions` value object with item and package dimensions
- Separate tracking of length, width, height
- Support for multiple units (inches, cm)
- Validation of dimensional constraints

**Business Rules**:
- All three dimensions required (L × W × H)
- Dimensions must be positive numbers
- Item dimensions cannot exceed package dimensions
- Support decimal precision (2 decimal places)
- Dimensional consistency validation

**Dimension Units**:
- `INCHES` (default for US operations)
- `CENTIMETERS` (international)
- Automatic conversion supported

**Key Metrics**:
- Average item dimensions by category
- Dimensional accuracy (vs. actual measurements)
- Dimension update frequency

**Domain Model**:
```java
@ValueObject
class Dimensions {
  private ItemDimension item;
  private PackageDimension package;
}

@ValueObject
class ItemDimension {
  private BigDecimal length;
  private BigDecimal width;
  private BigDecimal height;
  private DimensionUnit unit;

  public BigDecimal volume() {
    return length.multiply(width).multiply(height);
  }
}
```

**Related Services**:
- Cartonization (item dimensions for bin packing)
- Warehouse (slotting optimization)

---

#### L3.2.2: Package Dimension Management
**Description**: Manage dimensions of the product's standard packaging (outer box/package).

**Technical Implementation**:
- Part of `Dimensions` value object
- Represents "ship-alone" package dimensions
- Used for dimensional weight calculations
- Validation against item dimensions

**Business Rules**:
- Package dimensions ≥ item dimensions (validation rule)
- Package includes protective materials/padding
- Standard packaging dimensions (not custom pack)
- Used when item ships individually

**Key Metrics**:
- Package to item dimension ratio
- Package efficiency (item volume / package volume)
- Dimensional weight calculations

**Related Services**:
- Cartonization (ship-alone sizing)
- Shipment (dimensional weight)

---

#### L3.2.3: Weight Management
**Description**: Track product weight for shipping, handling, and cartonization decisions.

**Technical Implementation**:
- Weight stored as BigDecimal
- Support for multiple units (pounds, kg, oz)
- Separate tracking of item weight vs. package weight (optional)
- Validation of weight values

**Business Rules**:
- Weight must be positive
- Weight includes product only (not packaging by default)
- Support for catch-weight items (variable weight)
- Maximum weight limits based on handling requirements

**Weight Units**:
- `POUNDS` (default)
- `KILOGRAMS`
- `OUNCES`

**Key Metrics**:
- Average weight by product category
- Weight distribution
- Heavy item percentage (>50 lbs)

**Related Services**:
- Cartonization (weight-based packing)
- Shipment (carrier weight brackets)
- Warehouse (handling requirements)

---

#### L3.2.4: Dimensional Validation
**Description**: Validate dimensional data for consistency and business rule compliance.

**Technical Implementation**:
- Bean validation annotations
- Custom validators for complex rules
- Domain service for cross-field validation
- Validation on create and update operations

**Validation Rules**:
- Item L/W/H all > 0
- Package L/W/H all > 0
- Package dimensions ≥ item dimensions (all axes)
- Weight > 0
- Reasonable dimension limits (e.g., < 1000 inches)
- Consistency checks (cube vs. stated dimensions)

**Key Metrics**:
- Validation failure rate
- Most common validation errors
- Dimension correction rate

**Related Services**: None (internal validation)

---

## L2: Special Handling & Attributes

### L2.1: Description
Manage special product attributes and handling requirements including hazardous materials, temperature control, and other special handling needs.

### L2.2: Business Value
- Ensure regulatory compliance for hazmat shipping
- Support proper handling and storage
- Enable carrier selection based on capabilities
- Prevent incompatible product combinations

### L2.3: L3 Capabilities

#### L3.3.1: Hazardous Materials (Hazmat) Management
**Description**: Track and manage hazardous materials information for regulatory compliance.

**Technical Implementation**:
- `HazmatInfo` value object within `ProductAttributes`
- UN number, hazard class, packing group
- Proper shipping name
- Special handling instructions
- Validation of hazmat data completeness

**Business Rules**:
- Hazmat items require complete hazmat information
- UN number is mandatory for hazmat items
- Hazmat class determines shipping restrictions
- Cannot combine incompatible hazmat classes
- Special labeling requirements enforced

**Hazmat Information**:
```java
@ValueObject
class HazmatInfo {
  private String unNumber; // e.g., "UN1266"
  private String hazardClass; // e.g., "3" (Flammable liquids)
  private String packingGroup; // e.g., "II"
  private String properShippingName;
  private boolean requiresLabel;
  private List<String> specialInstructions;
}
```

**Key Metrics**:
- Percentage of hazmat SKUs
- Hazmat compliance rate
- Hazmat shipping restrictions violations

**Related Services**:
- Order Management (hazmat validation)
- Shipment (carrier selection, labeling)
- Warehouse (storage restrictions)

---

#### L3.3.2: Product Attributes Management
**Description**: Manage additional product attributes for special handling, categorization, and business logic.

**Technical Implementation**:
- Flexible `ProductAttributes` value object
- Support for various attribute types
- Extensible for new attribute categories
- Schema validation for required attributes

**Attribute Types**:
- **Fragile**: Requires special handling
- **Perishable**: Temperature/time sensitive
- **High Value**: Security requirements
- **Oversized**: Special handling/equipment
- **Battery**: Lithium battery restrictions
- **Liquid**: Leak-proof packaging required

**Business Rules**:
- Attributes affect handling and packing
- Some attributes trigger workflow requirements
- Attributes validated at order acceptance
- Attribute combinations may be restricted

**Domain Model**:
```java
@ValueObject
class ProductAttributes {
  private boolean fragile;
  private boolean perishable;
  private boolean highValue;
  private HazmatInfo hazmat; // null if not hazmat
  private Map<String, String> customAttributes;
}
```

**Key Metrics**:
- Attribute distribution
- Special handling SKU percentage
- Attribute impact on processing time

**Related Services**:
- Warehouse (handling requirements)
- Cartonization (packaging requirements)
- Shipment (carrier restrictions)

---

## L2: Product Data Synchronization

### L2.1: Description
Synchronize product master data across all dependent services through event-driven integration.

### L2.2: Business Value
- Real-time data consistency across services
- Automated propagation of product changes
- Reduced manual data management
- Support for service autonomy

### L2.3: L3 Capabilities

#### L3.4.1: Product Event Publishing
**Description**: Publish domain events for all product lifecycle changes to enable downstream synchronization.

**Technical Implementation**:
- Kafka as event bus
- CloudEvents format for standardization
- Topic: `product.catalog.v1.events`
- Schema registry for event schemas
- Event versioning for backward compatibility

**Published Events**:
- `ProductCreatedEvent` - New product registered
- `ProductUpdatedEvent` - Product information changed
- `ProductDeletedEvent` - Product archived/deleted

**Event Schema Example**:
```json
{
  "id": "evt-prod-12345",
  "type": "com.paklog.product.created",
  "source": "product-catalog-service",
  "specversion": "1.0",
  "time": "2025-10-18T10:30:00Z",
  "datacontenttype": "application/json",
  "data": {
    "sku": "PROD-12345",
    "name": "Widget Pro",
    "dimensions": {
      "item": {"length": 10.0, "width": 5.0, "height": 3.0},
      "package": {"length": 12.0, "width": 7.0, "height": 5.0}
    },
    "weight": 2.5,
    "hazmat": false,
    "createdAt": "2025-10-18T10:30:00Z"
  }
}
```

**Business Rules**:
- Events published immediately after data changes
- Include complete product data (avoid lookups)
- Support event replay for new consumers
- Ordered by timestamp per SKU

**Key Metrics**:
- Events published per day
- Event publishing latency (target: <100ms)
- Event consumption lag by service
- Schema validation success rate

**Related Services**: All services (event consumers)

---

#### L3.4.2: Bulk Product Export
**Description**: Support bulk export of product data for initial loads and reporting.

**Technical Implementation**:
- RESTful API for bulk export
- Pagination for large datasets
- Multiple export formats (JSON, CSV)
- Filtering and selection criteria

**Business Rules**:
- Exports run on read replicas (no prod impact)
- Maximum export size: 10,000 products per request
- Pagination required for large exports
- Include archived products if requested

**Key Metrics**:
- Export request volume
- Export size distribution
- Export generation time

**API Endpoints**:
- `GET /api/v1/products/export?format=csv&includeArchived=false`

**Related Services**:
- Business Intelligence (reporting)
- Partner systems (integration)

---

## L2: Data Quality & Governance

### L2.1: Description
Ensure product data quality, consistency, and compliance with governance policies.

### L2.2: Business Value
- High data quality reduces operational errors
- Consistent data enables accurate analytics
- Compliance with data governance policies
- Support for data-driven decision making

### L2.3: L3 Capabilities

#### L3.5.1: Data Validation
**Description**: Comprehensive validation of product data for accuracy and consistency.

**Technical Implementation**:
- Multi-layer validation (syntax, semantic, business)
- Bean Validation (JSR-303) annotations
- Custom validators for complex rules
- Domain service for cross-field validation

**Validation Layers**:
1. **Syntax Validation**: Data type, format, length
2. **Semantic Validation**: Value ranges, required fields
3. **Business Rule Validation**: Dimensional constraints, SKU format
4. **Cross-Field Validation**: Item ≤ package dimensions

**Validation Rules**:
- SKU: Alphanumeric, 1-50 chars, unique
- Name: Required, max 200 chars
- Dimensions: All positive, item ≤ package
- Weight: Positive, reasonable range (0.01 - 1000 lbs)
- Hazmat: Complete if hazmat flag set

**Key Metrics**:
- Validation failure rate (target: <5%)
- Most common validation errors
- Data quality score

**Related Services**: None (internal validation)

---

#### L3.5.2: SKU Format Validation
**Description**: Enforce consistent SKU formatting across the catalog.

**Technical Implementation**:
- Custom `@ValidSKU` annotation
- `SKUValidator` implementation
- Configurable SKU pattern (regex)
- Uniqueness check via repository

**Business Rules**:
- SKU format: `^[A-Z0-9-]{1,50}$` (alphanumeric + hyphen)
- Case-insensitive uniqueness check
- No leading/trailing whitespace
- Reserved SKU prefixes (TEST-, SAMPLE-)

**Key Metrics**:
- SKU format violations
- Reserved SKU usage
- SKU length distribution

**Related Services**: None (internal validation)

---

#### L3.5.3: Duplicate Detection
**Description**: Prevent duplicate products and identify potential duplicates.

**Technical Implementation**:
- Unique index on SKU field (MongoDB)
- Duplicate detection algorithm (fuzzy matching)
- Similarity scoring for product names
- Manual review workflow for suspected duplicates

**Business Rules**:
- SKU must be globally unique (enforced)
- Similar names flagged for review (>80% similarity)
- Same dimensions flagged as potential duplicate
- Manual approval for similar products

**Key Metrics**:
- Duplicate prevention rate (100% for SKU)
- Suspected duplicates flagged
- False positive rate

**Related Services**: None (internal quality control)

---

## L2: Performance & Scalability

### L2.1: Description
Ensure high performance and scalability for product catalog operations.

### L2.2: Business Value
- Fast product lookups for real-time operations
- Support for large product catalogs (millions of SKUs)
- Consistent performance under load
- Enable business growth

### L2.3: L3 Capabilities

#### L3.6.1: Caching Strategy
**Description**: Implement multi-layer caching for frequently accessed product data.

**Technical Implementation**:
- Redis for distributed cache
- Caffeine for in-memory L1 cache
- Cache-aside pattern
- TTL-based expiration (5 minutes)
- Cache warming for popular SKUs

**Business Rules**:
- Cache most frequently accessed products
- Invalidate cache on product updates
- Cache hit rate target: >90%
- Max cache size: 100,000 products

**Key Metrics**:
- Cache hit rate by layer (L1, L2)
- Cache latency (p95 < 5ms)
- Cache invalidation rate
- Memory utilization

**Related Services**: None (infrastructure)

---

#### L3.6.2: Database Indexing
**Description**: Optimize database indexes for query performance.

**Technical Implementation**:
- Compound indexes for query patterns
- Index on SKU (unique)
- Index on archived status
- Index on dimensions for range queries
- Query profiling and optimization

**Business Rules**:
- All queries must use indexes
- Index selectivity monitored
- Periodic index maintenance
- Query performance SLA: p95 < 50ms

**Key Metrics**:
- Index hit rate (target: 100%)
- Query response time by type
- Database CPU utilization

**Related Services**: None (infrastructure)

---

## L2: Monitoring & Observability

### L2.1: Description
Comprehensive monitoring and observability for operational excellence.

### L2.2: Business Value
- Proactive issue detection
- Performance optimization
- Support for SLA compliance
- Data-driven improvements

### L2.3: L3 Capabilities

#### L3.7.1: Product Metrics Collection
**Description**: Collect and expose comprehensive metrics for product catalog operations.

**Technical Implementation**:
- Prometheus metrics integration
- Custom business metrics
- Grafana dashboards
- Metric-based alerting

**Key Metrics Exposed**:
- `products.total` - Total products in catalog
- `products.created.rate` - Products created per minute
- `products.updated.rate` - Updates per minute
- `products.archived.total` - Archived products count
- `products.query.time` - Query response time
- `products.cache.hit.rate` - Cache effectiveness
- `products.hazmat.total` - Hazmat SKU count

**Related Services**: Infrastructure (Prometheus, Grafana)

---

#### L3.7.2: Health Checks
**Description**: Provide comprehensive health checks for service health monitoring.

**Technical Implementation**:
- Spring Boot Actuator
- MongoDB connectivity check
- Kafka connectivity check
- Custom business health indicators

**Health Endpoints**:
- `/actuator/health/liveness`
- `/actuator/health/readiness`
- `/actuator/health`

**Related Services**: Infrastructure (Kubernetes, load balancers)

---

## Summary

The Product Catalog Service provides comprehensive product master data management through:

### Key Strengths
- **Single Source of Truth**: Canonical product data for entire ecosystem
- **Data Quality**: Comprehensive validation and governance
- **Performance**: Multi-layer caching and optimized queries
- **Compliance**: Hazmat and regulatory information management
- **Integration**: Event-driven synchronization with all services

### Business Impact
- **Catalog Size**: Supports millions of SKUs
- **Data Quality**: >95% validation success rate
- **Performance**: <50ms p95 query latency
- **Cache Efficiency**: >90% cache hit rate
- **Synchronization**: Real-time event propagation (<100ms)

### Integration Points
- **Downstream**: Inventory, Cartonization, Warehouse, Shipment (all consume product events)
- **Events**: Publishes product lifecycle events to `product.catalog.v1.events`

### Domain Model Highlights
- **Product Aggregate**: Root entity with SKU as identifier
- **Dimensions Value Object**: Item and package dimensions
- **ProductAttributes Value Object**: Special handling requirements
- **HazmatInfo Value Object**: Hazardous materials compliance

### Technology Highlights
- Hexagonal architecture with DDD
- CQRS for read/write optimization
- Event-driven integration via Kafka
- Multi-layer caching strategy
- Comprehensive validation framework
