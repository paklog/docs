# PakLog API Documentation

## Table of Contents
1. [API Overview](#api-overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [Wave Planning API](#wave-planning-api)
4. [Task Execution API](#task-execution-api)
5. [Pick Execution API](#pick-execution-api)
6. [Pack & Ship API](#pack--ship-api)
7. [Location Master API](#location-master-api)
8. [Physical Tracking API](#physical-tracking-api)
9. [WebSocket APIs](#websocket-apis)
10. [Error Handling](#error-handling)

---

## API Overview

```mermaid
graph LR
    subgraph "API Structure"
        BASE[Base URL: api.paklog.com]
        V1[/v1]
        V2[/v2]

        subgraph "Services"
            WAVE[/waves]
            TASK[/tasks]
            PICK[/picks]
            PACK[/packing]
            LOC[/locations]
            TRACK[/tracking]
        end
    end

    BASE --> V1
    BASE --> V2
    V1 --> WAVE
    V1 --> TASK
    V1 --> PICK
    V1 --> PACK
    V1 --> LOC
    V1 --> TRACK
```

### Base Configuration

```yaml
servers:
  - url: https://api.paklog.com/v1
    description: Production API
  - url: https://staging-api.paklog.com/v1
    description: Staging API
  - url: http://localhost:8080/v1
    description: Local Development

security:
  - BearerAuth: []
  - ApiKeyAuth: []
  - OAuth2: [read, write]

headers:
  X-Request-ID: string
  X-Correlation-ID: string
  X-Tenant-ID: string
  Accept: application/json
  Content-Type: application/json
```

---

## Authentication & Authorization

### OAuth 2.0 Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant AS as Auth Server
    participant RS as Resource Server
    participant API as PakLog API

    C->>AS: POST /oauth/authorize
    AS->>C: Authorization Code
    C->>AS: POST /oauth/token
    AS->>C: Access Token + Refresh Token
    C->>API: API Request + Bearer Token
    API->>RS: Validate Token
    RS->>API: Token Valid
    API->>C: API Response
```

### Authentication Examples

```bash
# Get Access Token
curl -X POST https://auth.paklog.com/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "scope=read write"

# Response
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "8xLOx1BtZp8F7Y...",
  "scope": "read write"
}

# Use Token in API Call
curl -X GET https://api.paklog.com/v1/waves \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Wave Planning API

### Wave Endpoints

```mermaid
graph TB
    subgraph "Wave Operations"
        CREATE[POST /waves - Create Wave]
        GET[GET /waves/{id} - Get Wave]
        LIST[GET /waves - List Waves]
        RELEASE[POST /waves/{id}/release - Release Wave]
        CANCEL[POST /waves/{id}/cancel - Cancel Wave]
        OPTIMIZE[POST /waves/{id}/optimize - Optimize Wave]
    end
```

### Create Wave

```http
POST /v1/waves
Content-Type: application/json
Authorization: Bearer {token}

{
  "warehouseId": "WH001",
  "type": "STANDARD",
  "strategy": "TIME_BASED",
  "priority": 1,
  "plannedRelease": "2024-01-15T14:00:00Z",
  "orders": [
    {
      "orderId": "ORD-123456",
      "customerId": "CUST-789",
      "priority": "HIGH",
      "requiredDate": "2024-01-16T10:00:00Z",
      "shippingMethod": "NEXT_DAY",
      "orderLines": [
        {
          "productId": "SKU-001",
          "quantity": 10,
          "uom": "EACH"
        }
      ]
    }
  ],
  "configuration": {
    "maxOrders": 100,
    "maxLines": 500,
    "maxVolume": 1000,
    "zoneRestrictions": ["ZONE-A", "ZONE-B"]
  }
}

# Response
HTTP/1.1 201 Created
Location: /v1/waves/WAVE-789012

{
  "waveId": "WAVE-789012",
  "status": "PLANNED",
  "createdAt": "2024-01-15T10:30:00Z",
  "metrics": {
    "totalOrders": 1,
    "totalLines": 1,
    "totalUnits": 10,
    "estimatedPickers": 2,
    "estimatedCompletionTime": "2024-01-15T16:00:00Z"
  },
  "_links": {
    "self": "/v1/waves/WAVE-789012",
    "release": "/v1/waves/WAVE-789012/release",
    "optimize": "/v1/waves/WAVE-789012/optimize"
  }
}
```

### Release Wave

```http
POST /v1/waves/WAVE-789012/release
Authorization: Bearer {token}

{
  "releaseMode": "IMMEDIATE",
  "notifyOperators": true,
  "generateTasks": true
}

# Response
HTTP/1.1 200 OK

{
  "waveId": "WAVE-789012",
  "status": "RELEASED",
  "releasedAt": "2024-01-15T14:00:00Z",
  "tasksGenerated": 25,
  "operatorsNotified": 5,
  "events": [
    {
      "eventType": "WAVE_RELEASED",
      "timestamp": "2024-01-15T14:00:00Z",
      "eventId": "evt-123"
    }
  ]
}
```

---

## Task Execution API

### Task Management

```http
GET /v1/tasks/next
Authorization: Bearer {token}
X-Operator-ID: OP-123

# Response
HTTP/1.1 200 OK

{
  "taskId": "TASK-456789",
  "type": "PICKING",
  "priority": 1,
  "status": "ASSIGNED",
  "assignedTo": "OP-123",
  "location": {
    "locationId": "A-01-02-03",
    "zone": "ZONE-A",
    "aisle": "01",
    "bay": "02",
    "level": "03"
  },
  "items": [
    {
      "productId": "SKU-001",
      "description": "Widget A",
      "quantity": 5,
      "locationId": "A-01-02-03",
      "barcode": "123456789"
    }
  ],
  "estimatedDuration": 300,
  "_links": {
    "self": "/v1/tasks/TASK-456789",
    "start": "/v1/tasks/TASK-456789/start",
    "complete": "/v1/tasks/TASK-456789/complete"
  }
}
```

### Start Task

```http
POST /v1/tasks/TASK-456789/start
Authorization: Bearer {token}

{
  "operatorId": "OP-123",
  "deviceId": "RF-001",
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060
  }
}

# Response
HTTP/1.1 200 OK

{
  "taskId": "TASK-456789",
  "status": "IN_PROGRESS",
  "startedAt": "2024-01-15T14:15:00Z",
  "timer": {
    "elapsed": 0,
    "estimated": 300
  }
}
```

---

## Pick Execution API

### Pick Session Management

```http
POST /v1/picks/sessions
Authorization: Bearer {token}

{
  "operatorId": "OP-123",
  "waveId": "WAVE-789012",
  "type": "SINGLE_ORDER",
  "containerType": "TOTE",
  "containerId": "TOTE-123"
}

# Response
HTTP/1.1 201 Created

{
  "sessionId": "PICK-SESSION-001",
  "status": "READY",
  "pickPath": {
    "totalStops": 5,
    "totalDistance": 250.5,
    "estimatedTime": 900,
    "stops": [
      {
        "sequence": 1,
        "locationId": "A-01-02-03",
        "picks": [
          {
            "pickId": "PICK-001",
            "productId": "SKU-001",
            "quantity": 5
          }
        ]
      }
    ]
  }
}
```

### Execute Pick

```http
POST /v1/picks/sessions/PICK-SESSION-001/picks
Authorization: Bearer {token}

{
  "pickId": "PICK-001",
  "scannedLocation": "A-01-02-03",
  "scannedItems": [
    {
      "barcode": "123456789",
      "quantity": 5
    }
  ],
  "timestamp": "2024-01-15T14:20:00Z"
}

# Response
HTTP/1.1 200 OK

{
  "pickId": "PICK-001",
  "status": "COMPLETED",
  "nextPick": {
    "pickId": "PICK-002",
    "locationId": "A-02-03-01",
    "distance": 45.2
  },
  "sessionProgress": {
    "completed": 1,
    "remaining": 4,
    "percentage": 20
  }
}
```

---

## Pack & Ship API

### Create Packing Session

```http
POST /v1/packing/sessions
Authorization: Bearer {token}

{
  "orderId": "ORD-123456",
  "operatorId": "OP-456",
  "stationId": "PACK-STATION-01",
  "items": [
    {
      "productId": "SKU-001",
      "quantity": 5,
      "serialNumbers": ["SN001", "SN002", "SN003", "SN004", "SN005"]
    }
  ]
}

# Response
HTTP/1.1 201 Created

{
  "sessionId": "PACK-SESSION-123",
  "status": "IN_PROGRESS",
  "suggestedCarton": {
    "cartonType": "MEDIUM_BOX",
    "dimensions": {
      "length": 12,
      "width": 10,
      "height": 8,
      "unit": "INCH"
    },
    "fillRate": 75.5
  }
}
```

### Generate Shipping Label

```http
POST /v1/shipping/labels
Authorization: Bearer {token}

{
  "orderId": "ORD-123456",
  "carrier": "FEDEX",
  "service": "GROUND",
  "packageDetails": {
    "weight": 5.5,
    "weightUnit": "LBS",
    "dimensions": {
      "length": 12,
      "width": 10,
      "height": 8,
      "unit": "INCH"
    }
  },
  "shipTo": {
    "name": "John Doe",
    "address1": "123 Main St",
    "city": "New York",
    "state": "NY",
    "postalCode": "10001",
    "country": "US"
  }
}

# Response
HTTP/1.1 201 Created

{
  "labelId": "LBL-789456",
  "trackingNumber": "1234567890",
  "carrier": "FEDEX",
  "service": "GROUND",
  "cost": 12.50,
  "labelUrl": "/v1/shipping/labels/LBL-789456/download",
  "estimatedDelivery": "2024-01-18T17:00:00Z"
}
```

---

## Location Master API

### Location Management

```http
GET /v1/locations/optimal
Authorization: Bearer {token}

{
  "warehouseId": "WH001",
  "zone": "PICK",
  "slottingClass": "FAST_MOVER",
  "requiredCapacity": 100,
  "productCategory": "ELECTRONICS"
}

# Response
HTTP/1.1 200 OK

{
  "locations": [
    {
      "locationId": "A-01-01-01",
      "type": "BIN",
      "zone": "PICK",
      "slottingClass": "FAST_MOVER",
      "availableCapacity": 150,
      "distanceFromDock": 25.5,
      "score": 95.5,
      "reasons": [
        "Close to shipping dock",
        "High pick frequency zone",
        "Adequate capacity"
      ]
    }
  ]
}
```

### Update Location Status

```http
PATCH /v1/locations/A-01-01-01
Authorization: Bearer {token}

{
  "status": "BLOCKED",
  "reason": "Maintenance required",
  "estimatedAvailable": "2024-01-16T08:00:00Z"
}

# Response
HTTP/1.1 200 OK

{
  "locationId": "A-01-01-01",
  "status": "BLOCKED",
  "previousStatus": "ACTIVE",
  "updatedAt": "2024-01-15T15:00:00Z",
  "updatedBy": "SYSTEM",
  "notification": {
    "sent": true,
    "recipients": ["supervisor@paklog.com"]
  }
}
```

---

## Physical Tracking API

### License Plate Operations

```http
POST /v1/tracking/license-plates
Authorization: Bearer {token}

{
  "type": "PALLET",
  "items": [
    {
      "productId": "SKU-001",
      "quantity": 100,
      "lotNumber": "LOT-2024-001",
      "expiryDate": "2025-01-15"
    }
  ],
  "location": "RECV-01"
}

# Response
HTTP/1.1 201 Created

{
  "lpId": "LP-123456789",
  "sscc": "00123456789012345678",
  "barcode": "data:image/png;base64,iVBORw0KGgoAAAANS...",
  "status": "OPEN",
  "createdAt": "2024-01-15T15:30:00Z"
}
```

### Track Movement

```http
POST /v1/tracking/movements
Authorization: Bearer {token}

{
  "lpId": "LP-123456789",
  "fromLocation": "RECV-01",
  "toLocation": "A-05-10-02",
  "movedBy": "OP-789",
  "reason": "PUTAWAY",
  "equipment": "FORKLIFT-01"
}

# Response
HTTP/1.1 200 OK

{
  "movementId": "MOV-987654",
  "status": "COMPLETED",
  "distance": 125.5,
  "duration": 180,
  "path": [
    {"location": "RECV-01", "timestamp": "2024-01-15T15:35:00Z"},
    {"location": "AISLE-05", "timestamp": "2024-01-15T15:36:30Z"},
    {"location": "A-05-10-02", "timestamp": "2024-01-15T15:38:00Z"}
  ]
}
```

---

## WebSocket APIs

### Real-time Task Updates

```javascript
// WebSocket Connection
const ws = new WebSocket('wss://api.paklog.com/v1/ws');

// Authentication
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'AUTH',
    token: 'Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...'
  }));
};

// Subscribe to Events
ws.send(JSON.stringify({
  type: 'SUBSCRIBE',
  channels: ['tasks', 'picks', 'alerts'],
  filters: {
    warehouseId: 'WH001',
    operatorId: 'OP-123'
  }
}));

// Receive Updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'TASK_ASSIGNED':
      console.log('New task:', data.payload);
      break;

    case 'PICK_COMPLETED':
      console.log('Pick done:', data.payload);
      break;

    case 'ALERT':
      console.log('Alert:', data.payload);
      break;
  }
};

// Example Messages
{
  "type": "TASK_ASSIGNED",
  "timestamp": "2024-01-15T16:00:00Z",
  "payload": {
    "taskId": "TASK-789",
    "type": "PICKING",
    "priority": 1,
    "location": "A-01-02-03"
  }
}
```

---

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "WAVE_001",
    "message": "Wave cannot be released in current state",
    "details": {
      "currentStatus": "DRAFT",
      "requiredStatus": ["PLANNED", "OPTIMIZED"]
    },
    "timestamp": "2024-01-15T16:15:00Z",
    "traceId": "trace-123456",
    "path": "/v1/waves/WAVE-789012/release"
  }
}
```

### Common Error Codes

```mermaid
graph TB
    subgraph "HTTP Status Codes"
        E400[400 Bad Request]
        E401[401 Unauthorized]
        E403[403 Forbidden]
        E404[404 Not Found]
        E409[409 Conflict]
        E422[422 Unprocessable Entity]
        E429[429 Too Many Requests]
        E500[500 Internal Server Error]
        E503[503 Service Unavailable]
    end

    subgraph "Business Error Codes"
        WAVE[WAVE_XXX - Wave errors]
        TASK[TASK_XXX - Task errors]
        PICK[PICK_XXX - Pick errors]
        INV[INV_XXX - Inventory errors]
        LOC[LOC_XXX - Location errors]
    end
```

### Rate Limiting

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1642291200
Retry-After: 3600

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "API rate limit exceeded",
    "details": {
      "limit": 1000,
      "window": "1h",
      "retryAfter": 3600
    }
  }
}
```

### Pagination

```http
GET /v1/waves?page=2&size=20&sort=createdAt,desc
Authorization: Bearer {token}

# Response
HTTP/1.1 200 OK

{
  "content": [...],
  "pageable": {
    "sort": {
      "sorted": true,
      "ascending": false
    },
    "pageNumber": 2,
    "pageSize": 20,
    "offset": 20,
    "paged": true
  },
  "totalElements": 150,
  "totalPages": 8,
  "last": false,
  "first": false,
  "_links": {
    "first": "/v1/waves?page=0&size=20",
    "prev": "/v1/waves?page=1&size=20",
    "self": "/v1/waves?page=2&size=20",
    "next": "/v1/waves?page=3&size=20",
    "last": "/v1/waves?page=7&size=20"
  }
}
```