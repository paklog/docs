# Paklog API Specifications

This directory contains the OpenAPI and AsyncAPI specifications for all Paklog microservices.

## Directory Structure

Each service has its own subdirectory containing:
- `openapi.yaml` - REST API specification (OpenAPI 3.0)
- `asyncapi.yaml` - Event-driven API specification (AsyncAPI 2.6)

## Services with Complete API Specifications

### Phase 1: Foundation Services (3/3)
| Service | OpenAPI | AsyncAPI | Status |
|---------|---------|----------|--------|
| **cartonization** | ✓ | ✓ | Complete |
| **inventory** | ✓ | ✓ | Complete |
| **order-management** | ✓ | ✓ | Complete |
| **product-catalog** | ✓ | ✓ | Complete |
| **shipment-transportation** | ✓ | ✓ | Complete |

### Phase 2: Warehouse Operations (7/7)
| Service | OpenAPI | AsyncAPI | Status |
|---------|---------|----------|--------|
| **wave-planning-service** | ✓ | ✓ | Complete |
| **task-execution-service** | ✓ | ✓ | Complete |
| **pick-execution-service** | ✓ | ✓ | Complete |
| **pack-ship-service** | ✓ | ✓ | Complete |
| **physical-tracking-service** | ✓ | ✓ | Complete |
| **location-master-service** | ✓ | ✓ | Complete |
| **workload-planning-service** | ✓ | ✓ | Complete |

### Phase 3: Advanced Services (3/3)
| Service | OpenAPI | AsyncAPI | Status |
|---------|---------|----------|--------|
| **returns-management** | ✓ | ✓ | Complete |
| **robotics-fleet-management** | ✓ | ✓ | Complete |
| **wes-orchestration-engine** | ✓ | ✓ | Complete |

### Phase 4: Optimization Services (3/3)
| Service | OpenAPI | AsyncAPI | Status |
|---------|---------|----------|--------|
| **predictive-analytics-platform** | ✗ | ✗ | Pending |
| **yard-management-system** | ✗ | ✓ | Partial |
| **cross-docking-operations** | ✗ | ✓ | Partial |

### Phase 5: Customer & Intelligence Services (9/9)
| Service | OpenAPI | AsyncAPI | Status |
|---------|---------|----------|--------|
| **last-mile-delivery** | ✗ | ✓ | Partial |
| **value-added-services** | ✓ | ✓ | Complete |
| **quality-compliance** | ✓ | ✓ | Complete |
| **digital-twin-simulation** | ✓ | ✓ | Complete |
| **sustainability-management** | ✓ | ✓ | Complete |
| **customer-experience-hub** | ✓ | ✓ | Complete |
| **performance-intelligence** | ✗ | ✗ | Pending |
| **equipment-asset-management** | ✓ | ✓ | Complete |
| **financial-settlement** | ✗ | ✗ | Pending |

## Summary

- **Total Services**: 27
- **Services with Complete API Specs**: 18 (67%)
- **Services with Partial API Specs**: 3 (11%)
- **Services Pending API Specs**: 3 (11%)
- **Services Not Yet Implemented**: 3 (11%)

### Complete Specifications (18 services)
Both OpenAPI and AsyncAPI specifications available:

1. cartonization
2. inventory
3. order-management
4. product-catalog
5. shipment-transportation
6. wave-planning-service
7. task-execution-service
8. pick-execution-service
9. pack-ship-service
10. physical-tracking-service
11. location-master-service
12. workload-planning-service
13. returns-management
14. robotics-fleet-management
15. wes-orchestration-engine
16. value-added-services
17. quality-compliance
18. digital-twin-simulation
19. sustainability-management
20. customer-experience-hub
21. equipment-asset-management

### Partial Specifications (3 services)
AsyncAPI only, OpenAPI pending:

1. yard-management-system (AsyncAPI only)
2. cross-docking-operations (AsyncAPI only)
3. last-mile-delivery (AsyncAPI only)

### Pending Specifications (3 services)
Services implemented but API specs need to be created:

1. performance-intelligence
2. financial-settlement
3. predictive-analytics-platform

## OpenAPI Specifications

OpenAPI specifications define the REST API endpoints for each service, including:
- Request/response schemas
- Authentication requirements
- HTTP methods and paths
- Error responses
- Example payloads

### Viewing OpenAPI Specs
- Use [Swagger UI](https://swagger.io/tools/swagger-ui/)
- Use [Redoc](https://github.com/Redocly/redoc)
- Use [OpenAPI Generator](https://openapi-generator.tech/)

## AsyncAPI Specifications

AsyncAPI specifications define the event-driven APIs, including:
- Kafka topics and channels
- Event schemas (CloudEvents format)
- Message payloads
- Pub/Sub patterns

### Viewing AsyncAPI Specs
- Use [AsyncAPI Studio](https://studio.asyncapi.com/)
- Use [AsyncAPI Generator](https://github.com/asyncapi/generator)

## Integration

All services follow these patterns:
- **OpenAPI 3.0**: REST API specification standard
- **AsyncAPI 2.6**: Event-driven API specification standard
- **CloudEvents 1.0**: Event format standard
- **Kafka**: Message broker for async communication

## Next Steps

To complete the API documentation:
1. Generate OpenAPI specs for 3 partial services (yard-management-system, cross-docking-operations, last-mile-delivery)
2. Generate OpenAPI/AsyncAPI specs for 3 pending services (performance-intelligence, financial-settlement, predictive-analytics-platform)
3. Validate all specs against their respective schemas
4. Generate API documentation using Swagger UI / Redoc
5. Generate SDK clients using OpenAPI Generator
6. Deploy API documentation to GitHub Pages

## Tools

### OpenAPI Tools
```bash
# Validate OpenAPI spec
npx @stoplight/spectral-cli lint openapi.yaml

# Generate API documentation
docker run -p 8080:8080 -v $(pwd):/usr/share/nginx/html/api swaggerapi/swagger-ui

# Generate client SDK
docker run --rm -v $(pwd):/local openapitools/openapi-generator-cli generate \
  -i /local/openapi.yaml \
  -g java \
  -o /local/client
```

### AsyncAPI Tools
```bash
# Validate AsyncAPI spec
npx @asyncapi/cli validate asyncapi.yaml

# Generate documentation
npx @asyncapi/generator asyncapi.yaml @asyncapi/html-template -o ./docs

# Generate code
npx @asyncapi/generator asyncapi.yaml @asyncapi/java-spring-cloud-stream-template -o ./generated
```

## Contributing

When adding API specifications:
1. Place OpenAPI spec in `docs/apis/{service-name}/openapi.yaml`
2. Place AsyncAPI spec in `docs/apis/{service-name}/asyncapi.yaml`
3. Follow existing patterns and naming conventions
4. Validate specs before committing
5. Update this README with the new service status

## References

- [OpenAPI Specification](https://spec.openapis.org/oas/v3.0.3)
- [AsyncAPI Specification](https://www.asyncapi.com/docs/reference/specification/v2.6.0)
- [CloudEvents Specification](https://github.com/cloudevents/spec)
- [Paklog Architecture Documentation](../architecture/)
- [Paklog Domain-Driven Design](../domain-driven-design/)
