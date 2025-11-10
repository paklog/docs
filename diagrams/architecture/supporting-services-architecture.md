# Supporting Services Architecture

## Product Catalog Service

```mermaid
architecture-beta
    group interface(cloud)[Interface Layer]
    group catalog(server)[Catalog Management]
    group search(server)[Search Engine]
    group storage(database)[Storage]

    service adminUi(server)[Admin UI] in interface
    service apiEndpoint(server)[Catalog API] in interface
    service bulkImport(server)[Bulk Import] in interface

    service catalogCore(disk)[Catalog Core] in catalog
    service skuManager(disk)[SKU Manager] in catalog
    service attributes(disk)[Attribute Engine] in catalog
    service categories(disk)[Category Manager] in catalog
    service pricing(disk)[Pricing Engine] in catalog

    service searchEngine(disk)[Search Engine] in search
    service indexer(disk)[Product Indexer] in search
    service facets(disk)[Facet Engine] in search
    service suggestions(disk)[Suggestions] in search

    service productDb(database)[Product DB] in storage
    service mediaStore(database)[Media Storage] in storage
    service searchIndex(database)[Search Index] in storage
    service cache(database)[Cache Layer] in storage

    adminUi:B --> T:catalogCore
    apiEndpoint:B --> T:catalogCore
    bulkImport:B --> T:skuManager

    catalogCore:R --> L:skuManager
    catalogCore:B --> T:attributes
    catalogCore:R --> L:categories
    catalogCore:B --> T:pricing

    catalogCore:B --> T:searchEngine
    searchEngine:R --> L:indexer
    searchEngine:B --> T:facets
    searchEngine:R --> L:suggestions

    catalogCore:B --> T:productDb
    catalogCore:B --> T:mediaStore
    indexer:B --> T:searchIndex
    catalogCore:R --> L:cache
```

## Cartonization Service

```mermaid
architecture-beta
    group api(cloud)[API Layer]
    group engine(server)[Cartonization Engine]
    group optimization(server)[Optimization]
    group data(database)[Data Layer]

    service restApi(server)[REST API] in api
    service batchApi(server)[Batch API] in api

    service cartonEngine(disk)[Carton Engine] in engine
    service packLogic(disk)[Packing Logic] in engine
    service dimCalculator(disk)[Dimension Calculator] in engine
    service splitLogic(disk)[Order Split Logic] in engine

    service optimizer(disk)[3D Bin Packing] in optimization
    service algorithm(disk)[Packing Algorithm] in optimization
    service simulator(disk)[Pack Simulator] in optimization
    service mlOptimizer(disk)[ML Optimizer] in optimization

    service cartonDb(database)[Carton Database] in data
    service rulesDb(database)[Rules Database] in data
    service metricsDb(database)[Metrics Store] in data
    service cache(database)[Result Cache] in data

    restApi:B --> T:cartonEngine
    batchApi:B --> T:cartonEngine

    cartonEngine:R --> L:packLogic
    cartonEngine:B --> T:dimCalculator
    cartonEngine:R --> L:splitLogic

    cartonEngine:B --> T:optimizer
    optimizer:R --> L:algorithm
    optimizer:B --> T:simulator
    optimizer:R --> L:mlOptimizer

    cartonEngine:B --> T:cartonDb
    packLogic:B --> T:rulesDb
    optimizer:B --> T:metricsDb
    cartonEngine:R --> L:cache
```

## Shipment Transportation Service

```mermaid
architecture-beta
    group interface(cloud)[Integration Layer]
    group management(server)[Shipment Management]
    group carriers(internet)[Carrier Integration]
    group storage(database)[Data Storage]

    service api(server)[Shipment API] in interface
    service tracking(server)[Tracking Portal] in interface
    service edi(server)[EDI Gateway] in interface

    service shipmentCore(disk)[Shipment Core] in management
    service routePlanning(disk)[Route Planning] in management
    service consolidation(disk)[Consolidation Engine] in management
    service documentation(disk)[Doc Generator] in management

    service fedex(internet)[FedEx API] in carriers
    service ups(internet)[UPS API] in carriers
    service usps(internet)[USPS API] in carriers
    service ltl(internet)[LTL Carriers] in carriers

    service shipmentDb(database)[Shipment DB] in storage
    service trackingDb(database)[Tracking DB] in storage
    service documentsDb(database)[Documents Store] in storage
    service rateCache(database)[Rate Cache] in storage

    api:B --> T:shipmentCore
    tracking:B --> T:shipmentCore
    edi:B --> T:shipmentCore

    shipmentCore:R --> L:routePlanning
    shipmentCore:B --> T:consolidation
    shipmentCore:R --> L:documentation

    shipmentCore:B --> T:fedex
    shipmentCore:B --> T:ups
    shipmentCore:B --> T:usps
    shipmentCore:B --> T:ltl

    shipmentCore:B --> T:shipmentDb
    tracking:B --> T:trackingDb
    documentation:B --> T:documentsDb
    shipmentCore:R --> L:rateCache
```

## Yard Management System

```mermaid
architecture-beta
    group gates(cloud)[Gate Operations]
    group yard(server)[Yard Management]
    group docks(server)[Dock Management]
    group data(database)[Data Storage]

    service gateIn(server)[Gate Check-in] in gates
    service gateOut(server)[Gate Check-out] in gates
    service kiosk(server)[Driver Kiosk] in gates
    service cameras(server)[Camera System] in gates

    service yardCore(disk)[Yard Core] in yard
    service slotManager(disk)[Slot Manager] in yard
    service trailerMgmt(disk)[Trailer Management] in yard
    service moveQueue(disk)[Move Queue] in yard
    service yardOptimizer(disk)[Yard Optimizer] in yard

    service dockScheduler(disk)[Dock Scheduler] in docks
    service dockAssignment(disk)[Dock Assignment] in docks
    service loadingMgmt(disk)[Loading Management] in docks
    service sealMgmt(disk)[Seal Management] in docks

    service yardDb(database)[Yard Database] in data
    service appointmentDb(database)[Appointment DB] in data
    service eventLog(queue)[Event Log] in data
    service analytics(database)[Analytics DB] in data

    gateIn:B --> T:yardCore
    gateOut:B --> T:yardCore
    kiosk:B --> T:yardCore
    cameras:R --> L:yardCore

    yardCore:R --> L:slotManager
    yardCore:B --> T:trailerMgmt
    yardCore:R --> L:moveQueue
    yardCore:B --> T:yardOptimizer

    yardCore:B --> T:dockScheduler
    dockScheduler:R --> L:dockAssignment
    dockScheduler:B --> T:loadingMgmt
    loadingMgmt:R --> L:sealMgmt

    yardCore:B --> T:yardDb
    dockScheduler:B --> T:appointmentDb
    yardCore:B --> T:eventLog
    yardOptimizer:B --> T:analytics
```

## Returns Management Service

```mermaid
architecture-beta
    group customer(cloud)[Customer Interface]
    group processing(server)[Returns Processing]
    group disposition(server)[Disposition]
    group storage(database)[Storage]

    service rmaPortal(server)[RMA Portal] in customer
    service customerApi(server)[Customer API] in customer
    service tracking(server)[Return Tracking] in customer

    service returnsCore(disk)[Returns Core] in processing
    service rmaEngine(disk)[RMA Engine] in processing
    service inspection(disk)[Inspection Service] in processing
    service validation(disk)[Validation Engine] in processing

    service disposition(disk)[Disposition Engine] in disposition
    service refund(disk)[Refund Processor] in disposition
    service restock(disk)[Restock Manager] in disposition
    service disposal(disk)[Disposal Handler] in disposition

    service returnsDb(database)[Returns DB] in storage
    service rmaDb(database)[RMA Database] in storage
    service auditLog(database)[Audit Log] in storage
    service metrics(database)[Metrics Store] in storage

    rmaPortal:B --> T:returnsCore
    customerApi:B --> T:returnsCore
    tracking:B --> T:returnsCore

    returnsCore:R --> L:rmaEngine
    returnsCore:B --> T:inspection
    returnsCore:R --> L:validation

    returnsCore:B --> T:disposition
    disposition:R --> L:refund
    disposition:B --> T:restock
    disposition:R --> L:disposal

    returnsCore:B --> T:returnsDb
    rmaEngine:B --> T:rmaDb
    inspection:B --> T:auditLog
    disposition:B --> T:metrics
```