# Shared Services Architecture

## Quality Management Service

```mermaid
architecture-beta
    group interface(cloud)[Quality Interface]
    group inspection(server)[Inspection Engine]
    group compliance(server)[Compliance]
    group data(database)[Data Storage]

    service qcApp(server)[QC Application] in interface
    service mobileQc(server)[Mobile QC] in interface
    service dashboard(server)[QC Dashboard] in interface

    service inspectionEngine(disk)[Inspection Engine] in inspection
    service sampling(disk)[Sampling Logic] in inspection
    service defectMgmt(disk)[Defect Management] in inspection
    service imageAnalysis(disk)[Image Analysis] in inspection

    service compliance(disk)[Compliance Engine] in compliance
    service standards(disk)[Standards Manager] in compliance
    service certification(disk)[Certification Tracker] in compliance
    service reporting(disk)[Report Generator] in compliance

    service qualityDb(database)[Quality Database] in data
    service imageStore(database)[Image Storage] in data
    service auditLog(database)[Audit Log] in data
    service analytics(database)[Analytics DB] in data

    qcApp:B --> T:inspectionEngine
    mobileQc:B --> T:inspectionEngine
    dashboard:R --> L:reporting

    inspectionEngine:R --> L:sampling
    inspectionEngine:B --> T:defectMgmt
    inspectionEngine:R --> L:imageAnalysis

    inspectionEngine:B --> T:compliance
    compliance:R --> L:standards
    compliance:B --> T:certification
    compliance:R --> L:reporting

    inspectionEngine:B --> T:qualityDb
    imageAnalysis:B --> T:imageStore
    compliance:B --> T:auditLog
    reporting:B --> T:analytics
```

## Location Tracking Service

```mermaid
architecture-beta
    group realtime(cloud)[Real-time Interface]
    group tracking(server)[Tracking Core]
    group sync(server)[Synchronization]
    group storage(database)[Storage Layer]

    service rtlsApi(server)[RTLS API] in realtime
    service wsStream(server)[WebSocket Stream] in realtime
    service eventApi(server)[Event API] in realtime

    service trackingCore(disk)[Tracking Core] in tracking
    service stateManager(disk)[State Manager] in tracking
    service changeDetector(disk)[Change Detector] in tracking
    service validator(disk)[State Validator] in tracking

    service syncEngine(disk)[Sync Engine] in sync
    service reconciler(disk)[Reconciler] in sync
    service conflictResolver(disk)[Conflict Resolver] in sync
    service replicator(disk)[Data Replicator] in sync

    service stateDb(database)[State Database] in storage
    service timeseriesDb(database)[Time Series DB] in storage
    service cache(database)[Redis Cache] in storage
    service eventLog(queue)[Event Log] in storage

    rtlsApi:B --> T:trackingCore
    wsStream:B --> T:trackingCore
    eventApi:B --> T:changeDetector

    trackingCore:R --> L:stateManager
    trackingCore:B --> T:changeDetector
    trackingCore:R --> L:validator

    trackingCore:B --> T:syncEngine
    syncEngine:R --> L:reconciler
    syncEngine:B --> T:conflictResolver
    syncEngine:R --> L:replicator

    stateManager:B --> T:stateDb
    changeDetector:B --> T:timeseriesDb
    trackingCore:R --> L:cache
    changeDetector:B --> T:eventLog
```

## Event Bus Architecture (Kafka)

```mermaid
architecture-beta
    group producers(cloud)[Event Producers]
    group kafka(queue)[Kafka Infrastructure]
    group consumers(cloud)[Event Consumers]
    group management(server)[Management]

    service wmsProducer(server)[WMS Services] in producers
    service wesProducer(server)[WES Services] in producers
    service externalProducer(server)[External Systems] in producers

    service broker1(queue)[Broker 1] in kafka
    service broker2(queue)[Broker 2] in kafka
    service broker3(queue)[Broker 3] in kafka
    service zookeeper(database)[Zookeeper] in kafka
    service schemaRegistry(database)[Schema Registry] in kafka

    service wmsConsumer(server)[WMS Consumers] in consumers
    service wesConsumer(server)[WES Consumers] in consumers
    service analyticsConsumer(server)[Analytics Pipeline] in consumers

    service kafkaConnect(disk)[Kafka Connect] in management
    service kafkaStreams(disk)[Kafka Streams] in management
    service monitoring(disk)[Monitoring] in management
    service adminTools(disk)[Admin Tools] in management

    wmsProducer:B --> T:broker1
    wesProducer:B --> T:broker2
    externalProducer:B --> T:broker3

    broker1:R --> L:zookeeper
    broker2:R --> L:zookeeper
    broker3:R --> L:zookeeper

    broker1:B --> T:schemaRegistry
    broker2:B --> T:schemaRegistry
    broker3:B --> T:schemaRegistry

    broker1:B --> T:wmsConsumer
    broker2:B --> T:wesConsumer
    broker3:B --> T:analyticsConsumer

    kafkaConnect:T --> B:broker2
    kafkaStreams:T --> B:broker1
    monitoring:R --> L:broker1
    adminTools:T --> B:zookeeper
```

## Caching Layer Architecture (Redis)

```mermaid
architecture-beta
    group clients(cloud)[Client Applications]
    group redis(database)[Redis Infrastructure]
    group persistence(database)[Persistence]
    group monitoring(server)[Monitoring]

    service wmsClient(server)[WMS Services] in clients
    service wesClient(server)[WES Services] in clients
    service apiGateway(server)[API Gateway] in clients

    service redisMaster(database)[Redis Master] in redis
    service redisSlave1(database)[Redis Slave 1] in redis
    service redisSlave2(database)[Redis Slave 2] in redis
    service sentinel(server)[Redis Sentinel] in redis

    service snapshot(disk)[RDB Snapshots] in persistence
    service aof(disk)[AOF Logs] in persistence
    service backup(disk)[Backup Storage] in persistence

    service metrics(disk)[Metrics Collector] in monitoring
    service alerting(disk)[Alert Manager] in monitoring
    service dashboard(server)[Redis Dashboard] in monitoring

    wmsClient:B --> T:redisMaster
    wesClient:B --> T:redisSlave1
    apiGateway:B --> T:redisSlave2

    redisMaster:R --> L:redisSlave1
    redisMaster:R --> L:redisSlave2
    sentinel:T --> B:redisMaster

    redisMaster:B --> T:snapshot
    redisMaster:B --> T:aof
    snapshot:B --> T:backup

    redisMaster:R --> L:metrics
    metrics:R --> L:alerting
    metrics:B --> T:dashboard
```

## Authentication & Authorization Service

```mermaid
architecture-beta
    group gateway(cloud)[Access Layer]
    group auth(server)[Auth Core]
    group identity(server)[Identity Management]
    group storage(database)[Storage]

    service apiGateway(server)[API Gateway] in gateway
    service oauth(server)[OAuth 2.0] in gateway
    service saml(server)[SAML Provider] in gateway

    service authCore(disk)[Auth Core] in auth
    service jwtManager(disk)[JWT Manager] in auth
    service sessionMgr(disk)[Session Manager] in auth
    service mfa(disk)[MFA Engine] in auth

    service userMgmt(disk)[User Management] in identity
    service roleMgmt(disk)[Role Management] in identity
    service permissionMgmt(disk)[Permission Engine] in identity
    service auditLogger(disk)[Audit Logger] in identity

    service userDb(database)[User Database] in storage
    service sessionStore(database)[Session Store] in storage
    service auditDb(database)[Audit Database] in storage
    service cache(database)[Token Cache] in storage

    apiGateway:B --> T:authCore
    oauth:B --> T:authCore
    saml:B --> T:authCore

    authCore:R --> L:jwtManager
    authCore:B --> T:sessionMgr
    authCore:R --> L:mfa

    authCore:B --> T:userMgmt
    userMgmt:R --> L:roleMgmt
    roleMgmt:R --> L:permissionMgmt
    authCore:B --> T:auditLogger

    userMgmt:B --> T:userDb
    sessionMgr:B --> T:sessionStore
    auditLogger:B --> T:auditDb
    jwtManager:R --> L:cache
```