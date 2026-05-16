# Campus Notification System — Architecture Design Document

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Stage 1: REST API Design](#2-stage-1-rest-api-design)
3. [Stage 1: Real-Time Delivery](#3-stage-1-real-time-delivery)
4. [Stage 2: Database Design](#4-stage-2-database-design)
5. [Stage 2: Scalability Planning](#5-stage-2-scalability-planning)
6. [Stage 3: Query Optimization & Indexing](#6-stage-3-query-optimization--indexing)
7. [Stage 4: High-Scale Retrieval Optimization](#7-stage-4-high-scale-retrieval-optimization)
8. [Stage 5: Reliable Massive Delivery Architecture](#8-stage-5-reliable-massive-delivery-architecture)

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

*Document version: 2.0 | Roll: 22MIS1084*

---

## 6. Stage 3: Query Optimization & Indexing

### 6.1 The Slow Query — Analysis

Consider the following query that fetches unread notifications for a student:

```sql
-- SLOW VERSION (no proper indexes)
SELECT n.notification_id, n.title, n.category, n.priority, n.created_at
FROM notifications n
JOIN delivery_records dr ON n.notification_id = dr.notification_id
WHERE dr.student_id = 'stu-abc-123'
  AND dr.is_read = false
ORDER BY n.created_at DESC
LIMIT 20;
```

On a database with **millions of notifications** and **tens of millions of delivery records**, this query will be extremely slow. Here's why:

### 6.2 Why This Query Is Slow

#### Problem 1: Full Table Scan on `delivery_records`

Without an index on `(student_id, is_read)`, PostgreSQL must perform a **sequential scan** across the entire `delivery_records` table to find rows matching a specific student with `is_read = false`. With 180M+ rows, this scans every single row.

```
Seq Scan on delivery_records  (cost=0.00..4125000.00 rows=180000000)
  Filter: (student_id = 'stu-abc-123' AND is_read = false)
  Rows Removed by Filter: 179,999,800
```

**Impact**: O(N) scan instead of O(log N) index lookup. The query reads millions of irrelevant rows before finding the ~200 matching rows.

#### Problem 2: Inefficient JOIN Without Index Support

The join on `n.notification_id = dr.notification_id` triggers a **Nested Loop** or **Hash Join** against the `notifications` table. Without a covering index, PostgreSQL must perform random I/O lookups for each matched delivery record.

#### Problem 3: Expensive Sorting (`ORDER BY n.created_at DESC`)

After filtering and joining, PostgreSQL must **sort the entire result set** by `created_at DESC` before applying `LIMIT 20`. Without an index that provides pre-sorted data, this requires:

- Materializing all matching rows into memory
- Running an in-memory or disk-based sort (if results exceed `work_mem`)
- Discarding all but 20 rows

```
Sort  (cost=85000.00..85500.00 rows=200000)
  Sort Key: n.created_at DESC
  Sort Method: external merge  Disk: 45MB
```

#### Problem 4: Large Dataset Traversal Cost

The combination of full scan + unsupported join + filesort means the query touches millions of pages on disk. With cold caches, each page read is a physical I/O operation (~10ms on HDD). Total execution can exceed **30+ seconds**.

### 6.3 Optimized Solution — Composite Index

The critical fix is a **composite index** on the `delivery_records` table:

```sql
CREATE INDEX idx_dr_student_read_created
ON delivery_records (student_id, is_read, delivered_at DESC);
```

**Why this specific column order?**

| Position | Column | Reason |
|----------|--------|--------|
| 1st | `student_id` | Equality filter (`=`) — narrows to one student's rows |
| 2nd | `is_read` | Equality filter (`= false`) — narrows to unread only |
| 3rd | `delivered_at DESC` | Sort order — provides pre-sorted results, eliminates filesort |

**Execution with index:**

```
Index Scan using idx_dr_student_read_created on delivery_records
  Index Cond: (student_id = 'stu-abc-123' AND is_read = false)
  Rows: 20 (directly from index, no sort needed)
  Execution Time: 0.8ms
```

**Before vs After:**

| Metric | Without Index | With Composite Index |
|--------|--------------|---------------------|
| Scan type | Sequential (full table) | Index scan (targeted) |
| Rows examined | ~180,000,000 | ~200 |
| Sort required | Yes (disk-based) | No (index-ordered) |
| Execution time | 30,000+ ms | < 1 ms |
| I/O pages read | ~500,000 | ~5 |

### 6.4 Optimized Query

```sql
-- OPTIMIZED VERSION
SELECT n.notification_id, n.title, n.category, n.priority, n.created_at
FROM delivery_records dr
JOIN notifications n ON n.notification_id = dr.notification_id
WHERE dr.student_id = $1
  AND dr.is_read = false
ORDER BY dr.delivered_at DESC
LIMIT 20;
```

Key changes:
1. **Lead with `delivery_records`** — the indexed table drives the query
2. **Sort by `dr.delivered_at DESC`** — matches the index, avoids filesort
3. The composite index provides an **Index-Only Scan** path for the WHERE + ORDER BY

### 6.5 Why Indexing Every Column Is BAD

A common misconception is "more indexes = faster queries." This is **wrong**. Here's why:

#### 1. Slower Write Performance (INSERT)

Every `INSERT` must update **every index** on the table. With 10 indexes on `delivery_records`, each insert performs 10 additional B-tree insertions.

```
-- 1 index:  INSERT takes ~0.5ms
-- 5 indexes: INSERT takes ~2.5ms
-- 10 indexes: INSERT takes ~5.0ms (10x slower)
```

For a fan-out of 10K delivery records per notification, this means:
- 1 index: 5 seconds total
- 10 indexes: 50 seconds total — **unacceptable**

#### 2. Slower Update Performance

`UPDATE delivery_records SET is_read = true` must update both the row AND the index entry for `is_read`. With indexes on every column, even a single-column update triggers multiple index modifications.

```
-- UPDATE with 1 index:  ~0.3ms per row
-- UPDATE with 10 indexes: ~3.0ms per row
```

The `mark_read` operation is the most frequent write in this system. Over-indexing makes it 10x slower.

#### 3. Increased Storage Overhead

Each index is a separate B-tree structure stored on disk. For a table with 180M rows:

| Scenario | Table Size | Index Size | Total |
|----------|-----------|------------|-------|
| 2 indexes | 25 GB | 8 GB | 33 GB |
| 5 indexes | 25 GB | 20 GB | 45 GB |
| 10 indexes | 25 GB | 40 GB | **65 GB** |

Indexes can consume **more space than the table itself**, directly increasing storage costs and reducing cache efficiency.

#### 4. Index Maintenance Overhead

PostgreSQL must periodically `VACUUM` and `REINDEX` indexes. More indexes means:
- Longer VACUUM cycles (table locks)
- More WAL (Write-Ahead Log) traffic for replication
- Slower `pg_dump` backups

#### 5. Query Planner Confusion

With too many indexes, the PostgreSQL query planner must evaluate more execution plans. This increases planning time and occasionally leads to **suboptimal plan selection** (choosing a bad index over a sequential scan).

**Best Practice**: Only create indexes that serve specific, frequent query patterns. Prefer composite indexes over single-column indexes.

### 6.6 Required Query: Placement Notifications in Last 7 Days

**Query**: Fetch students who received placement notifications in the last 7 days.

```sql
SELECT DISTINCT
    s.student_id,
    s.name,
    s.roll_no,
    s.branch,
    s.email
FROM students s
JOIN delivery_records dr ON s.student_id = dr.student_id
JOIN notifications n ON dr.notification_id = n.notification_id
WHERE n.category = 'PLACEMENT'
  AND dr.delivered_at >= NOW() - INTERVAL '7 days'
ORDER BY s.name ASC;
```

**Supporting index:**

```sql
-- Composite index for category + time range filtering
CREATE INDEX idx_notif_category_created
ON notifications (category, created_at DESC);

-- Delivery records by time range (partition-pruned)
CREATE INDEX idx_dr_delivered_at
ON delivery_records (delivered_at DESC);
```

**Execution plan:**

1. Index scan on `notifications` using `idx_notif_category_created` → filters to `PLACEMENT` type
2. Join to `delivery_records` using `notification_id` FK index → filters by `delivered_at >= 7 days ago`
3. Join to `students` using `student_id` PK → fetches student details
4. `DISTINCT` removes duplicates (one student may receive multiple placement notifications)

**Expected performance:** < 5ms with proper indexes on a table with millions of rows.

---

### 6.7 Summary: Indexing Strategy for This System

| Index | Table | Purpose | Type |
|-------|-------|---------|------|
| `(student_id, is_read, delivered_at DESC)` | `delivery_records` | Unread feed query | Composite |
| `(student_id) WHERE is_read = false` | `delivery_records` | Unread count | Partial |
| `(notification_id, is_acknowledged)` | `delivery_records` | Ack tracking | Composite |
| `(category, created_at DESC)` | `notifications` | Category + time filter | Composite |
| `(roll_no)` | `students` | Student lookup | Single |
| `(branch)` | `students` | Branch targeting | Single |

**Total: 6 carefully chosen indexes** — not one per column, but one per **query pattern**.

---

## 7. Stage 4: High-Scale Retrieval Optimization

### Problem Statement

If every student fetches notifications on every page load via a direct DB query, the database faces **N × PageLoads queries/second**. With 10K students loading pages 10 times/day, that's **100K identical queries/day**. This section proposes solutions.

### 7.1 Redis Caching

Cache feeds and unread counts in Redis. Serve from cache on hit; fall back to DB on miss.

```python
async def get_feed(student_id, page=1):
    cache_key = f"feed:{student_id}:p{page}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)       # Cache HIT
    result = await db.fetch_feed(student_id, page)
    await redis.setex(cache_key, 60, json.dumps(result))  # TTL 60s
    return result
```

| Aspect | Detail |
|--------|--------|
| **Advantage** | 95%+ hit rate; sub-ms reads; massive DB load reduction |
| **Disadvantage** | Staleness up to TTL; memory cost; invalidation complexity |
| **Tradeoff** | 60s staleness is acceptable for most campus notifications |
| **Performance** | DB queries reduced ~95%; p99 latency 50ms → 1ms |

### 7.2 Pagination

Never return full history. Fetch 20 items per page.

```sql
-- Cursor-based (efficient for feeds)
SELECT * FROM notifications WHERE created_at < $cursor
ORDER BY created_at DESC LIMIT 20;
```

| Aspect | Detail |
|--------|--------|
| **Advantage** | Constant query time with indexes; predictable response size |
| **Disadvantage** | Cursor requires client state; no random page jumps |
| **Tradeoff** | Cursor is 100x faster at deep pages but harder to implement |
| **Performance** | Scans 20 rows instead of 10K+; response 500KB → 5KB |

### 7.3 Infinite Scrolling

Load next page automatically when user scrolls to bottom. Combines with cursor pagination.

```javascript
observer.observe(sentinelElement);
async function loadMore() {
    const data = await fetch(`/api/v1/notifications?cursor=${lastCursor}&limit=20`);
    appendToDOM(data);
    lastCursor = data.pagination.nextCursor;
}
```

| Aspect | Detail |
|--------|--------|
| **Advantage** | Smooth UX; loads data only when needed |
| **Disadvantage** | Hard to bookmark; back-navigation issues |
| **Tradeoff** | Better UX than buttons but requires scroll state management |
| **Performance** | Initial load: 20 items (5KB) vs all (500KB) — 100x reduction |

### 7.4 Lazy Loading

Load previews first (title + category), fetch full body on click.

```
Initial:  GET /notifications?fields=id,title,category,createdAt  (lightweight)
On click: GET /notifications/{id}  (full body)
```

| Aspect | Detail |
|--------|--------|
| **Advantage** | Faster initial render; reduced bandwidth |
| **Disadvantage** | Extra roundtrip on expand |
| **Tradeoff** | One extra call per opened notification; saves bandwidth for 90% unread |
| **Performance** | Initial payload 80% smaller |

### 7.5 WebSockets Instead of Polling

Replace `setInterval` polling with persistent WebSocket. Server pushes only on new events.

```
POLLING:    12 req/min/user → 120K req/min for 10K users
WEBSOCKET:  ~50 messages/day/user (push on event only)
```

| Aspect | Detail |
|--------|--------|
| **Advantage** | Real-time; eliminates 99.9% of polling requests |
| **Disadvantage** | ~50KB memory per connection; sticky sessions needed |
| **Tradeoff** | 3K concurrent WS = 150MB RAM vs 120K HTTP req/min |
| **Performance** | DB queries for updates drop from 120K/min to near-zero |

### 7.6 Read Replicas

Route all reads to PostgreSQL replicas. Only writes go to primary.

```python
def get_db(operation):
    if operation == "read":
        return replica_pool.acquire()
    return primary_pool.acquire()
```

| Aspect | Detail |
|--------|--------|
| **Advantage** | Horizontally scale read capacity |
| **Disadvantage** | 100-500ms replication lag; read-after-write inconsistency |
| **Tradeoff** | Student may not see "mark read" for 500ms — acceptable |
| **Performance** | Primary load reduced 90%+; add replicas as users grow |

### 7.7 Asynchronous Refresh

Pre-compute feeds in background, not at request time.

```python
async def refresh_feeds():
    for student in active_students:
        feed = await db.compute_feed(student.id)
        await redis.setex(f"feed:{student.id}:p1", 120, json.dumps(feed))
```

| Aspect | Detail |
|--------|--------|
| **Advantage** | Zero DB time at request; consistent response times |
| **Disadvantage** | Stale between refreshes; wasteful for inactive users |
| **Tradeoff** | Best for hot users; can skip inactive students |
| **Performance** | 0ms DB time at request (pure cache) |

### 7.8 Comparison Summary

| Solution | DB Reduction | Latency | Complexity | Best For |
|----------|-------------|---------|------------|----------|
| Redis Cache | 95% | ⬇️ 50x | Medium | All scenarios |
| Pagination | 80% | ⬇️ 10x | Low | Every API |
| Infinite Scroll | 70% | ⬇️ Progressive | Medium | Web/mobile |
| Lazy Loading | 60% | ⬇️ Initial | Low | Detail-heavy |
| WebSockets | 99% vs poll | Real-time | High | Active users |
| Read Replicas | 90% primary | Same | Medium | High reads |
| Async Refresh | 100% at req | Pre-computed | High | Hot feeds |

**Recommended**: Redis + Cursor Pagination + WebSockets + Read Replicas.

---

## 8. Stage 5: Reliable Massive Delivery Architecture

### 8.1 The Flawed Implementation

```python
# BAD: Sequential, coupled, no error handling
def send_notification(notification, users):
    for user in users:                           # 10,000 users
        save_to_database(notification, user)      # DB write
        send_email(user.email, notification)      # Email API
        send_push(user.device_token, notification) # Push API
```

### 8.2 Problems Identified

#### 1. Sequential Bottleneck

Each user processed one at a time. 10K users × 305ms each = **50+ minutes**. API times out.

#### 2. No Retry Mechanism

Email failure at user #3,000 crashes the loop. Users #3,001-10,000 never processed.

#### 3. Poor Fault Tolerance

Single failure (email service down, DB timeout) stops the **entire pipeline**. No channel isolation.

#### 4. Partial Failures → Inconsistent State

DB says "delivered" but student never got the email. No detection or recovery.

#### 5. No Idempotency

Restart after crash at user #5,000 → users #1-5,000 get **duplicate** notifications.

#### 6. Scalability Limitations

Single-threaded. More users = linearly slower. No parallelism.

#### 7. No Async Processing

API blocks for 50+ minutes. Caller gets timeout with no status feedback.

### 8.3 Redesigned Architecture

```
┌─────────────┐
│  API Server  │  POST /notifications → returns in <100ms
└──────┬──────┘
       │ 1. Save notification to DB
       │ 2. Publish fan-out job to queue
       ▼
┌─────────────────────────────────┐
│        Message Queue            │
│   (RabbitMQ / Kafka / Redis)    │
├─────────┬─────────┬─────────────┤
│ email   │  push   │  db_delivery│
│ queue   │  queue  │  queue      │
└────┬────┘────┬────┘──────┬──────┘
     ▼         ▼           ▼
┌─────────┐ ┌─────────┐ ┌──────────┐
│ Email   │ │  Push   │ │ DB Write │
│ Workers │ │ Workers │ │ Workers  │
│ (×5)    │ │ (×3)    │ │ (×3)     │
└────┬────┘ └────┬────┘ └─────┬────┘
     │    On failure:         │
     ▼           ▼            ▼
┌─────────────────────────────────┐
│     Dead Letter Queue (DLQ)     │
│  Failed → retry or alert        │
└─────────────────────────────────┘
```

### 8.4 Technology Choices

| Technology | Use Case | Why |
|------------|----------|-----|
| **RabbitMQ** | Task queues | Reliable delivery, DLQ, ack/nack |
| **Kafka** | Event stream | High throughput, ordered, replayable |
| **Redis Queue** | Lightweight | Simple, fast, good for <100K jobs/day |
| **Celery** | Python workers | Native retry, beat scheduler |

**Recommended**: Celery + RabbitMQ for Python-native async with reliable delivery.

### 8.5 Implementation

#### API Layer (Fast Response)

```python
@app.post("/api/v1/notifications")
async def create_notification(payload):
    notification = await db.insert(payload)
    fan_out_task.delay(notification.id)      # Enqueue, return instantly
    return {"notificationId": notification.id, "status": "QUEUED"}
```

#### Fan-Out Worker

```python
@celery.task(bind=True, max_retries=3)
def fan_out_task(self, notification_id):
    students = db.get_targeted_students(notification_id)
    for student in students:
        deliver_email.delay(notification_id, student.id)
        deliver_push.delay(notification_id, student.id)
        record_delivery.delay(notification_id, student.id)
```

#### Channel Workers with Retry + Idempotency

```python
@celery.task(bind=True, max_retries=5,
             retry_backoff=True, retry_jitter=True)
def deliver_email(self, notification_id, student_id):
    key = f"email:{notification_id}:{student_id}"
    if redis.exists(key):
        return "ALREADY_SENT"           # Idempotency guard
    try:
        email_service.send(student_id, notification_id)
        redis.setex(key, 86400, "sent")
    except EmailServiceDown:
        raise self.retry(countdown=60)  # Retry in 60s
    except InvalidEmail:
        dead_letter.publish(notification_id, student_id, "INVALID_EMAIL")
```

### 8.6 Why Decouple Email, DB, and Push?

| Scenario | Coupled (BAD) | Decoupled (GOOD) |
|----------|---------------|-------------------|
| Email down 10 min | All stop | Only emails queue up |
| Push token expired | Loop crashes | Push worker → DLQ |
| DB timeout | Everything fails | DB retries; others continue |
| Partial failure | Inconsistent state | Independent tracking |

### 8.7 Key Concepts

**Eventual Consistency**: DB at T+0, push at T+2s, email at T+30s. Acceptable — not ACID-critical.

**Retry with Backoff**: 60s → 120s → 240s → 480s → DLQ. Prevents thundering herd.

**Dead Letter Queue**: After max retries, failed jobs go to DLQ for manual inspection, alerting, and compliance auditing.

**Idempotency**: Redis key `email:{notif}:{student}` checked before every send. Re-runs never duplicate.

### 8.8 Performance Comparison

| Metric | Sequential (BAD) | Queue-Based (GOOD) |
|--------|------------------|-------------------|
| 10K deliveries | 50+ minutes | < 30 seconds |
| Failure at #5K | Stops entirely | Only that task retries |
| Email down | All blocked | Emails queue, rest continues |
| Duplicates | High on restart | Zero (idempotency) |
| API response | Timeout | < 100ms |
| Scalability | More users = slower | More workers = faster |

---

*Document version: 3.0 | Roll: 22MIS1084*
