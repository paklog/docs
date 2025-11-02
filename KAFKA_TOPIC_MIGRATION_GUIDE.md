# Kafka Topic Migration Guide - Subdomain-Based Naming

## Overview
This document describes the migration from inconsistent Kafka topic naming to a subdomain-based naming convention aligned with Domain-Driven Design bounded contexts.

## Naming Convention

**Pattern**: `{subdomain}.{context}.{event-category}`

Where:
- **subdomain**: The business subdomain (order-fulfillment-core, warehouse-execution, physical-operations, transportation-logistics, support-intelligence)
- **context**: The specific bounded context/service
- **event-category**: The type of events (events, requests, responses, commands)

## Subdomain Mapping

### 1. Order Fulfillment Core
- **order-management**: Not included (separate)
- **inventory**: Not included (separate)
- **cartonization**
- **product-catalog**

### 2. Warehouse Execution
- **wave-planning**
- **task-execution**
- **pick-execution**
- **pack-ship**

### 3. Physical Operations
- **physical-tracking**
- **location-master**
- **robotics-fleet**
- **wes-orchestration**

### 4. Transportation & Logistics
- **shipment-transportation**
- **yard-management**
- **cross-docking**
- **last-mile-delivery**

### 5. Support & Intelligence
- **returns-management**
- **predictive-analytics**
- **workload-planning**
- **quality-compliance**
- **value-added-services**

## Topic Migration Mapping

### Order Fulfillment Core

| Service | Old Topic | New Topic |
|---------|-----------|-----------|
| cartonization | cartonization.requests | order-fulfillment-core.cartonization.requests |
| cartonization | cartonization.responses | order-fulfillment-core.cartonization.responses |
| cartonization | cartonization.solutions | order-fulfillment-core.cartonization.solutions |
| cartonization | cartonization.events | order-fulfillment-core.cartonization.events |
| cartonization | carton.management.requests | order-fulfillment-core.cartonization.management-requests |
| product-catalog | product.events | order-fulfillment-core.product-catalog.events |

### Warehouse Execution

| Service | Old Topic | New Topic |
|---------|-----------|-----------|
| wave-planning | paklog.events | warehouse-execution.wave-planning.events |
| task-execution | wes-task-events | warehouse-execution.task-execution.events |
| task-execution | wms-wave-events | warehouse-execution.wave-planning.events |
| pick-execution | wes-pick-events | warehouse-execution.pick-execution.events |
| pick-execution | wes-task-events | warehouse-execution.task-execution.events |
| pack-ship | wes-pack-events | warehouse-execution.pack-ship.events |
| pack-ship | wes-pick-events | warehouse-execution.pick-execution.events |
| pack-ship | wes-ship-events | warehouse-execution.pack-ship.ship-events |

### Physical Operations

| Service | Old Topic | New Topic |
|---------|-----------|-----------|
| location-master | wms-location-events | physical-operations.location-master.events |
| physical-tracking | wes-tracking-events | physical-operations.physical-tracking.events |
| wes-orchestration | wes.workflow.events | physical-operations.wes-orchestration.workflow-events |
| wes-orchestration | wes.system.events | physical-operations.wes-orchestration.system-events |
| wes-orchestration | wes.integration.events | physical-operations.wes-orchestration.integration-events |

### Transportation & Logistics

| Service | Old Topic | New Topic |
|---------|-----------|-----------|
| shipment-transportation | fulfillment.shipment.v1.events | transportation-logistics.shipment.events |
| cross-docking | crossdock.events | transportation-logistics.cross-docking.events |
| last-mile-delivery | lastmile.events | transportation-logistics.last-mile-delivery.events |

### Support & Intelligence

| Service | Old Topic | New Topic |
|---------|-----------|-----------|
| returns-management | return-events | support-intelligence.returns.events |
| returns-management | order-events | order-fulfillment-core.order-management.events |
| returns-management | notifications | support-intelligence.notifications.events |
| returns-management | fraud-alerts | support-intelligence.returns.fraud-alerts |
| predictive-analytics | analytics.events | support-intelligence.predictive-analytics.events |
| quality-compliance | quality.events | support-intelligence.quality-compliance.events |
| value-added-services | vas.events | support-intelligence.value-added-services.events |

## Migration Strategy

### Phase 1: Dual Publishing (Recommended)
1. Update producers to publish to BOTH old and new topics
2. Update consumers to subscribe to new topics
3. Monitor for 2 weeks
4. Remove old topic publishing

### Phase 2: Direct Migration (For Development)
1. Update all application.yml files with new topic names
2. Update all docker-compose.yml with new topics
3. Recreate Kafka topics
4. Restart all services

## Benefits

1. **Clarity**: Topic names clearly indicate business domain
2. **Organization**: Topics grouped by subdomain
3. **Scalability**: Easy to add new contexts within subdomains
4. **Governance**: Subdomain teams own their topic namespaces
5. **Discovery**: Easier to understand event flows

## Example Event Flow

**Order Fulfillment**:
```
order-fulfillment-core.order-management.events
  ↓
warehouse-execution.wave-planning.events
  ↓
warehouse-execution.task-execution.events
  ↓
warehouse-execution.pick-execution.events
  ↓
warehouse-execution.pack-ship.events
  ↓
transportation-logistics.shipment.events
```
