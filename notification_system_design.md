# Campus Notification System — Architecture Design Document

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Stage 1: REST API Design](#2-stage-1-rest-api-design)
3. [Stage 1: Real-Time Delivery](#3-stage-1-real-time-delivery)
4. [Stage 2: Database Design](#4-stage-2-database-design)
5. [Stage 2: Scalability Planning](#5-stage-2-scalability-planning)

---

## 1. System Overview

A campus-wide notification platform enabling students to receive updates on **placements**, **exam results**, and **events** through REST APIs and real-time delivery channels.

### Core Functionalities

| Module | Description |
|--------|-------------|
| **Notification Management** | Create, update, delete, list notifications |
| **Delivery Tracking** | Track per-student delivery status |
| **Read/Unread Tracking** | Mark as read, fetch unread count |
| **Acknowledgement** | Students confirm receipt of critical notifications |
| **Real-Time Push** | WebSocket/SSE for instant delivery |
| **User Preferences** | Subscribe/unsubscribe to categories |

### Naming Conventions

- **URLs**: lowercase, kebab-case, plural nouns → `/api/v1/notifications`
- **Fields**: camelCase → `createdAt`, `isRead`, `notificationId`
- **Enums**: UPPER_SNAKE → `PLACEMENT`, `RESULT`, `EVENT`
- **Versioning**: URL prefix → `/api/v1/`

---

## 2. Stage 1: REST API Design

### 2.1 Authentication

All endpoints require `Authorization: Bearer <token>` header.

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | `Bearer <JWT>` |
| `Content-Type` | Yes | `application/json` |
| `X-Request-ID` | Optional | Idempotency/tracing key |

### 2.2 Notification Endpoints

#### Create Notification (Admin)

```
POST /api/v1/notifications
```

**Request Body:**
```json
{
  "title": "Placement Drive: Google",
  "body": "Google is visiting campus on June 15. Eligible branches: CSE, IT.",
  "category": "PLACEMENT",
  "priority": "HIGH",
  "targetAudience": {
    "type": "BRANCH",
    "values": ["CSE", "IT"]
  },
  "expiresAt": "2026-06-15T00:00:00Z",
  "requiresAck": true
}
```

**Response: `201 Created`**
```json
{
  "notificationId": "n-abc123",
  "title": "Placement Drive: Google",
  "category": "PLACEMENT",
  "priority": "HIGH",
  "createdAt": "2026-05-16T10:00:00Z",
  "status": "PUBLISHED"
}
```

#### List Notifications (Student)

```
GET /api/v1/notifications?category=PLACEMENT&status=UNREAD&page=1&limit=20&sortBy=createdAt&order=desc
```

**Response: `200 OK`**
```json
{
  "data": [
    {
      "notificationId": "n-abc123",
      "title": "Placement Drive: Google",
      "body": "Google is visiting campus...",
      "category": "PLACEMENT",
      "priority": "HIGH",
      "isRead": false,
      "isAcknowledged": false,
      "createdAt": "2026-05-16T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "totalItems": 47,
    "totalPages": 3,
    "hasNext": true,
    "hasPrev": false
  }
}
```

#### Get Single Notification

```
GET /api/v1/notifications/{notificationId}
```

**Response: `200 OK`** — Full notification object with delivery metadata.

#### Update Notification (Admin)

```
PATCH /api/v1/notifications/{notificationId}
```

**Request:** Partial update fields. **Response: `200 OK`**

#### Delete Notification (Admin)

```
DELETE /api/v1/notifications/{notificationId}
```

**Response: `204 No Content`**

### 2.3 Unread Notification Handling

#### Get Unread Count

```
GET /api/v1/notifications/unread/count
```

**Response: `200 OK`**
```json
{
  "totalUnread": 12,
  "byCategory": {
    "PLACEMENT": 5,
    "RESULT": 3,
    "EVENT": 4
  }
}
```

#### Mark as Read

```
PATCH /api/v1/notifications/{notificationId}/read
```

**Response: `200 OK`**
```json
{
  "notificationId": "n-abc123",
  "isRead": true,
  "readAt": "2026-05-16T12:30:00Z"
}
```

#### Mark All as Read

```
POST /api/v1/notifications/read-all
```

**Request Body (optional filter):**
```json
{ "category": "EVENT" }
```

**Response: `200 OK`**
```json
{ "markedCount": 4 }
```

### 2.4 Acknowledgement Workflow

For critical notifications (placement deadlines, exam schedules) that require confirmation.

#### Acknowledge Notification

```
POST /api/v1/notifications/{notificationId}/acknowledge
```

**Response: `200 OK`**
```json
{
  "notificationId": "n-abc123",
  "isAcknowledged": true,
  "acknowledgedAt": "2026-05-16T13:00:00Z"
}
```

#### Get Acknowledgement Status (Admin)

```
GET /api/v1/notifications/{notificationId}/acknowledgements?page=1&limit=50
```

**Response: `200 OK`**
```json
{
  "notificationId": "n-abc123",
  "totalTargeted": 200,
  "totalAcknowledged": 142,
  "ackRate": 71.0,
  "pending": [
    { "studentId": "s-xyz", "name": "Student A", "branch": "CSE" }
  ]
}
```

### 2.5 Preference Endpoints

```
GET    /api/v1/preferences              → Get student's subscription preferences
PUT    /api/v1/preferences              → Update preferences
```

**PUT Request:**
```json
{
  "categories": {
    "PLACEMENT": { "enabled": true, "channels": ["PUSH", "EMAIL"] },
    "RESULT": { "enabled": true, "channels": ["PUSH"] },
    "EVENT": { "enabled": false, "channels": [] }
  }
}
```

### 2.6 Pagination Strategy

**Cursor-based pagination** for real-time feeds (prevents duplicate/missed items on new inserts):

```
GET /api/v1/notifications?cursor=eyJjcmVhdGVk&limit=20
```

**Offset-based pagination** for admin dashboards (supports random page access):

```
GET /api/v1/admin/notifications?page=3&limit=50
```

| Strategy | Use Case | Pros | Cons |
|----------|----------|------|------|
| Cursor | Student feeds | Consistent with real-time inserts | No random page jump |
| Offset | Admin panels | Simple, supports page jumping | Drift on concurrent writes |

### 2.7 Status Codes

| Code | Usage |
|------|-------|
| `200` | Successful GET, PATCH |
| `201` | Resource created |
| `204` | Successful DELETE |
| `400` | Validation error |
| `401` | Missing/invalid token |
| `403` | Insufficient permissions |
| `404` | Resource not found |
| `409` | Duplicate acknowledgement |
| `422` | Unprocessable entity |
| `429` | Rate limit exceeded |
| `500` | Internal server error |

### 2.8 Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid category value",
    "details": [
      { "field": "category", "issue": "Must be PLACEMENT, RESULT, or EVENT" }
    ]
  },
  "requestId": "req-abc123",
  "timestamp": "2026-05-16T10:00:00Z"
}
```

---

## 3. Stage 1: Real-Time Delivery

### 3.1 Technology Comparison

| Technology | Latency | Scalability | Browser Support | Bidirectional | Best For |
|------------|---------|-------------|-----------------|---------------|----------|
| **WebSocket** | ~50ms | Medium | Universal | Yes | Interactive apps |
| **SSE** | ~100ms | High | Good (no IE) | No | Notification feeds |
| **Push (FCM/APNs)** | ~200ms | Very High | Mobile native | No | Mobile apps |
| **Pub/Sub (Redis)** | ~10ms | Very High | Backend only | N/A | Backend fan-out |

### 3.2 Recommended Architecture: Hybrid Approach

```
                    ┌─────────────────────┐
                    │   Admin / Service    │
                    │  (Creates Notification)│
                    └──────────┬──────────┘
                               │ POST /api/v1/notifications
                               ▼
                    ┌─────────────────────┐
                    │   API Server        │
                    │   (FastAPI)         │
                    └──────────┬──────────┘
                               │ PUBLISH
                               ▼
                    ┌─────────────────────┐
                    │   Redis Pub/Sub     │
                    │   (Message Broker)  │
                    └──────────┬──────────┘
                   ┌───────────┼───────────┐
                   ▼           ▼           ▼
            ┌───────────┐ ┌────────┐ ┌──────────┐
            │ WebSocket │ │  SSE   │ │ Push     │
            │ Server    │ │ Server │ │ (FCM)    │
            └─────┬─────┘ └───┬────┘ └────┬─────┘
                  │            │           │
                  ▼            ▼           ▼
              Browser      Browser      Mobile
              (Active)     (Passive)    (Background)
```

### 3.3 WebSocket Implementation

**Connection:** `ws://api.campus.edu/ws/notifications?token=<JWT>`

**Server → Client Messages:**
```json
{
  "type": "NEW_NOTIFICATION",
  "payload": {
    "notificationId": "n-abc123",
    "title": "Placement Drive: Google",
    "category": "PLACEMENT",
    "priority": "HIGH",
    "preview": "Google is visiting campus on June 15..."
  },
  "timestamp": "2026-05-16T10:00:00Z"
}
```

**Client → Server Messages:**
```json
{ "type": "ACK", "notificationId": "n-abc123" }
{ "type": "MARK_READ", "notificationId": "n-abc123" }
```

**Heartbeat:** Client sends `PING` every 30s, server responds `PONG`. Disconnect after 3 missed pings.

### 3.4 SSE Fallback

For clients that don't support WebSocket:

```
GET /api/v1/notifications/stream
Accept: text/event-stream
Authorization: Bearer <token>
```

```
event: notification
data: {"notificationId":"n-abc123","title":"Placement Drive","category":"PLACEMENT"}

event: unread-count
data: {"totalUnread": 13}
```

### 3.5 Redis Pub/Sub Fan-Out

```python
# Publisher (on notification create)
redis.publish(f"notifications:branch:CSE", json.dumps(notification))
redis.publish(f"notifications:all", json.dumps(notification))

# Subscriber (WebSocket server)
pubsub = redis.pubsub()
pubsub.subscribe(f"notifications:branch:{student.branch}")
for message in pubsub.listen():
    websocket.send(message["data"])
```

### 3.6 Delivery Guarantees

| Level | Strategy |
|-------|----------|
| **At-least-once** | Persist to DB before publishing to Redis |
| **Ordered** | Monotonic notification IDs + client-side dedup |
| **Offline delivery** | On reconnect, fetch unread via REST API |
| **Retry** | Failed push → retry queue with exponential backoff |

---

## 4. Stage 2: Database Design

### 4.1 Database Choice: PostgreSQL

| Criteria | PostgreSQL |
|----------|-----------|
| ACID compliance | Full |
| JSON support | Native JSONB |
| Full-text search | Built-in `tsvector` |
| Partitioning | Declarative (v10+) |
| Replication | Streaming + logical |
| Extensions | `pg_cron`, `pg_stat`, `uuid-ossp` |

PostgreSQL is ideal for this system: strong consistency for delivery tracking, JSONB for flexible notification metadata, and native partitioning for time-series notification data.

### 4.2 Schema Design

#### Entity Relationship Diagram

```
┌──────────────┐     ┌───────────────────┐     ┌──────────────────┐
│   students   │     │  notifications    │     │ delivery_records │
├──────────────┤     ├───────────────────┤     ├──────────────────┤
│ student_id PK│     │ notification_id PK│◄────│ notification_id FK│
│ email        │     │ title             │     │ student_id FK ───►│
│ name         │◄────│ created_by FK     │     │ is_read          │
│ roll_no      │     │ category          │     │ is_acknowledged  │
│ branch       │     │ priority          │     │ read_at          │
│ year         │     │ body              │     │ ack_at           │
│ created_at   │     │ target_audience   │     │ delivered_at     │
└──────────────┘     │ requires_ack      │     │ channel          │
                     │ expires_at        │     └──────────────────┘
                     │ created_at        │
                     └───────────────────┘
```

#### SQL Schema

```sql
-- Students table
CREATE TABLE students (
    student_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) UNIQUE NOT NULL,
    name        VARCHAR(100) NOT NULL,
    roll_no     VARCHAR(20) UNIQUE NOT NULL,
    branch      VARCHAR(10) NOT NULL,  -- CSE, IT, ECE, etc.
    year        SMALLINT NOT NULL CHECK (year BETWEEN 1 AND 5),
    is_active   BOOLEAN DEFAULT true,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Notifications table (partitioned by created_at)
CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           VARCHAR(200) NOT NULL,
    body            TEXT NOT NULL,
    category        VARCHAR(20) NOT NULL CHECK (category IN ('PLACEMENT','RESULT','EVENT')),
    priority        VARCHAR(10) NOT NULL DEFAULT 'NORMAL' CHECK (priority IN ('LOW','NORMAL','HIGH','CRITICAL')),
    target_audience JSONB NOT NULL DEFAULT '{"type":"ALL"}',
    requires_ack    BOOLEAN DEFAULT false,
    created_by      UUID REFERENCES students(student_id),
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Monthly partitions
CREATE TABLE notifications_2026_05 PARTITION OF notifications
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
CREATE TABLE notifications_2026_06 PARTITION OF notifications
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');

-- Delivery records (per-student tracking)
CREATE TABLE delivery_records (
    id              BIGSERIAL,
    notification_id UUID NOT NULL REFERENCES notifications(notification_id) ON DELETE CASCADE,
    student_id      UUID NOT NULL REFERENCES students(student_id),
    is_read         BOOLEAN DEFAULT false,
    is_acknowledged BOOLEAN DEFAULT false,
    channel         VARCHAR(10) DEFAULT 'PUSH' CHECK (channel IN ('PUSH','EMAIL','WS','SSE')),
    delivered_at    TIMESTAMPTZ DEFAULT NOW(),
    read_at         TIMESTAMPTZ,
    ack_at          TIMESTAMPTZ,
    PRIMARY KEY (id, delivered_at),
    UNIQUE (notification_id, student_id)
) PARTITION BY RANGE (delivered_at);

-- Preferences table
CREATE TABLE student_preferences (
    student_id  UUID PRIMARY KEY REFERENCES students(student_id),
    preferences JSONB NOT NULL DEFAULT '{
        "PLACEMENT": {"enabled": true, "channels": ["PUSH","EMAIL"]},
        "RESULT": {"enabled": true, "channels": ["PUSH"]},
        "EVENT": {"enabled": true, "channels": ["PUSH"]}
    }',
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.3 Relationships

| Relationship | Type | Description |
|-------------|------|-------------|
| `students` → `notifications` | 1:M | Admin creates many notifications |
| `notifications` → `delivery_records` | 1:M | One notification → many deliveries |
| `students` → `delivery_records` | 1:M | One student → many delivery records |
| `students` → `student_preferences` | 1:1 | Each student has one preference set |

### 4.4 Example Queries

**Fetch unread notifications for a student:**
```sql
SELECT n.notification_id, n.title, n.category, n.priority, n.created_at
FROM notifications n
JOIN delivery_records dr ON n.notification_id = dr.notification_id
WHERE dr.student_id = $1
  AND dr.is_read = false
  AND (n.expires_at IS NULL OR n.expires_at > NOW())
ORDER BY n.created_at DESC
LIMIT 20;
```

**Get unread count by category:**
```sql
SELECT n.category, COUNT(*) AS unread_count
FROM delivery_records dr
JOIN notifications n ON dr.notification_id = n.notification_id
WHERE dr.student_id = $1 AND dr.is_read = false
GROUP BY n.category;
```

**Mark notification as read:**
```sql
UPDATE delivery_records
SET is_read = true, read_at = NOW()
WHERE notification_id = $1 AND student_id = $2
RETURNING notification_id, is_read, read_at;
```

**Acknowledge a notification:**
```sql
UPDATE delivery_records
SET is_acknowledged = true, ack_at = NOW()
WHERE notification_id = $1 AND student_id = $2 AND is_read = true
RETURNING notification_id, is_acknowledged, ack_at;
```

**Admin: Get acknowledgement stats:**
```sql
SELECT
    COUNT(*) AS total_targeted,
    COUNT(*) FILTER (WHERE is_acknowledged) AS total_acked,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_acknowledged) / COUNT(*), 1) AS ack_rate
FROM delivery_records
WHERE notification_id = $1;
```

**Fan-out: Create delivery records for targeted students:**
```sql
INSERT INTO delivery_records (notification_id, student_id, channel)
SELECT $1, s.student_id, 'PUSH'
FROM students s
WHERE s.is_active = true
  AND s.branch = ANY($2::varchar[])
ON CONFLICT (notification_id, student_id) DO NOTHING;
```

---

## 5. Stage 2: Scalability Planning

### 5.1 Indexing Strategy

```sql
-- Students: lookups by roll_no, branch
CREATE INDEX idx_students_roll ON students(roll_no);
CREATE INDEX idx_students_branch ON students(branch);

-- Notifications: filter by category, sort by date
CREATE INDEX idx_notif_category ON notifications(category);
CREATE INDEX idx_notif_created ON notifications(created_at DESC);
CREATE INDEX idx_notif_expires ON notifications(expires_at) WHERE expires_at IS NOT NULL;

-- Delivery records: THE CRITICAL INDEXES
-- Unread fetch (most frequent query)
CREATE INDEX idx_dr_student_unread ON delivery_records(student_id, is_read)
    WHERE is_read = false;

-- Ack tracking for admins
CREATE INDEX idx_dr_notif_ack ON delivery_records(notification_id, is_acknowledged);

-- Composite for student feed queries
CREATE INDEX idx_dr_student_delivered ON delivery_records(student_id, delivered_at DESC);
```

**Why partial indexes?** The `WHERE is_read = false` index is far smaller than a full index because most notifications eventually get read. This dramatically speeds up the unread count query.

### 5.2 Partitioning

**Time-based range partitioning** on `notifications` and `delivery_records`:

| Table | Partition Key | Interval | Rationale |
|-------|--------------|----------|-----------|
| `notifications` | `created_at` | Monthly | Old notifications rarely queried |
| `delivery_records` | `delivered_at` | Monthly | Bulk of data, enables fast archival |

Benefits:
- **Query pruning**: Queries with date filters only scan relevant partitions
- **Archival**: Drop old partitions instead of expensive DELETE
- **Maintenance**: VACUUM and ANALYZE run per-partition, reducing lock contention

```sql
-- Auto-create future partitions via pg_cron
SELECT cron.schedule('create-monthly-partitions', '0 0 1 * *', $$
    SELECT create_next_month_partitions();
$$);
```

### 5.3 Replication

```
┌─────────────┐    Streaming     ┌─────────────┐
│   Primary   │ ──────────────►  │  Replica 1   │  ← Read queries (student feeds)
│  (Writes)   │                  │  (Hot Standby)│
└─────────────┘    Streaming     ┌─────────────┐
                ──────────────►  │  Replica 2   │  ← Analytics / Admin dashboards
                                 │  (Hot Standby)│
                                 └─────────────┘
```

- **Primary**: All writes (create notification, mark read, acknowledge)
- **Read replicas**: Student feed queries, unread counts, admin dashboards
- **Failover**: Automatic promotion of replica to primary via Patroni/pgBouncer

### 5.4 Caching (Redis)

| Cache Key | TTL | Purpose |
|-----------|-----|---------|
| `unread:{studentId}` | 60s | Unread count (invalidate on read/new) |
| `notif:{notifId}` | 5min | Notification detail (immutable after create) |
| `prefs:{studentId}` | 10min | Student preferences |
| `feed:{studentId}:page1` | 30s | First page of notification feed |

**Cache invalidation strategy**: Write-through on mutations.

```python
# On mark-as-read
async def mark_read(notification_id, student_id):
    await db.execute(UPDATE_QUERY)
    await redis.delete(f"unread:{student_id}")      # Invalidate count
    await redis.delete(f"feed:{student_id}:page1")   # Invalidate feed cache
```

### 5.5 Sharding (Future Scale)

For 100K+ students with millions of delivery records:

**Shard key**: `student_id` (hash-based)

```
student_id hash % 4 → Shard 0, 1, 2, or 3

Shard 0: students A-G → DB cluster 1
Shard 1: students H-M → DB cluster 2
Shard 2: students N-S → DB cluster 3
Shard 3: students T-Z → DB cluster 4
```

**Why student_id?** Most queries are student-scoped (fetch my notifications, my unread count). Sharding by student keeps all of a student's data co-located, avoiding cross-shard joins.

### 5.6 Architecture Summary

```
                         ┌──────────────┐
                         │  Load Balancer│
                         └──────┬───────┘
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │ API Srv 1│ │ API Srv 2│ │ API Srv 3│
              └────┬─────┘ └────┬─────┘ └────┬─────┘
                   └────────────┼────────────┘
                          ┌─────┴─────┐
                          │   Redis   │
                          │ Cache +   │
                          │ Pub/Sub   │
                          └─────┬─────┘
                   ┌────────────┼────────────┐
                   ▼            ▼            ▼
             ┌──────────┐ ┌──────────┐ ┌──────────┐
             │ PG Primary│ │PG Replica│ │PG Replica│
             │ (Writes) │ │ (Reads)  │ │(Analytics)│
             └──────────┘ └──────────┘ └──────────┘
```

**Capacity Estimates (10K students, 50 notifications/day):**

| Metric | Value |
|--------|-------|
| Delivery records/day | 500K (10K × 50) |
| Delivery records/year | ~180M |
| Avg read query latency | <5ms (with index + cache) |
| WebSocket connections | ~3K concurrent (30% online) |
| Redis memory | ~500MB (cached feeds + counts) |

---

*Document version: 1.0 | Roll: 22MIS1084*
