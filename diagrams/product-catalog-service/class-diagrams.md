# Product Catalog Service - Class Diagrams

## Domain Model Overview

```mermaid
classDiagram
    class Product {
        <<Aggregate Root>>
        -String productId
        -String skuCode
        -String name
        -String description
        -ProductCategory category
        -Brand brand
        -ProductStatus status
        -List~ProductVariant~ variants
        -List~ProductAttribute~ attributes
        -PricingInfo pricing
        -List~ProductImage~ images
        -Dimensions dimensions
        -Weight weight
        -DateTime createdAt
        -DateTime updatedAt
        +create(specification) void
        +update(updates) void
        +addVariant(variant) void
        +addAttribute(attribute) void
        +activate() void
        +discontinue() void
        +validate() ValidationResult
        +clone() Product
    }

    class ProductVariant {
        <<Entity>>
        -String variantId
        -String skuCode
        -Map~String, String~ options
        -VariantPricing pricing
        -StockInfo stockInfo
        -List~String~ images
        -VariantStatus status
        +updateOption(key, value) void
        +updatePrice(price) void
        +isAvailable() boolean
    }

    class ProductAttribute {
        <<Value Object>>
        -String name
        -String value
        -AttributeType type
        -String unit
        -boolean searchable
        -boolean filterable
        -boolean required
        +validate(value) boolean
        +format() String
    }

    class ProductCategory {
        <<Entity>>
        -String categoryId
        -String name
        -String parentCategoryId
        -CategoryPath path
        -List~CategoryAttribute~ attributes
        -int level
        -boolean active
        +getFullPath() String
        +hasParent() boolean
        +getChildren() List~ProductCategory~
    }

    class PricingInfo {
        <<Value Object>>
        -Money basePrice
        -Money salePrice
        -Currency currency
        -List~TierPricing~ tierPricing
        -List~Discount~ discounts
        -DateTime priceEffectiveDate
        +getCurrentPrice() Money
        +getTierPrice(quantity) Money
        +applyDiscount(discount) Money
    }

    class ProductSpecification {
        <<Value Object>>
        -Map~String, String~ technicalSpecs
        -List~Material~ materials
        -List~Certification~ certifications
        -ManufacturerInfo manufacturer
        -WarrantyInfo warranty
        +addSpec(key, value) void
        +hasCertification(type) boolean
    }

    Product "1" --> "*" ProductVariant : has
    Product "1" --> "*" ProductAttribute : contains
    Product "1" --> "1" ProductCategory : belongs to
    Product "1" --> "1" PricingInfo : has
    Product "1" --> "1" ProductSpecification : defines
```

## Product Search and Discovery

```mermaid
classDiagram
    class ProductSearchService {
        <<Domain Service>>
        -SearchEngine searchEngine
        -FilterEngine filterEngine
        -SortingEngine sortingEngine
        +search(query) SearchResult
        +advancedSearch(criteria) SearchResult
        +getSuggestions(prefix) List~Suggestion~
        +getFilters(category) List~Filter~
        -buildSearchQuery(criteria) Query
        -applyFilters(results, filters) SearchResult
    }

    class SearchEngine {
        <<Service>>
        -IndexManager indexManager
        -QueryParser parser
        -Analyzer analyzer
        +indexProduct(product) void
        +search(query) List~SearchHit~
        +moreLikeThis(productId) List~Product~
        -analyzeText(text) List~Token~
        -scoreResults(hits) void
    }

    class FacetEngine {
        <<Service>>
        -FacetBuilder builder
        -AggregationEngine aggregator
        +buildFacets(products) List~Facet~
        +applyFacetFilter(products, facet) List~Product~
        +calculateCounts(facet, products) Map~String, Integer~
    }

    class RecommendationEngine {
        <<Service>>
        -MLModel model
        -SimilarityCalculator calculator
        +getRecommendations(userId) List~Product~
        +getRelatedProducts(productId) List~Product~
        +getTrendingProducts() List~Product~
        -calculateSimilarity(p1, p2) double
        -predictPreference(user, product) double
    }

    class AutocompleteService {
        <<Service>>
        -TrieIndex trie
        -PopularityTracker popularity
        +getSuggestions(prefix) List~String~
        +updatePopularity(term) void
        +rebuildIndex() void
    }

    ProductSearchService --> SearchEngine : uses
    ProductSearchService --> FacetEngine : uses
    ProductSearchService --> RecommendationEngine : consults
    ProductSearchService --> AutocompleteService : uses
```

## Product Information Management

```mermaid
classDiagram
    class ProductInformationManager {
        <<Domain Service>>
        -ValidationService validator
        -EnrichmentService enricher
        -TranslationService translator
        +createProduct(data) Product
        +enrichProduct(productId) void
        +validateProduct(product) ValidationResult
        +translateProduct(productId, language) TranslatedProduct
        -normalizeData(data) NormalizedData
    }

    class ProductEnricher {
        <<Service>>
        -DataSourceConnector connector
        -RuleEngine rules
        +enrich(product) EnrichedProduct
        +fetchManufacturerData(manufacturer) ManufacturerInfo
        +enhanceDescription(description) String
        +generateTags(product) List~Tag~
    }

    class ProductValidator {
        <<Service>>
        -List~ValidationRule~ rules
        -SchemaValidator schema
        +validate(product) ValidationResult
        +validateCompleteness(product) Completeness
        +validateConsistency(product) boolean
        -checkRequiredFields(product) List~Error~
    }

    class BulkOperationService {
        <<Service>>
        -BatchProcessor processor
        -ImportValidator validator
        +bulkImport(file) ImportResult
        +bulkUpdate(updates) UpdateResult
        +bulkExport(criteria) ExportFile
        -processInBatches(items) void
    }

    class VersioningService {
        <<Service>>
        -VersionStore store
        -DiffCalculator differ
        +createVersion(product) Version
        +getHistory(productId) List~Version~
        +compareVersions(v1, v2) Diff
        +rollback(productId, versionId) void
    }

    ProductInformationManager --> ProductEnricher : uses
    ProductInformationManager --> ProductValidator : validates with
    ProductInformationManager --> BulkOperationService : delegates bulk ops
    ProductInformationManager --> VersioningService : tracks versions
```

## Category and Taxonomy Management

```mermaid
classDiagram
    class CategoryManager {
        <<Domain Service>>
        -CategoryRepository repository
        -TaxonomyValidator validator
        +createCategory(category) CategoryId
        +moveCategory(categoryId, newParent) void
        +mergeCategories(source, target) void
        +deleteCategory(categoryId) void
        -validateHierarchy(category) boolean
        -updatePaths(category) void
    }

    class TaxonomyTree {
        <<Entity>>
        -TreeNode root
        -Map~String, TreeNode~ nodeMap
        -int maxDepth
        +addNode(category, parentId) void
        +removeNode(categoryId) void
        +findNode(categoryId) TreeNode
        +getPath(categoryId) List~Category~
        +getDescendants(categoryId) List~Category~
    }

    class CategoryAttribute {
        <<Entity>>
        -String attributeId
        -String name
        -AttributeType type
        -boolean inherited
        -boolean mandatory
        -List~String~ allowedValues
        +validate(value) boolean
        +inherit() CategoryAttribute
    }

    class NavigationBuilder {
        <<Service>>
        -CategoryTree tree
        -FilterService filters
        +buildNavigation(context) Navigation
        +getBreadcrumbs(categoryId) List~Breadcrumb~
        +getCategoryMenu() Menu
        +getCategoryFilters(categoryId) List~Filter~
    }

    CategoryManager --> TaxonomyTree : manages
    TaxonomyTree "1" --> "*" CategoryAttribute : defines
    CategoryManager --> NavigationBuilder : uses
```

## Pricing and Promotions

```mermaid
classDiagram
    class PricingEngine {
        <<Domain Service>>
        -PriceCalculator calculator
        -PromotionEngine promotions
        -TaxCalculator tax
        +calculatePrice(product, quantity, context) Price
        +applyPromotions(price, promotions) Price
        +calculateTax(price, location) Tax
        -selectPricingStrategy(context) PricingStrategy
    }

    class PricingStrategy {
        <<Strategy Interface>>
        +calculatePrice(product, context) Money
    }

    class TieredPricing {
        <<Strategy>>
        -List~PriceTier~ tiers
        +calculatePrice(product, context) Money
        -findApplicableTier(quantity) PriceTier
    }

    class DynamicPricing {
        <<Strategy>>
        -MLPricingModel model
        -MarketDataService market
        +calculatePrice(product, context) Money
        -predictOptimalPrice(product, demand) Money
    }

    class BundlePricing {
        <<Strategy>>
        -BundleConfiguration config
        +calculatePrice(product, context) Money
        -calculateBundleDiscount(items) Money
    }

    class Promotion {
        <<Entity>>
        -String promotionId
        -PromotionType type
        -List~Condition~ conditions
        -DiscountRule discount
        -DateTime startDate
        -DateTime endDate
        -int priority
        +isApplicable(context) boolean
        +apply(price) Money
        +canCombine(other) boolean
    }

    PricingEngine --> PricingStrategy : uses
    PricingStrategy <|.. TieredPricing
    PricingStrategy <|.. DynamicPricing
    PricingStrategy <|.. BundlePricing
    PricingEngine --> Promotion : applies
```

## Media and Content Management

```mermaid
classDiagram
    class MediaManager {
        <<Service>>
        -MediaStorage storage
        -ImageProcessor processor
        -CDNService cdn
        +uploadImage(image) MediaAsset
        +processImage(image, operations) ProcessedImage
        +generateThumbnails(image) List~Thumbnail~
        +getMediaUrl(assetId) URL
        -optimizeImage(image) OptimizedImage
    }

    class MediaAsset {
        <<Entity>>
        -String assetId
        -MediaType type
        -String filename
        -String mimeType
        -long size
        -Dimensions dimensions
        -Map~String, String~ metadata
        -List~MediaVariant~ variants
        +createVariant(specification) MediaVariant
        +getUrl(variant) URL
    }

    class ContentManager {
        <<Service>>
        -ContentRepository repository
        -LocalizationService localizer
        +createContent(content) ContentId
        +localizeContent(contentId, locale) LocalizedContent
        +approveContent(contentId) void
        +publishContent(contentId) void
    }

    class SEOManager {
        <<Service>>
        -MetaDataGenerator generator
        -URLBuilder urlBuilder
        +generateMetaTags(product) MetaTags
        +generateSitemap(products) Sitemap
        +createCanonicalUrl(product) URL
        +generateStructuredData(product) JsonLD
    }

    MediaManager --> MediaAsset : manages
    ContentManager --> MediaManager : uses
    ContentManager --> SEOManager : coordinates
```

## Integration and Events

```mermaid
classDiagram
    class ProductEvent {
        <<Abstract Event>>
        -String eventId
        -String productId
        -DateTime occurredAt
        +getEventType() String
    }

    class ProductCreatedEvent {
        <<Event>>
        -Product product
        -String createdBy
        +getEventType() String
    }

    class ProductUpdatedEvent {
        <<Event>>
        -Map~String, Object~ changes
        -String updatedBy
        +getEventType() String
    }

    class PriceChangedEvent {
        <<Event>>
        -Money oldPrice
        -Money newPrice
        -String reason
        +getEventType() String
    }

    class ProductDiscontinuedEvent {
        <<Event>>
        -String reason
        -DateTime effectiveDate
        +getEventType() String
    }

    class ProductIntegrationService {
        <<Integration Service>>
        -ERPConnector erp
        -MarketplaceConnector marketplaces
        -InventoryConnector inventory
        +syncWithERP() SyncResult
        +publishToMarketplace(product, marketplace) void
        +updateInventory(product, stock) void
        +importFromSupplier(supplierId) List~Product~
    }

    ProductEvent <|-- ProductCreatedEvent
    ProductEvent <|-- ProductUpdatedEvent
    ProductEvent <|-- PriceChangedEvent
    ProductEvent <|-- ProductDiscontinuedEvent
    ProductIntegrationService ..> ProductEvent : publishes
```