# PakLog Data Flow and Integration Diagrams

## Table of Contents
1. [End-to-End Data Flow](#end-to-end-data-flow)
2. [Event Flow Architecture](#event-flow-architecture)
3. [Integration Patterns](#integration-patterns)
4. [Data Pipeline Architecture](#data-pipeline-architecture)
5. [Real-time Analytics Flow](#real-time-analytics-flow)
6. [ETL/ELT Processes](#etlelt-processes)
7. [External System Integration](#external-system-integration)
8. [API Gateway Flow](#api-gateway-flow)
9. [Event Sourcing Flow](#event-sourcing-flow)
10. [CQRS Implementation](#cqrs-implementation)

---

## End-to-End Data Flow

Complete data flow from order creation to shipment.

```mermaid
flowchart TB
    subgraph "Order Entry"
        O1[E-Commerce Order]
        O2[EDI Order]
        O3[Manual Entry]
        O4[Bulk Import]
    end

    subgraph "Order Processing"
        OP[Order Processor]
        VAL[Validation Engine]
        INV[Inventory Check]
        ALLOC[Allocation Engine]
    end

    subgraph "Wave Management"
        WC[Wave Creator]
        WO[Wave Optimizer]
        WR[Wave Releaser]
    end

    subgraph "Task Generation"
        TG[Task Generator]
        TP[Task Prioritizer]
        TQ[Task Queue]
    end

    subgraph "Execution Layer"
        PICK[Pick Execution]
        PACK[Pack Execution]
        SHIP[Ship Execution]
    end

    subgraph "Data Storage"
        ODB[(Order DB)]
        WDB[(Wave DB)]
        TDB[(Task DB)]
        IDB[(Inventory DB)]
    end

    subgraph "Event Stream"
        KAFKA[Apache Kafka]
        ES[Event Store]
    end

    subgraph "Analytics"
        RT[Real-time Analytics]
        DW[Data Warehouse]
        ML[ML Pipeline]
    end

    O1 --> OP
    O2 --> OP
    O3 --> OP
    O4 --> OP

    OP --> VAL
    VAL --> INV
    INV --> ALLOC
    ALLOC --> ODB

    ODB --> WC
    WC --> WO
    WO --> WR
    WR --> WDB

    WDB --> TG
    TG --> TP
    TP --> TQ
    TQ --> TDB

    TDB --> PICK
    PICK --> PACK
    PACK --> SHIP

    OP -.-> KAFKA
    WR -.-> KAFKA
    TG -.-> KAFKA
    PICK -.-> KAFKA
    PACK -.-> KAFKA
    SHIP -.-> KAFKA

    KAFKA --> ES
    KAFKA --> RT
    ES --> DW
    DW --> ML
```

---

## Event Flow Architecture

Event-driven architecture with Apache Kafka.

```mermaid
flowchart LR
    subgraph "Event Producers"
        subgraph "WMS Services"
            WP[Wave Planning]
            LM[Location Master]
            WL[Workload Planning]
        end

        subgraph "WES Services"
            TE[Task Execution]
            PE[Pick Execution]
            PS[Pack & Ship]
            PT[Physical Tracking]
        end
    end

    subgraph "Event Bus - Kafka"
        subgraph "WMS Topics"
            T1[wave-events]
            T2[order-events]
            T3[inventory-events]
        end

        subgraph "WES Topics"
            T4[task-events]
            T5[pick-events]
            T6[pack-events]
            T7[tracking-events]
        end

        subgraph "Integration Topics"
            T8[external-events]
            T9[audit-events]
            T10[error-events]
        end
    end

    subgraph "Event Consumers"
        subgraph "Service Consumers"
            C1[Task Service]
            C2[Pick Service]
            C3[Pack Service]
        end

        subgraph "Analytics Consumers"
            C4[Stream Processor]
            C5[Analytics Engine]
            C6[ML Pipeline]
        end

        subgraph "Integration Consumers"
            C7[ERP Connector]
            C8[WMS Connector]
            C9[Notification Service]
        end
    end

    WP --> T1
    WP --> T2
    LM --> T3
    WL --> T1

    TE --> T4
    PE --> T5
    PS --> T6
    PT --> T7

    T1 --> C1
    T4 --> C2
    T5 --> C3

    T1 --> C4
    T4 --> C5
    T5 --> C6

    T2 --> C7
    T3 --> C8
    T6 --> C9

    style T1 fill:#f9f,stroke:#333,stroke-width:4px
    style T4 fill:#9ff,stroke:#333,stroke-width:4px
```

---

## Integration Patterns

Common integration patterns used in the system.

```mermaid
graph TB
    subgraph "Message Patterns"
        subgraph "Pub-Sub Pattern"
            PUB[Publisher]
            TOPIC[Topic]
            SUB1[Subscriber 1]
            SUB2[Subscriber 2]
            SUB3[Subscriber 3]
        end

        subgraph "Request-Reply Pattern"
            REQ[Requester]
            QUEUE1[Request Queue]
            PROC[Processor]
            QUEUE2[Reply Queue]
        end

        subgraph "Message Router Pattern"
            SOURCE[Source]
            ROUTER[Content Router]
            DEST1[Destination 1]
            DEST2[Destination 2]
            DEST3[Destination 3]
        end
    end

    subgraph "Data Patterns"
        subgraph "Aggregator Pattern"
            SRC1[Source 1]
            SRC2[Source 2]
            SRC3[Source 3]
            AGG[Aggregator]
            OUT1[Output]
        end

        subgraph "Splitter Pattern"
            IN1[Input]
            SPLIT[Splitter]
            PROC1[Processor 1]
            PROC2[Processor 2]
            PROC3[Processor 3]
        end

        subgraph "Transformation Pattern"
            INPUT[Input Format]
            TRANS[Transformer]
            OUTPUT[Output Format]
        end
    end

    subgraph "Error Patterns"
        subgraph "Circuit Breaker"
            SERVICE[Service]
            CB[Circuit Breaker]
            FALLBACK[Fallback]
        end

        subgraph "Retry Pattern"
            CALLER[Caller]
            RETRY[Retry Logic]
            TARGET[Target Service]
        end

        subgraph "Dead Letter Queue"
            MSG[Message]
            PROCESS[Processor]
            DLQ[Dead Letter Queue]
        end
    end

    PUB --> TOPIC
    TOPIC --> SUB1
    TOPIC --> SUB2
    TOPIC --> SUB3

    REQ --> QUEUE1
    QUEUE1 --> PROC
    PROC --> QUEUE2
    QUEUE2 --> REQ

    SOURCE --> ROUTER
    ROUTER --> DEST1
    ROUTER --> DEST2
    ROUTER --> DEST3

    SRC1 --> AGG
    SRC2 --> AGG
    SRC3 --> AGG
    AGG --> OUT1

    IN1 --> SPLIT
    SPLIT --> PROC1
    SPLIT --> PROC2
    SPLIT --> PROC3

    INPUT --> TRANS
    TRANS --> OUTPUT

    SERVICE --> CB
    CB --> FALLBACK

    CALLER --> RETRY
    RETRY --> TARGET

    MSG --> PROCESS
    PROCESS -.->|Failed| DLQ
```

---

## Data Pipeline Architecture

Data pipeline for batch processing and analytics.

```mermaid
flowchart TB
    subgraph "Data Sources"
        DS1[Operational DB]
        DS2[Event Stream]
        DS3[File Uploads]
        DS4[External APIs]
    end

    subgraph "Ingestion Layer"
        subgraph "Batch Ingestion"
            SQOOP[Sqoop/CDC]
            FTP[File Transfer]
            BATCH[Batch Jobs]
        end

        subgraph "Stream Ingestion"
            KAFKA_IN[Kafka Connect]
            KINESIS[Kinesis]
            PUBSUB[Pub/Sub]
        end
    end

    subgraph "Processing Layer"
        subgraph "Stream Processing"
            SPARK_STREAM[Spark Streaming]
            FLINK[Apache Flink]
            STORM[Storm]
        end

        subgraph "Batch Processing"
            SPARK_BATCH[Spark Batch]
            HADOOP[Hadoop MR]
            PRESTO[Presto]
        end
    end

    subgraph "Storage Layer"
        subgraph "Raw Zone"
            S3_RAW[S3 Raw Data]
            HDFS_RAW[HDFS Raw]
        end

        subgraph "Processed Zone"
            S3_PROC[S3 Processed]
            PARQUET[Parquet Files]
        end

        subgraph "Curated Zone"
            DW_TABLES[DW Tables]
            MARTS[Data Marts]
        end
    end

    subgraph "Serving Layer"
        subgraph "Analytics"
            OLAP[OLAP Cubes]
            BI[BI Tools]
            REPORTS[Reports]
        end

        subgraph "ML Serving"
            MODEL_STORE[Model Store]
            FEATURE_STORE[Feature Store]
            INFERENCE[Inference API]
        end

        subgraph "APIs"
            REST_API[REST APIs]
            GRAPHQL[GraphQL]
            GRPC[gRPC]
        end
    end

    DS1 --> SQOOP
    DS2 --> KAFKA_IN
    DS3 --> FTP
    DS4 --> BATCH

    SQOOP --> S3_RAW
    KAFKA_IN --> SPARK_STREAM
    FTP --> HDFS_RAW
    BATCH --> S3_RAW

    S3_RAW --> SPARK_BATCH
    HDFS_RAW --> HADOOP
    SPARK_STREAM --> S3_PROC

    SPARK_BATCH --> PARQUET
    HADOOP --> PARQUET
    PARQUET --> PRESTO

    PRESTO --> DW_TABLES
    DW_TABLES --> MARTS

    MARTS --> OLAP
    OLAP --> BI
    BI --> REPORTS

    PARQUET --> FEATURE_STORE
    FEATURE_STORE --> MODEL_STORE
    MODEL_STORE --> INFERENCE

    MARTS --> REST_API
    MARTS --> GRAPHQL
    INFERENCE --> GRPC
```

---

## Real-time Analytics Flow

Real-time analytics and monitoring pipeline.

```mermaid
flowchart LR
    subgraph "Event Sources"
        APP[Applications]
        IOT[IoT Devices]
        SCAN[RF Scanners]
        WEB[Web Events]
    end

    subgraph "Stream Ingestion"
        KAFKA_STREAM[Kafka Streams]
        CEP[Complex Event Processing]
    end

    subgraph "Real-time Processing"
        subgraph "Stream Analytics"
            WINDOW[Window Functions]
            AGG_RT[Real-time Aggregation]
            JOIN[Stream Joins]
        end

        subgraph "ML Pipeline"
            FEATURE[Feature Extraction]
            SCORING[Model Scoring]
            ANOMALY[Anomaly Detection]
        end
    end

    subgraph "Real-time Storage"
        REDIS_RT[Redis Streams]
        ELASTIC[Elasticsearch]
        TSDB[Time Series DB]
    end

    subgraph "Real-time Visualization"
        subgraph "Dashboards"
            GRAFANA_RT[Grafana]
            KIBANA[Kibana]
            CUSTOM[Custom Dashboard]
        end

        subgraph "Alerts"
            ALERT_MGR[Alert Manager]
            NOTIFICATION[Notifications]
        end
    end

    subgraph "Actions"
        AUTO[Automation]
        WEBHOOK[Webhooks]
        API_CALL[API Calls]
    end

    APP --> KAFKA_STREAM
    IOT --> KAFKA_STREAM
    SCAN --> KAFKA_STREAM
    WEB --> KAFKA_STREAM

    KAFKA_STREAM --> CEP
    CEP --> WINDOW
    CEP --> AGG_RT
    CEP --> JOIN

    WINDOW --> FEATURE
    AGG_RT --> SCORING
    JOIN --> ANOMALY

    FEATURE --> REDIS_RT
    SCORING --> ELASTIC
    ANOMALY --> TSDB

    REDIS_RT --> GRAFANA_RT
    ELASTIC --> KIBANA
    TSDB --> CUSTOM

    ANOMALY --> ALERT_MGR
    ALERT_MGR --> NOTIFICATION

    ALERT_MGR --> AUTO
    AUTO --> WEBHOOK
    WEBHOOK --> API_CALL
```

---

## ETL/ELT Processes

ETL and ELT data processing pipelines.

```mermaid
flowchart TB
    subgraph "Traditional ETL"
        subgraph "Extract"
            SRC_DB[(Source DB)]
            SRC_FILE[Files]
            SRC_API[APIs]
        end

        subgraph "Transform"
            CLEAN[Data Cleaning]
            VALIDATE[Validation]
            ENRICH[Enrichment]
            CONFORM[Conforming]
        end

        subgraph "Load"
            STAGE[Staging Tables]
            DIM[Dimension Tables]
            FACT[Fact Tables]
            TARGET_DW[(Data Warehouse)]
        end
    end

    subgraph "Modern ELT"
        subgraph "Extract & Load"
            MODERN_SRC[(Sources)]
            LAND[Data Lake Landing]
            RAW_STORE[Raw Storage]
        end

        subgraph "Transform in Place"
            SQL_TRANS[SQL Transforms]
            DBT[dbt Models]
            SPARK_SQL[Spark SQL]
        end

        subgraph "Analytics Ready"
            SILVER[Silver Layer]
            GOLD[Gold Layer]
            SEMANTIC[Semantic Layer]
        end
    end

    subgraph "Orchestration"
        AIRFLOW[Apache Airflow]
        SCHEDULE[Schedulers]
        DEPENDENCIES[Dependencies]
    end

    SRC_DB --> CLEAN
    SRC_FILE --> CLEAN
    SRC_API --> CLEAN

    CLEAN --> VALIDATE
    VALIDATE --> ENRICH
    ENRICH --> CONFORM

    CONFORM --> STAGE
    STAGE --> DIM
    STAGE --> FACT
    DIM --> TARGET_DW
    FACT --> TARGET_DW

    MODERN_SRC --> LAND
    LAND --> RAW_STORE

    RAW_STORE --> SQL_TRANS
    RAW_STORE --> DBT
    RAW_STORE --> SPARK_SQL

    SQL_TRANS --> SILVER
    DBT --> SILVER
    SPARK_SQL --> SILVER

    SILVER --> GOLD
    GOLD --> SEMANTIC

    AIRFLOW --> CLEAN
    AIRFLOW --> SQL_TRANS
    SCHEDULE --> AIRFLOW
    DEPENDENCIES --> SCHEDULE
```

---

## External System Integration

Integration with external systems and partners.

```mermaid
flowchart TB
    subgraph "PakLog Core"
        CORE[Core Services]
        INT_LAYER[Integration Layer]
        API_GW[API Gateway]
    end

    subgraph "ERP Integration"
        ERP[SAP/Oracle ERP]
        ERP_ADAPTER[ERP Adapter]
        ERP_QUEUE[Message Queue]
    end

    subgraph "E-Commerce Integration"
        SHOPIFY[Shopify]
        MAGENTO[Magento]
        CUSTOM_EC[Custom Platform]
        EC_ADAPTER[E-Commerce Adapter]
    end

    subgraph "Carrier Integration"
        FEDEX[FedEx API]
        UPS[UPS API]
        USPS[USPS API]
        CARRIER_ADAPTER[Carrier Adapter]
    end

    subgraph "WMS/3PL Integration"
        WMS_3PL[3PL WMS]
        EDI[EDI Gateway]
        AS2[AS2 Protocol]
        FTP_SERVER[FTP/SFTP]
    end

    subgraph "IoT Integration"
        RFID[RFID Readers]
        SENSORS[Sensors]
        PLC[PLC Systems]
        IOT_GATEWAY[IoT Gateway]
    end

    subgraph "Analytics Integration"
        TABLEAU[Tableau]
        POWERBI[Power BI]
        LOOKER[Looker]
        ANALYTICS_API[Analytics API]
    end

    CORE <--> INT_LAYER
    INT_LAYER <--> API_GW

    ERP <--> ERP_ADAPTER
    ERP_ADAPTER <--> ERP_QUEUE
    ERP_QUEUE <--> INT_LAYER

    SHOPIFY --> EC_ADAPTER
    MAGENTO --> EC_ADAPTER
    CUSTOM_EC --> EC_ADAPTER
    EC_ADAPTER <--> API_GW

    FEDEX --> CARRIER_ADAPTER
    UPS --> CARRIER_ADAPTER
    USPS --> CARRIER_ADAPTER
    CARRIER_ADAPTER <--> API_GW

    WMS_3PL <--> EDI
    EDI <--> AS2
    AS2 <--> FTP_SERVER
    FTP_SERVER <--> INT_LAYER

    RFID --> IOT_GATEWAY
    SENSORS --> IOT_GATEWAY
    PLC --> IOT_GATEWAY
    IOT_GATEWAY --> INT_LAYER

    TABLEAU <--> ANALYTICS_API
    POWERBI <--> ANALYTICS_API
    LOOKER <--> ANALYTICS_API
    ANALYTICS_API <--> API_GW
```

---

## API Gateway Flow

API Gateway request flow and processing.

```mermaid
flowchart TB
    subgraph "Clients"
        WEB_APP[Web Application]
        MOBILE_APP[Mobile App]
        PARTNER[Partner System]
        IOT_DEV[IoT Device]
    end

    subgraph "API Gateway"
        subgraph "Request Processing"
            ROUTE[Request Routing]
            AUTH[Authentication]
            AUTHZ[Authorization]
            RATE[Rate Limiting]
            TRANSFORM[Transform]
        end

        subgraph "Policies"
            CORS[CORS Policy]
            CACHE[Cache Policy]
            RETRY_POL[Retry Policy]
            THROTTLE[Throttle Policy]
        end

        subgraph "Middleware"
            LOG_REQ[Request Logger]
            METRICS_COL[Metrics Collector]
            TRACE[Trace Context]
        end
    end

    subgraph "Backend Services"
        SVC1[Wave Service]
        SVC2[Task Service]
        SVC3[Pick Service]
        SVC4[Pack Service]
    end

    subgraph "Response Processing"
        RESP_TRANS[Response Transform]
        COMPRESS[Compression]
        ENCRYPT[Encryption]
        RESP_CACHE[Response Cache]
    end

    subgraph "Monitoring"
        ACCESS_LOG[Access Logs]
        METRICS_STORE[Metrics Store]
        TRACE_STORE[Trace Store]
    end

    WEB_APP --> ROUTE
    MOBILE_APP --> ROUTE
    PARTNER --> ROUTE
    IOT_DEV --> ROUTE

    ROUTE --> AUTH
    AUTH --> AUTHZ
    AUTHZ --> RATE
    RATE --> TRANSFORM

    TRANSFORM --> CORS
    CORS --> CACHE
    CACHE --> RETRY_POL
    RETRY_POL --> THROTTLE

    THROTTLE --> LOG_REQ
    LOG_REQ --> METRICS_COL
    METRICS_COL --> TRACE

    TRACE --> SVC1
    TRACE --> SVC2
    TRACE --> SVC3
    TRACE --> SVC4

    SVC1 --> RESP_TRANS
    SVC2 --> RESP_TRANS
    SVC3 --> RESP_TRANS
    SVC4 --> RESP_TRANS

    RESP_TRANS --> COMPRESS
    COMPRESS --> ENCRYPT
    ENCRYPT --> RESP_CACHE

    LOG_REQ --> ACCESS_LOG
    METRICS_COL --> METRICS_STORE
    TRACE --> TRACE_STORE
```

---

## Event Sourcing Flow

Event sourcing implementation pattern.

```mermaid
flowchart TB
    subgraph "Command Side"
        CMD[Command]
        CMD_HANDLER[Command Handler]
        AGG[Aggregate]
        VALIDATE_CMD[Validation]
    end

    subgraph "Event Store"
        EVENT_STREAM[Event Stream]
        EVENT_DB[(Event Store DB)]
        SNAPSHOT[Snapshots]
    end

    subgraph "Event Processing"
        EVENT_PROC[Event Processor]
        PROJECTION[Projections]
        SAGA[Saga Orchestrator]
    end

    subgraph "Query Side"
        QUERY[Query]
        READ_MODEL[Read Model]
        VIEW_DB[(View Database)]
        CACHE_LAYER[Cache Layer]
    end

    subgraph "Event Subscribers"
        ANALYTICS_SUB[Analytics]
        AUDIT_SUB[Audit Log]
        INTEGRATION_SUB[Integration]
        NOTIFICATION_SUB[Notifications]
    end

    subgraph "Event Replay"
        REPLAY[Replay Manager]
        REBUILD[Projection Rebuilder]
        REPLAY_FILTER[Event Filter]
    end

    CMD --> CMD_HANDLER
    CMD_HANDLER --> VALIDATE_CMD
    VALIDATE_CMD --> AGG
    AGG --> EVENT_STREAM

    EVENT_STREAM --> EVENT_DB
    EVENT_STREAM --> EVENT_PROC
    EVENT_DB --> SNAPSHOT

    EVENT_PROC --> PROJECTION
    EVENT_PROC --> SAGA
    PROJECTION --> VIEW_DB

    QUERY --> READ_MODEL
    READ_MODEL --> VIEW_DB
    READ_MODEL --> CACHE_LAYER

    EVENT_STREAM --> ANALYTICS_SUB
    EVENT_STREAM --> AUDIT_SUB
    EVENT_STREAM --> INTEGRATION_SUB
    EVENT_STREAM --> NOTIFICATION_SUB

    EVENT_DB --> REPLAY
    REPLAY --> REPLAY_FILTER
    REPLAY_FILTER --> REBUILD
    REBUILD --> VIEW_DB
```

---

## CQRS Implementation

Command Query Responsibility Segregation pattern.

```mermaid
flowchart TB
    subgraph "User Interface"
        UI[UI Layer]
        UI_CMD[Commands]
        UI_QRY[Queries]
    end

    subgraph "Command Side"
        subgraph "Write API"
            CMD_API[Command API]
            CMD_VAL[Command Validator]
            CMD_BUS[Command Bus]
        end

        subgraph "Domain Model"
            AGG_ROOT[Aggregate Root]
            ENTITY[Entities]
            VALUE_OBJ[Value Objects]
            DOMAIN_EVENT[Domain Events]
        end

        subgraph "Write Store"
            WRITE_DB[(Write Database)]
            WRITE_OPT[Write Optimized]
        end
    end

    subgraph "Event Bus"
        EVENT_BUS[Event Stream]
        EVENT_STORE[(Event Store)]
    end

    subgraph "Query Side"
        subgraph "Read API"
            QUERY_API[Query API]
            QUERY_HANDLER[Query Handler]
            QUERY_BUS[Query Bus]
        end

        subgraph "Read Models"
            DENORM[Denormalized Views]
            MATERIALIZED[Materialized Views]
            SEARCH_INDEX[Search Index]
        end

        subgraph "Read Store"
            READ_DB[(Read Database)]
            READ_OPT[Read Optimized]
            ELASTIC_SEARCH[Elasticsearch]
        end
    end

    subgraph "Synchronization"
        SYNC[Sync Handler]
        EVENTUAL[Eventual Consistency]
        COMPENSATE[Compensation]
    end

    UI --> UI_CMD
    UI --> UI_QRY

    UI_CMD --> CMD_API
    CMD_API --> CMD_VAL
    CMD_VAL --> CMD_BUS
    CMD_BUS --> AGG_ROOT

    AGG_ROOT --> ENTITY
    AGG_ROOT --> VALUE_OBJ
    AGG_ROOT --> DOMAIN_EVENT

    AGG_ROOT --> WRITE_DB
    WRITE_DB --> WRITE_OPT

    DOMAIN_EVENT --> EVENT_BUS
    EVENT_BUS --> EVENT_STORE

    EVENT_BUS --> SYNC
    SYNC --> DENORM
    SYNC --> MATERIALIZED
    SYNC --> SEARCH_INDEX

    DENORM --> READ_DB
    MATERIALIZED --> READ_DB
    SEARCH_INDEX --> ELASTIC_SEARCH

    UI_QRY --> QUERY_API
    QUERY_API --> QUERY_HANDLER
    QUERY_HANDLER --> QUERY_BUS

    QUERY_BUS --> READ_DB
    QUERY_BUS --> ELASTIC_SEARCH
    READ_DB --> READ_OPT

    SYNC --> EVENTUAL
    EVENTUAL --> COMPENSATE

    style EVENT_BUS fill:#f96,stroke:#333,stroke-width:4px
    style AGG_ROOT fill:#9f9,stroke:#333,stroke-width:4px
```