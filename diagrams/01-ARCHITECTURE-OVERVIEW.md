# PakLog WMS/WES Architecture Overview

## Table of Contents
1. [System Context (C4 Level 1)](#system-context-c4-level-1)
2. [Container Architecture (C4 Level 2)](#container-architecture-c4-level-2)
3. [Component Architecture (C4 Level 3)](#component-architecture-c4-level-3)
4. [Deployment Architecture](#deployment-architecture)
5. [Technology Stack](#technology-stack)

---

## System Context (C4 Level 1)

```mermaid
C4Context
    title System Context Diagram - PakLog WMS/WES Platform

    Person(warehouse_manager, "Warehouse Manager", "Plans and monitors warehouse operations")
    Person(warehouse_operator, "Warehouse Operator", "Executes picking, packing, shipping tasks")
    Person(system_admin, "System Admin", "Manages system configuration")
    Person(inventory_analyst, "Inventory Analyst", "Monitors stock levels and locations")

    System(paklog_wms, "PakLog WMS/WES", "Warehouse Management and Execution System")

    System_Ext(erp, "ERP System", "Enterprise Resource Planning")
    System_Ext(ecommerce, "E-Commerce Platform", "Order source")
    System_Ext(tms, "Transportation Management", "Shipping and carriers")
    System_Ext(wcs, "Warehouse Control System", "Equipment automation")
    System_Ext(mobile_devices, "Mobile RF Devices", "Handheld scanners")

    Rel(warehouse_manager, paklog_wms, "Plans waves, monitors KPIs", "Web UI")
    Rel(warehouse_operator, paklog_wms, "Executes tasks", "Mobile App")
    Rel(system_admin, paklog_wms, "Configures", "Admin Portal")
    Rel(inventory_analyst, paklog_wms, "Analyzes", "Reports/API")

    Rel(ecommerce, paklog_wms, "Sends orders", "REST/Events")
    Rel(paklog_wms, erp, "Syncs inventory", "REST/Events")
    Rel(paklog_wms, tms, "Books shipments", "REST API")
    Rel(paklog_wms, wcs, "Controls equipment", "TCP/MQTT")
    Rel(mobile_devices, paklog_wms, "Updates tasks", "REST API")
```

---

## Container Architecture (C4 Level 2)

```mermaid
C4Container
    title Container Diagram - PakLog Microservices Architecture

    Person(user, "Warehouse User", "Any warehouse role")

    Container_Boundary(frontend, "Frontend Applications") {
        Container(web_app, "Web Application", "React", "Dashboard and management UI")
        Container(mobile_app, "Mobile Application", "React Native", "Task execution interface")
        Container(admin_portal, "Admin Portal", "React", "System configuration")
    }

    Container(api_gateway, "API Gateway", "Spring Cloud Gateway", "Routes requests, authentication")

    Container_Boundary(wms_services, "WMS Services") {
        Container(wave_planning, "Wave Planning Service", "Spring Boot", "Wave creation and optimization")
        Container(location_master, "Location Master Service", "Spring Boot", "Location management and slotting")
        Container(workload_planning, "Workload Planning Service", "Spring Boot", "Resource and capacity planning")
    }

    Container_Boundary(wes_services, "WES Services") {
        Container(task_execution, "Task Execution Service", "Spring Boot", "Task orchestration and assignment")
        Container(pick_execution, "Pick Execution Service", "Spring Boot", "Pick session management")
        Container(pack_ship, "Pack & Ship Service", "Spring Boot", "Packing and shipping operations")
        Container(physical_tracking, "Physical Tracking Service", "Spring Boot", "License plate and inventory tracking")
    }

    Container_Boundary(integration, "Integration Layer") {
        Container(event_bus, "Event Bus", "Apache Kafka", "Async event streaming")
        Container(integration_service, "Integration Service", "Spring Boot", "External system adapters")
    }

    Container_Boundary(data_layer, "Data Storage") {
        ContainerDb(mongodb, "Document Store", "MongoDB", "Service data")
        ContainerDb(postgresql, "Relational DB", "PostgreSQL", "Location master data")
        ContainerDb(redis, "Cache/Queue", "Redis", "Task queues, caching")
    }

    Container_Boundary(observability, "Observability") {
        Container(prometheus, "Metrics", "Prometheus", "Metrics collection")
        Container(grafana, "Visualization", "Grafana", "Dashboards")
        Container(loki, "Logs", "Loki", "Log aggregation")
    }

    Rel(user, web_app, "Uses", "HTTPS")
    Rel(user, mobile_app, "Uses", "HTTPS")
    Rel(user, admin_portal, "Configures", "HTTPS")

    Rel(web_app, api_gateway, "API calls", "REST/WebSocket")
    Rel(mobile_app, api_gateway, "API calls", "REST")
    Rel(admin_portal, api_gateway, "API calls", "REST")

    Rel(api_gateway, wave_planning, "Routes", "REST")
    Rel(api_gateway, location_master, "Routes", "REST")
    Rel(api_gateway, task_execution, "Routes", "REST")
    Rel(api_gateway, pick_execution, "Routes", "REST")
    Rel(api_gateway, pack_ship, "Routes", "REST")

    Rel(wave_planning, event_bus, "Publishes", "Events")
    Rel(task_execution, event_bus, "Subscribes/Publishes", "Events")
    Rel(pick_execution, event_bus, "Subscribes/Publishes", "Events")

    Rel(wave_planning, mongodb, "Stores", "TCP")
    Rel(location_master, postgresql, "Stores", "TCP")
    Rel(task_execution, redis, "Queue ops", "TCP")
```

---

## Component Architecture (C4 Level 3)

### Wave Planning Service Components

```mermaid
C4Component
    title Component Diagram - Wave Planning Service

    Container_Boundary(wave_service, "Wave Planning Service") {
        Component(rest_controller, "REST Controller", "Spring MVC", "HTTP endpoints")
        Component(wave_service_comp, "Wave Service", "Spring Service", "Business logic")
        Component(wave_optimizer, "Wave Optimizer", "Spring Component", "Optimization algorithms")
        Component(wave_aggregate, "Wave Aggregate", "DDD Aggregate", "Domain model")
        Component(wave_repository, "Wave Repository", "Spring Data", "Persistence")
        Component(event_publisher, "Event Publisher", "Spring Kafka", "Publishes domain events")
        Component(event_handler, "Event Handler", "Kafka Listener", "Handles external events")
    }

    Container_Ext(kafka, "Apache Kafka", "Event streaming")
    ContainerDb_Ext(mongodb, "MongoDB", "Document store")
    Container_Ext(api_gateway, "API Gateway", "Request routing")

    Rel(api_gateway, rest_controller, "HTTP requests", "REST")
    Rel(rest_controller, wave_service_comp, "Calls", "Method")
    Rel(wave_service_comp, wave_optimizer, "Uses", "Method")
    Rel(wave_service_comp, wave_aggregate, "Manipulates", "Method")
    Rel(wave_aggregate, wave_repository, "Persists", "Method")
    Rel(wave_repository, mongodb, "Stores", "TCP")
    Rel(wave_aggregate, event_publisher, "Emits events", "Method")
    Rel(event_publisher, kafka, "Publishes", "TCP")
    Rel(kafka, event_handler, "Delivers", "TCP")
    Rel(event_handler, wave_service_comp, "Triggers", "Method")
```

### Task Execution Service Components

```mermaid
C4Component
    title Component Diagram - Task Execution Service

    Container_Boundary(task_service, "Task Execution Service") {
        Component(task_controller, "REST Controller", "Spring MVC", "Task API endpoints")
        Component(task_service_comp, "Task Service", "Spring Service", "Task orchestration")
        Component(task_scheduler, "Task Scheduler", "Spring Component", "Priority scheduling")
        Component(assignment_engine, "Assignment Engine", "Spring Component", "Resource matching")
        Component(task_aggregate, "Task Aggregate", "DDD Aggregate", "Task domain model")
        Component(task_repository, "Task Repository", "Spring Data", "MongoDB persistence")
        Component(task_queue, "Task Queue Manager", "Spring Component", "Redis queue operations")
        Component(event_processor, "Event Processor", "Kafka Listener", "Process wave events")
    }

    ContainerDb_Ext(mongodb, "MongoDB", "Task storage")
    ContainerDb_Ext(redis, "Redis", "Priority queues")
    Container_Ext(kafka, "Kafka", "Events")

    Rel(task_controller, task_service_comp, "Uses", "Method")
    Rel(task_service_comp, task_scheduler, "Schedules", "Method")
    Rel(task_scheduler, task_queue, "Manages", "Method")
    Rel(task_queue, redis, "Queue ops", "TCP")
    Rel(task_service_comp, assignment_engine, "Assigns", "Method")
    Rel(task_service_comp, task_aggregate, "Updates", "Method")
    Rel(task_aggregate, task_repository, "Persists", "Method")
    Rel(task_repository, mongodb, "Stores", "TCP")
    Rel(kafka, event_processor, "Events", "TCP")
    Rel(event_processor, task_service_comp, "Creates tasks", "Method")
```

---

## Deployment Architecture

```mermaid
C4Deployment
    title Deployment Diagram - Kubernetes Production Environment

    Deployment_Node(aws, "AWS Cloud", "Amazon Web Services") {
        Deployment_Node(region, "us-east-1", "AWS Region") {
            Deployment_Node(eks, "EKS Cluster", "Kubernetes") {

                Deployment_Node(ingress, "Ingress Controller", "NGINX") {
                    Container(nginx, "NGINX", "Reverse Proxy")
                }

                Deployment_Node(wms_pods, "WMS Namespace", "Kubernetes Namespace") {
                    Deployment_Node(wave_pod, "Wave Planning Pods", "3 replicas") {
                        Container(wave_container, "Wave Planning", "Spring Boot")
                    }
                    Deployment_Node(location_pod, "Location Master Pods", "2 replicas") {
                        Container(location_container, "Location Master", "Spring Boot")
                    }
                }

                Deployment_Node(wes_pods, "WES Namespace", "Kubernetes Namespace") {
                    Deployment_Node(task_pod, "Task Execution Pods", "5 replicas") {
                        Container(task_container, "Task Execution", "Spring Boot")
                    }
                    Deployment_Node(pick_pod, "Pick Execution Pods", "5 replicas") {
                        Container(pick_container, "Pick Execution", "Spring Boot")
                    }
                }

                Deployment_Node(kafka_pods, "Kafka Namespace", "Kubernetes Namespace") {
                    Deployment_Node(kafka_cluster, "Kafka Cluster", "3 brokers") {
                        Container(kafka_broker, "Kafka Broker", "Apache Kafka")
                    }
                }
            }

            Deployment_Node(rds, "RDS", "Managed PostgreSQL") {
                ContainerDb(postgres, "PostgreSQL", "Location data")
            }

            Deployment_Node(documentdb, "DocumentDB", "Managed MongoDB") {
                ContainerDb(docdb, "MongoDB", "Service data")
            }

            Deployment_Node(elasticache, "ElastiCache", "Managed Redis") {
                ContainerDb(redis_cache, "Redis", "Queues and cache")
            }
        }
    }
```

---

## Technology Stack

```mermaid
mindmap
  root((PakLog Stack))
    Backend
      Languages
        Java 21
        SQL
      Frameworks
        Spring Boot 3.2
        Spring Cloud
        Spring Data
      Messaging
        Apache Kafka
        CloudEvents
        WebSocket
      Databases
        MongoDB
        PostgreSQL
        Redis
    Frontend
      Web
        React 18
        TypeScript
        Material-UI
        Redux Toolkit
      Mobile
        React Native
        Expo
        AsyncStorage
    Infrastructure
      Container
        Docker
        Kubernetes
        Helm
      Cloud
        AWS/Azure/GCP
        Terraform
        Service Mesh
      CI/CD
        GitHub Actions
        ArgoCD
        SonarQube
    Observability
      Monitoring
        Prometheus
        Grafana
        AlertManager
      Logging
        Loki
        Fluentd
      Tracing
        Tempo
        OpenTelemetry
```

---

## Service Communication Matrix

```mermaid
quadrantChart
    title Service Communication Patterns
    x-axis Synchronous --> Asynchronous
    y-axis Low Volume --> High Volume
    quadrant-1 REST APIs
    quadrant-2 Event Streaming
    quadrant-3 Batch Processing
    quadrant-4 Real-time Updates
    Wave Planning: [0.3, 0.7]
    Task Execution: [0.7, 0.9]
    Pick Execution: [0.6, 0.8]
    Pack Ship: [0.5, 0.6]
    Location Master: [0.2, 0.3]
    Physical Tracking: [0.8, 0.5]
    Workload Planning: [0.3, 0.4]
```