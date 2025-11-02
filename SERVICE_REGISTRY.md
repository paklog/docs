# PakLog WMS/WES Service Registry

## Overview
This document serves as the authoritative source for all microservice names, ensuring consistency across documentation, code, and infrastructure.

**Total Services: 27**

## Standardized Service Naming Convention

### Naming Rules
1. Use kebab-case for all service names
2. Add `-service` suffix for operational services
3. Use descriptive suffixes for specialized systems (`-platform`, `-engine`, `-hub`, `-system`)
4. No abbreviations except widely recognized ones (WES, API)

## Complete Service Registry

| # | Standard Name | Directory Name | API Path | Category | Description |
|---|--------------|----------------|----------|----------|-------------|
| 1 | inventory-service | inventory | /api/inventory | Foundation | Inventory management and stock control |
| 2 | order-management-service | order-management | /api/orders | Foundation | Order processing and fulfillment |
| 3 | product-catalog-service | product-catalog | /api/products | Foundation | Product information management |
| 4 | cartonization-service | cartonization | /api/cartonization | Foundation | Packing optimization |
| 5 | shipment-transportation-service | shipment-transportation | /api/shipments | Foundation | Outbound logistics |
| 6 | wave-planning-service | wave-planning | /api/waves | Execution | Wave generation and management |
| 7 | task-execution-service | task-execution | /api/tasks | Execution | Unified task management |
| 8 | pick-execution-service | pick-execution | /api/picking | Execution | Pick list execution |
| 9 | pack-ship-service | pack-ship | /api/packing | Execution | Packing and shipping operations |
| 10 | physical-tracking-service | physical-tracking | /api/tracking | Execution | License plate tracking |
| 11 | location-master-service | location-master | /api/locations | Execution | Warehouse location management |
| 12 | workload-planning-service | workload-planning | /api/workload | Execution | Labor planning and forecasting |
| 13 | returns-management-service | returns-management | /api/returns | Operations | Returns and RMA processing |
| 14 | quality-compliance-service | quality-compliance | /api/quality | Operations | Quality control and compliance |
| 15 | value-added-services | value-added-services | /api/vas | Operations | Kitting and customization |
| 16 | cross-docking-operations | cross-docking-operations | /api/cross-dock | Operations | Flow-through operations |
| 17 | last-mile-delivery-service | last-mile-delivery | /api/last-mile | Operations | Final delivery management |
| 18 | robotics-fleet-management | robotics-fleet-management | /api/robotics | Automation | Robot and AGV management |
| 19 | wes-orchestration-engine | wes-orchestration-engine | /api/wes | Automation | Warehouse execution orchestration |
| 20 | equipment-asset-management | equipment-asset-management | /api/equipment | Automation | Equipment lifecycle management |
| 21 | predictive-analytics-platform | predictive-analytics-platform | /api/analytics | Intelligence | ML-based predictions |
| 22 | performance-intelligence | performance-intelligence | /api/performance | Intelligence | KPI and analytics |
| 23 | digital-twin-simulation | digital-twin-simulation | /api/simulation | Intelligence | Virtual warehouse modeling |
| 24 | yard-management-system | yard-management-system | /api/yard | Support | Dock and yard operations |
| 25 | financial-settlement | financial-settlement | /api/billing | Support | Billing and invoicing |
| 26 | sustainability-management | sustainability-management | /api/sustainability | Support | Environmental tracking |
| 27 | customer-experience-hub | customer-experience-hub | /api/customer | Support | Customer portal and engagement |

## Service Categories

### Foundation Services (5)
Core WMS functionality that other services depend on:
- inventory-service
- order-management-service
- product-catalog-service
- cartonization-service
- shipment-transportation-service

### Execution Services (7)
Real-time warehouse execution and coordination:
- wave-planning-service
- task-execution-service
- pick-execution-service
- pack-ship-service
- physical-tracking-service
- location-master-service
- workload-planning-service

### Operations Services (5)
Specialized warehouse operations:
- returns-management-service
- quality-compliance-service
- value-added-services
- cross-docking-operations
- last-mile-delivery-service

### Automation Services (3)
Equipment and automation management:
- robotics-fleet-management
- wes-orchestration-engine
- equipment-asset-management

### Intelligence Services (3)
Analytics and optimization:
- predictive-analytics-platform
- performance-intelligence
- digital-twin-simulation

### Support Services (4)
Supporting business functions:
- yard-management-system
- financial-settlement
- sustainability-management
- customer-experience-hub

## Kafka Topic Naming

Each service uses standardized Kafka topics:

### Pattern
`{service-name}.{event-type}.{version}`

### Examples
- `inventory-service.stock-adjusted.v1`
- `order-management-service.order-allocated.v1`
- `wave-planning-service.wave-released.v1`

## Database Naming

### Pattern
`paklog_{service_name}_db`

### Examples
- `paklog_inventory_service_db`
- `paklog_order_management_service_db`
- `paklog_wave_planning_service_db`

## Container/K8s Naming

### Pattern
- **Deployment**: `{service-name}-deployment`
- **Service**: `{service-name}-svc`
- **ConfigMap**: `{service-name}-config`
- **Secret**: `{service-name}-secret`

### Examples
- `inventory-service-deployment`
- `inventory-service-svc`
- `inventory-service-config`

## Port Allocation

| Service Range | Port Range | Category |
|---------------|------------|----------|
| Foundation | 8001-8010 | Core WMS |
| Execution | 8011-8020 | WES Services |
| Operations | 8021-8030 | Operations |
| Automation | 8031-8040 | Equipment |
| Intelligence | 8041-8050 | Analytics |
| Support | 8051-8060 | Business |
| Gateway | 8080 | API Gateway |
| Admin | 9000-9010 | Admin Tools |

## Migration Notes

### Services Requiring Rename
The following services need to be renamed for consistency:

| Current Name | New Standard Name |
|-------------|-------------------|
| inventory | inventory-service |
| order-management | order-management-service |
| product-catalog | product-catalog-service |
| cartonization | cartonization-service |
| shipment-transportation | shipment-transportation-service |

### Directory Structure
```
/paklog
  /services
    /inventory-service
    /order-management-service
    /wave-planning-service
    ...
  /docs
    /domain-driven-design
      /inventory-service
      /order-management-service
      ...
    /apis
      /inventory-service
      /order-management-service
      ...
```

## Usage Guidelines

1. **Always use the standard name** from this registry in:
   - Documentation
   - Code comments
   - Configuration files
   - Infrastructure definitions

2. **Directory names** should match the standard name

3. **API paths** should use the simplified version without `-service` suffix

4. **Display names** in UIs can use title case with spaces

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-11-01 | Initial service registry with 27 services |

---

**Note**: This is the authoritative source for service naming. Any deviations should be documented and approved through the architecture review process.