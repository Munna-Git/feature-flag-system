# 🚩 Feature Flag Service

A production-grade backend microservice for **controlled feature rollouts** using deterministic hashing, percentage-based strategies, and Redis-backed caching. Built for teams that need to ship fast without breaking things.

> Enable features for 1% of users. Then 10%. Then everyone — all without a single redeployment.

---

## Table of Contents

- [Overview](#overview)
- [Why Feature Flags?](#why-feature-flags)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [System Architecture](#system-architecture)
- [Database Design](#database-design)
- [Rollout Logic](#rollout-logic)
- [Caching Strategy](#caching-strategy)
- [API Reference](#api-reference)
- [Getting Started](#getting-started)
- [Example Walkthrough](#example-walkthrough)
- [Future Improvements](#future-improvements)

---

## Overview

The Feature Flag Service is a backend microservice that lets engineering teams:

- **Gradually roll out** new features to a percentage of users
- **Instantly disable** problematic functionality without redeploying
- **Run A/B tests** and experiments with consistent user targeting
- **Decouple feature releases** from code deployments

It is built with **FastAPI**, **PostgreSQL**, **Redis**, and **Docker**, designed for low-latency evaluation and high reliability.

---

## Why Feature Flags?

Shipping code directly to 100% of users is risky. A new feature might introduce:

- Unexpected bugs or crashes
- Performance regressions
- Unintended side effects in edge cases

Traditional rollback requires reverting commits, redeploying the app, and often results in downtime or a degraded user experience.

Feature flags solve this by separating **code deployment** from **feature activation**:

```
if feature_enabled("ai_search", user_id):
    show_new_search()
else:
    show_legacy_search()
```

Used by **Netflix**, **Amazon**, **Google**, and virtually every modern software company at scale.

---

## Tech Stack

| Technology   | Role                                              |
|--------------|---------------------------------------------------|
| **FastAPI**  | High-performance Python REST API framework        |
| **PostgreSQL** | Persistent storage for feature flag configurations |
| **Redis**    | In-memory caching layer for fast flag evaluation  |
| **Docker**   | Containerized deployment for consistent environments |

---

## Project Structure

```
feature-flag-service/
│
├── app/
│   ├── core/
│   │   └── cache.py              # Redis client setup and cache utilities
│   │
│   ├── models/
│   │   └── feature_flag.py       # SQLAlchemy ORM model for feature_flags table
│   │
│   ├── routers/
│   │   └── feature_router.py     # FastAPI route definitions (CRUD + evaluation)
│   │
│   ├── schemas/
│   │   └── feature_schema.py     # Pydantic request/response schemas
│   │
│   ├── services/
│   │   └── feature_service.py    # Business logic: rollout evaluation, cache management
│   │
│   ├── config.py                 # Environment variable configuration
│   ├── database.py               # PostgreSQL connection and session management
│   └── main.py                   # FastAPI app entry point
│
├── venv/                         # Python virtual environment (not committed)
├── .gitignore
├── docker-compose.yml            # Multi-container orchestration (API + DB + Redis)
├── Dockerfile                    # API service container definition
├── README.md
└── requirements.txt              # Python dependencies
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Client Application                  │
│          (Web App / Mobile App / Service)            │
└────────────────────────┬────────────────────────────┘
                         │  HTTP Request
                         ▼
┌─────────────────────────────────────────────────────┐
│              Feature Flag API (FastAPI)              │
│                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │   Routers   │→ │   Services   │→ │   Models   │  │
│  │  (HTTP I/O) │  │ (Biz Logic)  │  │  (ORM)     │  │
│  └─────────────┘  └──────┬───────┘  └────────────┘  │
└─────────────────────────┬───────────────────────────┘
                          │
              ┌───────────┴────────────┐
              ▼                        ▼
┌─────────────────────┐   ┌───────────────────────────┐
│     Redis Cache      │   │    PostgreSQL Database     │
│                      │   │                            │
│  • Feature configs   │   │  • Persistent flag store   │
│  • TTL-based expiry  │   │  • Source of truth         │
│  • Cache-aside       │   │  • CRUD operations         │
└─────────────────────┘   └───────────────────────────┘
```

### Request Lifecycle

```
1. Client calls GET /feature/{feature_name}/{user_id}
        │
2. Router receives request → delegates to Service layer
        │
3. Service checks Redis cache
        │
   ┌────┴────┐
   │         │
Cache HIT  Cache MISS
   │         │
   │    4. Query PostgreSQL
   │         │
   │    5. Store result in Redis
   │         │
   └────┬────┘
        │
6. Run rollout evaluation: hash(user_id) % 100 < rollout_percentage
        │
7. Return { "feature": "...", "enabled": true/false }
```

---

## Database Design

Feature flags are stored in the `feature_flags` table in PostgreSQL.

### Schema

| Column               | Type      | Description                                          |
|----------------------|-----------|------------------------------------------------------|
| `id`                 | Integer   | Primary key, auto-incremented                        |
| `feature_name`       | String    | Unique identifier for the feature (e.g. `ai_search`) |
| `enabled`            | Boolean   | Master switch — if false, feature is off for everyone |
| `rollout_percentage` | Integer   | % of users (0–100) who receive the feature           |

### Example Records

| feature_name       | enabled | rollout_percentage |
|--------------------|---------|--------------------|
| `ai_search`        | true    | 20                 |
| `dark_mode`        | true    | 100                |
| `new_checkout`     | false   | 0                  |
| `recommendation_v2`| true    | 5                  |

---

## Rollout Logic

### Deterministic Hashing

The service uses **deterministic hashing** to assign users to rollout buckets. This guarantees that the same user always gets the same result — no flickering features.

```python
bucket = hash(user_id) % 100   # Produces a value between 0 and 99

is_enabled = bucket < rollout_percentage
```

### Example

```
Feature: ai_search
Rollout: 20%

User 123  →  bucket 14  →  14 < 20  →  ✅ ENABLED
User 456  →  bucket 73  →  73 < 20  →  ❌ DISABLED
User 789  →  bucket 2   →  2  < 20  →  ✅ ENABLED
```

### Bucket Distribution

With `rollout_percentage = 20`, users in buckets **0–19** receive the feature. The remaining 80% (buckets 20–99) do not.

```
Buckets:   0  1  2  ... 19 | 20  21  ... 99
           [   ENABLED    ] | [    DISABLED   ]
                 20%        |       80%
```

This approach ensures:
- **Consistency** — the same user always sees the same result
- **Fair distribution** — no clustering or bias
- **Zero statefulness** — no user records need to be stored

---

## Caching Strategy

Every feature evaluation hits the service at high frequency. Querying PostgreSQL on every request would introduce unnecessary latency.

### Cache-Aside Pattern

```
Request arrives
       │
       ▼
Check Redis for feature config
       │
  ┌────┴─────┐
  │          │
HIT        MISS
  │          │
  │    Query PostgreSQL
  │          │
  │    Write result to Redis (with TTL)
  │          │
  └────┬─────┘
       │
Return config → run rollout logic → respond
```

### Cache Invalidation

The cache is invalidated immediately on any write operation:

| Operation         | Cache Action              |
|-------------------|---------------------------|
| `POST /feature`   | Invalidate (new key set)  |
| `PUT /feature`    | Invalidate updated key    |
| `DELETE /feature` | Remove key from Redis     |

This ensures the API always reflects the latest configuration.

---

## API Reference

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

---

### `GET /features`
Returns all configured feature flags.

**Response**
```json
[
  {
    "id": 1,
    "feature_name": "ai_search",
    "enabled": true,
    "rollout_percentage": 20
  }
]
```

---

### `POST /feature`
Creates a new feature flag.

**Request Body**
```json
{
  "feature_name": "ai_search",
  "enabled": true,
  "rollout_percentage": 20
}
```

**Response** `201 Created`

---

### `PUT /feature`
Updates an existing feature flag (enable/disable, change rollout %).

**Request Body**
```json
{
  "feature_name": "ai_search",
  "enabled": false,
  "rollout_percentage": 0
}
```

**Response** `200 OK`

---

### `DELETE /feature`
Removes a feature flag permanently.

**Request Body**
```json
{
  "feature_name": "ai_search"
}
```

**Response** `200 OK`

---

### `GET /feature/{feature_name}/{user_id}`
Evaluates whether a feature is enabled for a specific user.

**Example**
```
GET /feature/ai_search/123
```

**Response**
```json
{
  "feature": "ai_search",
  "enabled": true
}
```

---

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose installed

### 1. Clone the repository

```bash
git clone <repository-url>
cd feature-flag-service
```

### 2. Start all services

```bash
docker compose up --build
```

This starts:
- The **FastAPI** application on port `8000`
- **PostgreSQL** database
- **Redis** cache

### 3. Access the API docs

Open your browser and navigate to:

```
http://localhost:8000/docs
```

FastAPI auto-generates interactive Swagger documentation where you can test all endpoints directly.

### 4. Create your first feature flag

```bash
curl -X POST http://localhost:8000/feature \
  -H "Content-Type: application/json" \
  -d '{"feature_name": "ai_search", "enabled": true, "rollout_percentage": 20}'
```

### 5. Evaluate for a user

```bash
curl http://localhost:8000/feature/ai_search/12345
```

---

## Example Walkthrough

Here's a complete end-to-end scenario:

**Scenario:** You're rolling out a new AI-powered search feature to 20% of users.

```bash
# 1. Create the feature flag
POST /feature
{ "feature_name": "ai_search", "enabled": true, "rollout_percentage": 20 }

# 2. Your app evaluates the flag for each user on login
GET /feature/ai_search/99201   →  { "enabled": true  }  ← gets new search
GET /feature/ai_search/40512   →  { "enabled": false }  ← gets old search

# 3. Bug detected! Instantly kill the feature for everyone
PUT /feature
{ "feature_name": "ai_search", "enabled": false, "rollout_percentage": 0 }

# 4. No redeployment needed. All users are back on the stable experience.
```

---

## Future Improvements

| Feature                      | Description                                                      |
|------------------------------|------------------------------------------------------------------|
| **User Targeting**           | Enable features for specific user IDs, cohorts, or segments      |
| **A/B Testing Support**      | Track variant assignment and expose experiment metadata          |
| **Feature Analytics**        | Log evaluation events for usage and adoption tracking            |
| **Admin Dashboard**          | Web UI for managing flags without touching the API directly      |
| **Client SDKs**              | Python / JS / Go SDKs for easier application integration         |
| **Audit Logging**            | Record all flag changes with timestamps and author info          |
| **Gradual Ramp**             | Automatically increase rollout % on a schedule                   |

---

## Key Concepts Demonstrated

- REST API design with **FastAPI**
- **Cache-aside** pattern with Redis
- **Deterministic hashing** for consistent user bucketing
- **Microservice architecture** with clear separation of concerns
- **Containerized deployment** with Docker Compose
- **Database-driven configuration** decoupled from application code