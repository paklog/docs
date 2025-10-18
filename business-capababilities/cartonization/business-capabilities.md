# Cartonization Service - Business Capabilities

**Service Overview**: The Cartonization Service is responsible for optimizing shipment packaging by selecting the most efficient carton configurations using advanced 3D bin-packing algorithms. It minimizes shipping costs, reduces material waste, and ensures optimal space utilization.

**Architecture**: Hexagonal Architecture (Ports & Adapters)
**Technology Stack**: Spring Boot 3.2, MongoDB, Apache Kafka, Redis
**Domain Model**: Event-driven with domain events published via Kafka

---

## L1: Shipment Optimization

### L1.1: Description
Optimize packaging and cartonization for shipments to minimize costs, reduce waste, and maximize efficiency in the fulfillment process.

### L1.2: Strategic Value
- **Cost Reduction**: Minimize shipping costs by selecting optimal carton sizes
- **Sustainability**: Reduce material waste and environmental impact
- **Operational Efficiency**: Automate complex packing decisions
- **Customer Satisfaction**: Ensure products arrive safely with appropriate packaging

---

## L2: Packing Solution Calculation

### L2.1: Description
Calculate optimal packing solutions for items using 3D bin-packing algorithms, considering item dimensions, carton capacities, and business constraints.

### L2.2: Business Value
- Automatically determine the best carton configuration for any set of items
- Support for complex multi-item orders requiring multiple cartons
- Real-time calculation for immediate fulfillment decisions

### L2.3: L3 Capabilities

#### L3.1.1: 3D Bin-Packing Algorithm
**Description**: Core algorithm that optimally places items within cartons considering three-dimensional constraints.

**Technical Implementation**:
- Uses advanced geometric packing algorithms
- Considers item dimensions (length, width, height)
- Optimizes for space utilization and weight distribution
- Supports rotation and orientation constraints

**Business Rules**:
- Items cannot be compressed or deformed
- Heavier items placed at bottom when possible
- Fragile items receive special handling

**Key Metrics**:
- Space utilization percentage
- Packing efficiency score
- Time to calculate solution

**Related Services**: Product Catalog (item dimensions)

---

#### L3.1.2: Multi-Carton Optimization
**Description**: Determine the optimal distribution of items across multiple cartons when a single carton is insufficient.

**Technical Implementation**:
- Iterative algorithm to distribute items across cartons
- Minimizes total number of cartons needed
- Balances weight across multiple packages

**Business Rules**:
- Minimize number of cartons to reduce shipping costs
- Respect weight limits per carton
- Group related items when possible

**Key Metrics**:
- Total cartons used
- Average carton utilization
- Cost savings vs. naive packing

**Related Services**: Product Catalog (item weights and dimensions)

---

#### L3.1.3: Carton Selection Strategy
**Description**: Select the most appropriate carton type from available inventory based on items to be packed.

**Technical Implementation**:
- Evaluates available carton types from catalog
- Considers internal dimensions and weight capacity
- Selects smallest carton that fits all items

**Business Rules**:
- Prefer smallest viable carton to minimize costs
- Ensure adequate protection for contents
- Consider special handling requirements (fragile, hazmat)

**Key Metrics**:
- Carton selection accuracy
- Dimensional weight optimization
- Void fill reduction

**Related Services**: Product Catalog (carton specifications)

---

#### L3.1.4: Weight-Based Optimization
**Description**: Optimize packing considering weight constraints and carrier weight brackets.

**Technical Implementation**:
- Calculates total package weight including packaging materials
- Considers carrier weight brackets for pricing
- Optimizes to stay below weight breakpoints when possible

**Business Rules**:
- Never exceed maximum carton weight capacity
- Consider dimensional weight calculations
- Account for packaging material weight

**Key Metrics**:
- Weight accuracy
- Dimensional weight utilization
- Cost tier optimization

**Related Services**: Shipment & Transportation (carrier weight brackets)

---

#### L3.1.5: Packing Solution Caching
**Description**: Cache calculated packing solutions for identical item combinations to improve performance.

**Technical Implementation**:
- Redis-based caching layer
- Cache key based on item SKUs and quantities
- TTL-based cache expiration
- Cache warming for common combinations

**Business Rules**:
- Cache solutions for 24 hours (configurable)
- Invalidate cache when carton catalog changes
- Prioritize cache for high-frequency item combinations

**Key Metrics**:
- Cache hit rate
- Response time improvement
- Cache size and memory usage

**Related Services**: None (internal optimization)

---

## L2: Carton Catalog Management

### L2.1: Description
Manage the catalog of available carton types, including dimensions, capacities, and costs.

### L2.2: Business Value
- Maintain centralized carton specifications
- Enable dynamic carton selection based on availability
- Support carton lifecycle management (new types, deprecation)

### L2.3: L3 Capabilities

#### L3.2.1: Carton Type Registration
**Description**: Register new carton types with specifications including dimensions, weight capacity, and costs.

**Technical Implementation**:
- RESTful API for carton CRUD operations
- MongoDB persistence for carton specifications
- Validation of dimension and capacity constraints

**Business Rules**:
- Carton type must have unique identifier
- Internal dimensions must be less than external dimensions
- Weight capacity must be positive

**Key Metrics**:
- Number of active carton types
- Carton type utilization
- Frequency of type additions/removals

**API Endpoints**:
- `POST /api/v1/cartons` - Create carton type
- `PUT /api/v1/cartons/{id}` - Update carton type
- `GET /api/v1/cartons` - List all carton types

**Related Services**: None (master data)

---

#### L3.2.2: Carton Specification Retrieval
**Description**: Retrieve carton specifications for use in packing calculations.

**Technical Implementation**:
- Query interface for carton lookup
- Support for filtering by dimensions, capacity, cost
- Bulk retrieval for optimization algorithms

**Business Rules**:
- Only return active (non-deprecated) cartons by default
- Support filtering by attributes (e.g., heavy-duty, fragile-approved)

**Key Metrics**:
- Query response time
- Most frequently used carton types
- Specification accuracy

**API Endpoints**:
- `GET /api/v1/cartons/{id}` - Get specific carton
- `GET /api/v1/cartons?minDimensions=...` - Filter cartons

**Related Services**: None (data service)

---

#### L3.2.3: Carton Cost Management
**Description**: Manage costs associated with each carton type for cost-based optimization.

**Technical Implementation**:
- Cost attributes stored with each carton type
- Support for cost updates without version changes
- Historical cost tracking

**Business Rules**:
- Costs updated independently of specifications
- Support multiple cost types (material, handling, disposal)
- Effective dating for cost changes

**Key Metrics**:
- Average cost per carton type
- Cost trends over time
- Cost impact on optimization decisions

**Related Services**: None (configuration data)

---

## L2: Event-Driven Integration

### L2.1: Description
Publish domain events to enable asynchronous integration with other fulfillment services.

### L2.2: Business Value
- Enable real-time notification of packing decisions
- Support event-driven orchestration
- Provide audit trail of packing operations

### L2.3: L3 Capabilities

#### L3.3.1: Packing Solution Calculated Event
**Description**: Publish event when a packing solution has been successfully calculated.

**Technical Implementation**:
- CloudEvents format via Kafka
- Includes item list, selected cartons, utilization metrics
- Guaranteed delivery via Kafka durability

**Event Schema**:
```json
{
  "id": "solution-12345",
  "orderId": "ORD-67890",
  "cartons": [
    {
      "cartonType": "SMALL-BOX-001",
      "items": ["SKU-123", "SKU-456"],
      "utilization": 0.85
    }
  ],
  "totalCost": 12.50,
  "calculatedAt": "2025-10-18T10:30:00Z"
}
```

**Business Rules**:
- Event published only after successful solution calculation
- Includes all items and carton assignments
- Contains cost and efficiency metrics

**Key Metrics**:
- Event publishing latency
- Event consumption by downstream services
- Event delivery success rate

**Event Topic**: `fulfillment.cartonization.v1.events`

**Related Services**:
- Warehouse Operations (triggers packing activities)
- Order Management (updates order status)

---

#### L3.3.2: Carton Type Created/Updated Event
**Description**: Publish event when carton catalog is modified.

**Technical Implementation**:
- Event-driven cache invalidation
- Triggers recalculation of affected packing solutions
- CloudEvents format

**Event Schema**:
```json
{
  "id": "carton-type-update-123",
  "cartonTypeId": "LARGE-BOX-002",
  "action": "CREATED|UPDATED|DEPRECATED",
  "dimensions": { "length": 40, "width": 30, "height": 20 },
  "changedAt": "2025-10-18T10:30:00Z"
}
```

**Business Rules**:
- Published immediately upon carton type changes
- Triggers cache invalidation for affected solutions
- Includes before/after state for updates

**Key Metrics**:
- Catalog change frequency
- Cache invalidation impact
- Downstream system sync latency

**Event Topic**: `fulfillment.cartonization.v1.events`

**Related Services**:
- Product Catalog (sync carton data)
- Warehouse Operations (update packing materials)

---

## L2: Performance & Scalability

### L2.1: Description
Ensure the service can handle high-volume packing requests with low latency and high throughput.

### L2.2: Business Value
- Support peak fulfillment periods (holidays, sales events)
- Minimize impact on order processing time
- Enable real-time packing decisions at warehouse stations

### L2.3: L3 Capabilities

#### L3.4.1: Asynchronous Processing
**Description**: Process packing solution requests asynchronously to improve responsiveness.

**Technical Implementation**:
- Spring @Async for non-blocking execution
- Thread pool configuration for concurrent processing
- CompletableFuture for result handling

**Business Rules**:
- Requests processed in priority order (rush orders first)
- Maximum concurrent calculations configurable
- Timeout for long-running calculations

**Key Metrics**:
- Average processing time
- Concurrent request capacity
- Queue depth

**Related Services**: None (internal capability)

---

#### L3.4.2: Caching Strategy
**Description**: Multi-layer caching to minimize redundant calculations.

**Technical Implementation**:
- Redis for distributed cache
- In-memory cache for frequently used data
- Cache-aside pattern implementation
- Intelligent cache warming

**Business Rules**:
- Cache packing solutions for identical item sets
- Invalidate cache on carton catalog changes
- TTL-based expiration (configurable)

**Key Metrics**:
- Cache hit rate (target: >80%)
- Cache memory utilization
- Cache invalidation rate

**Related Services**: None (infrastructure)

---

#### L3.4.3: Solution Pre-calculation
**Description**: Pre-calculate packing solutions for common item combinations during low-traffic periods.

**Technical Implementation**:
- Scheduled background jobs
- Analysis of historical order patterns
- Bulk calculation and cache storage

**Business Rules**:
- Pre-calculate during off-peak hours
- Focus on high-frequency item combinations
- Automatically identify trending combinations

**Key Metrics**:
- Pre-calculation coverage (% of requests served from cache)
- Background job performance
- Storage efficiency

**Related Services**: Order Management (historical data)

---

## L2: Monitoring & Observability

### L2.1: Description
Provide comprehensive monitoring, metrics, and tracing for operational excellence.

### L2.2: Business Value
- Enable proactive issue detection
- Support performance optimization
- Provide business intelligence on packing efficiency

### L2.3: L3 Capabilities

#### L3.5.1: Packing Metrics Collection
**Description**: Collect and expose metrics related to packing operations and efficiency.

**Technical Implementation**:
- Prometheus metrics integration
- Custom metrics for business KPIs
- Real-time metrics dashboards

**Key Metrics Exposed**:
- `cartonization.solution.calculation.time` - Calculation duration
- `cartonization.solution.cartons.count` - Number of cartons per solution
- `cartonization.solution.utilization.avg` - Average space utilization
- `cartonization.cache.hit.rate` - Cache effectiveness
- `cartonization.requests.total` - Total requests processed

**Business Rules**:
- Metrics collected for every request
- Aggregated by time windows (1m, 5m, 1h)
- Alerting on metric thresholds

**Related Services**: Infrastructure (Prometheus, Grafana)

---

#### L3.5.2: Distributed Tracing
**Description**: Trace packing requests across service boundaries for performance analysis.

**Technical Implementation**:
- OpenTelemetry instrumentation
- Trace propagation via headers
- Integration with Tempo

**Business Rules**:
- Trace all requests with correlation IDs
- Include timing for each operation step
- Link to related service traces

**Key Metrics**:
- End-to-end request latency
- Service dependency performance
- Bottleneck identification

**Related Services**: All services (distributed tracing)

---

## L2: Quality & Validation

### L2.1: Description
Ensure packing solutions meet quality standards and business constraints.

### L2.2: Business Value
- Prevent invalid or suboptimal packing decisions
- Ensure compliance with shipping regulations
- Maintain high customer satisfaction

### L2.3: L3 Capabilities

#### L3.6.1: Solution Validation
**Description**: Validate calculated packing solutions against business rules and physical constraints.

**Technical Implementation**:
- Domain validation service
- Rule engine for constraint checking
- Automated solution verification

**Validation Rules**:
- Total item volume ≤ total carton volume
- Total item weight ≤ carton weight capacity
- All items assigned to a carton
- No overlapping items in 3D space
- Fragile items properly protected

**Key Metrics**:
- Validation success rate
- Most common validation failures
- Impact on calculation time

**Related Services**: None (internal validation)

---

#### L3.6.2: Dimensional Accuracy Verification
**Description**: Verify accuracy of dimensional data from product catalog.

**Technical Implementation**:
- Comparison with historical packing data
- Anomaly detection for dimension discrepancies
- Feedback loop to Product Catalog

**Business Rules**:
- Flag items with dimension mismatches
- Recommend dimension corrections
- Track accuracy metrics per SKU

**Key Metrics**:
- Dimension accuracy rate
- Number of flagged discrepancies
- Correction acceptance rate

**Related Services**: Product Catalog (dimension corrections)

---

## Summary

The Cartonization Service provides comprehensive shipment optimization capabilities through:

### Key Strengths
- **Advanced Algorithms**: 3D bin-packing with multi-carton optimization
- **Performance**: Redis caching, async processing, pre-calculation
- **Integration**: Event-driven architecture with Kafka
- **Observability**: Comprehensive metrics and tracing
- **Flexibility**: Configurable carton catalog and optimization strategies

### Business Impact
- **Cost Savings**: 15-30% reduction in shipping costs through optimal carton selection
- **Sustainability**: 25-40% reduction in packaging waste
- **Speed**: Sub-second packing solutions for 95% of orders
- **Scalability**: Supports 10,000+ packing calculations per hour

### Integration Points
- **Upstream**: Product Catalog (item/carton dimensions)
- **Downstream**: Warehouse Operations (packing instructions), Shipment & Transportation (package details)
- **Events**: Publishes packing solutions, carton catalog changes

### Technology Highlights
- Hexagonal architecture for clean separation of concerns
- Domain-driven design with rich domain model
- Event-driven integration via Kafka
- High-performance caching with Redis
- Cloud-native observability stack
