# ToolKit — Backend Phase-by-Phase Implementation Plan

> **Document Type:** Backend Engineering Roadmap
> **Version:** 1.0
> **Scope:** Full-cycle backend development roadmap (from setup to production launch)
> **Audience:** Engineering team, backend developers, project manager

---

## Executive Roadmap Summary

This document details the **7 development phases** required to build and deploy the ToolKit backend platform. The architecture is built on **FastAPI**, **PostgreSQL**, **Redis**, and **Celery**, structured to support a high-performance, async-native, freemium API with built-in advertising controls, subscription billing, and local AI processing.

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: Environment & Scaffold [COMPLETED]                 │
└──────────────┬──────────────────────────────────────────────┘
               ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: Database, Auth & API Key Layer [COMPLETED]         │
└──────────────┬──────────────────────────────────────────────┘
               ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: Synchronous Processing Services [COMPLETED]        │
└──────────────┬──────────────────────────────────────────────┘
               ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: Celery Task Queue, AI & Storage [COMPLETED]        │
└──────────────┬──────────────────────────────────────────────┘
               ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 5: Stripe Billing & Quota Middleware [COMPLETED]      │
└──────────────┬──────────────────────────────────────────────┘
               ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 6: Email, WebSockets & Security Rules [COMPLETED]     │
└──────────────┬──────────────────────────────────────────────┘
               ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 7: Orchestration, Testing & Launch (Weeks 13-14)     │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Environment & Project Scaffolding

### Objective
Establish the repository layout, configuration pipelines, developer tooling guidelines, base web frameworks, and test runners.

### Key Milestones
- [x] Configure virtual python environment (`venv`, `poetry` or `pip`).
- [x] Build the project directory tree structure.
- [x] Set up linting, code formatting, and strict type checking rules.
- [x] Initialize FastAPI application shell with core middleware layers.
- [x] Implement local test suite baseline with `pytest` and `httpx`.

### 📁 Target Directory Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application initializer
│   ├── core/
│   │   ├── config.py           # Pydantic Settings env configuration
│   │   ├── security.py         # Hashing, signature checkers
│   │   └── exceptions.py       # Custom platform error types
│   ├── routers/
│   │   ├── documents.py        # /api/v1/convert/documents/*
│   │   ├── images.py           # /api/v1/convert/images/*
│   │   ├── utilities.py        # /api/v1/convert/utilities/*
│   │   ├── jobs.py             # /api/v1/jobs/*
│   │   └── billing.py          # /api/v1/billing/* and /webhooks/stripe
│   ├── services/
│   │   ├── storage.py          # S3/Supabase Storage integrations
│   │   ├── mail.py             # Resend transaction email client
│   │   └── jobs.py             # Database CRUD helpers for jobs
│   ├── tasks/
│   │   ├── __init__.py
│   │   └── worker.py           # Celery tasks (heavy converters)
│   ├── models/
│   │   └── database.py         # SQLAlchemy schemas
│   └── tests/
│       ├── conftest.py
│       └── test_endpoints.py
├── requirements.txt
└── Dockerfile
```

### Technical Detail Tasks

1. **Pydantic settings environment loader (`core/config.py`)**:
   Implement a `Settings` class using `pydantic-settings` to load and parse environment variables (e.g., `DATABASE_URL`, `REDIS_URL`, `STRIPE_SECRET_KEY`) with validation.
2. **FastAPI application base (`main.py`)**:
   Setup the FastAPI instance. Add middlewares for:
   - CORS (`CORSMiddleware`) for Next.js frontend calls.
   - Gzip response compression.
   - Global exception handling targeting customized exceptions.
3. **Base Testing framework (`tests/`)**:
   Create a root level `conftest.py` with mock clients and a simple test asserting route health (`GET /api/v1/health`).

---

## Phase 2: Database, Auth & API Key Layer

### Objective
Integrate the PostgreSQL database, setup tables, hook up user authentication verifying tokens against Supabase JWT signatures, and implement the API Key generation/authorization pipeline.

### Key Milestones
- [x] Connect SQLAlchemy or SQLModel engine to database.
- [x] Create initial migration scripts (via `Alembic`).
- [x] Write DB schemas (`users`, `jobs`, `api_keys`).
- [x] Implement Supabase JWT verification middleware.
- [x] Code API Key creation endpoints and security handlers.

### Detailed Database Schemas (SQLAlchemy)

```python
# models/database.py
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()

class DBUser(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    plan = Column(String, default="free")  # free, pro, team
    stripe_customer_id = Column(String, nullable=True)
    daily_conversions_used = Column(Integer, default=0)
    last_reset_at = Column(DateTime(timezone=True))

class DBJob(Base):
    __tablename__ = "jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    session_id = Column(String, nullable=True) # for guests
    tool = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed, expired
    input_path = Column(String, nullable=False)
    output_path = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))

class DBAPIKey(Base):
    __tablename__ = "api_keys"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    key_hash = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True))
    last_used_at = Column(DateTime(timezone=True), nullable=True)
```

### Technical Detail Tasks

1. **Supabase JWT Verifier**:
   Write a utility utilizing `python-jose` to fetch Supabase's JWKS and decode standard user JWTs stateless.
2. **API Key Generation & Hashing System**:
   Generate cryptographically random strings (`tk_live_` prefix + 32 alphanumeric characters). The plaintext is returned once to the frontend. Store a `sha256` hash in the database.
3. **Security dependency validation (`app/core/security.py`)**:
   Implement dynamic validation that accepts either a `Bearer` JWT token or a custom header `X-API-Key` (matching database keys by hashing the incoming key).

---

## Phase 3: Synchronous Processing Services

### Objective
Build the lightweight synchronous utility services that process fast operations (primarily <5 seconds) directly inside the API process.

### Key Milestones
- [x] Create safe temporary file management helper class.
- [x] Implement image utilities using Pillow (format converter, resizer, optimizer, cropper, grayscale).
- [x] Build file manipulation services (PDF merge/split via `pypdf`).
- [x] Implement developer converters (Base64, JSON formatter, CSV/JSON conversion, Timestamp/Datetime, color codes, diffing, hashing).
- [x] Code the styled QR Code generator service.

### Technical Detail Tasks

1. **Temp Context Manager (`app/services/temp.py`)**:
   Ensure files are strictly cleaned up immediately after streaming to prevent server disk overflow.
   ```python
   import tempfile
   import os
   from contextlib import contextmanager

   @contextmanager
   def temp_session(suffix: str = ""):
       fd, path = tempfile.mkstemp(suffix=suffix)
       os.close(fd)
       try:
           yield path
       finally:
           if os.path.exists(path):
               os.unlink(path)
   ```
2. **Standard Document/Image Sync Pipeline**:
   Expose routes under `/api/v1/convert/utilities` and `/api/v1/convert/images` accepting multipart uploads and query parameters.
3. **QR Code Generator Engine**:
   Construct customized color masks and modules with error correction (Level H) so user logos can safely overlay in future phases.

---

## Phase 4: Celery Task Queue, AI & Storage

### Objective
Configure the asynchronous execution architecture. Connect Celery workers to a Redis broker to handle heavy conversions (pypandoc, weasyprint) and AI background removal, saving results to external object storage.

### Key Milestones
- [x] Set up the Redis instance and Celery App connection.
- [x] Construct the background worker configuration and start scripts.
- [x] Build the AI background removal task (`rembg`).
- [x] Code Document conversion tasks using `pypandoc` (to PDF/DOCX) and `reportlab` (Markdown/HTML to PDF).
- [x] Create object storage managers (Local disk fallback & S3 storage integration).

### Celery/Redis Job Orchestration

```
 FastAPI API Route                 Redis Broker                     Celery Worker
┌──────────────────┐             ┌──────────────┐                 ┌───────────────┐
│ Upload File      ├────────────►│ Enqueue Job  ├────────────────►│ Pull Job Task │
│ Save state to DB │             └──────────────┘                 │ Run Converter │
│ Return 202 JobID │                                              │ Upload Output │
└────────┬─────────┘                                              └───────┬───────┘
         │                                                                │
         │                                                                │
         ▼                                                                ▼
 Polling Endpoint ◄─────────────────────────────────────────────── Update DB state
```

### Technical Detail Tasks

1. **Celery Worker Setup (`app/tasks/worker.py`)**:
   Implement standard celery task handlers matching the database `job_id`. Provide robust retry strategies on network failures (upload errors).
2. **AI Model Initialization**:
   Pre-load `rembg` session models (e.g. `u2net`) on Celery worker startup to prevent slow initial latency per request.
3. **File Storage Client Integration**:
   Integrate an AWS S3-compatible client to stream file bytes straight to object storage and fetch short-lived signed URLs for result retrieval.

---

## Phase 5: Stripe Billing & Quota Middleware

### Objective
Integrate the subscription engine. Sync user profiles against Stripe events, control quota allocations dynamically, and build the free-tier download countdown logic.

### Key Milestones
- [x] Set up Stripe webhook handler endpoints.
- [x] Build database sync script for subscription life-cycles (Checkout, Renewal, Deletion).
- [x] Write quota verification middlewares.
- [x] Code daily counter cron reset script.
- [x] Implement the server-side download countdown throttling logic.

### Quota Middleware Check Flow

```
   Incoming User Request
             │
             ▼
     Extract Identity
             │
      ┌──────┴──────┐
      ▼             ▼
   Pro/Team        Free
      │             │
      │             ▼
      │      Conversions today >= 10?
      │       ┌─────┴─────┐
      │       ▼ Yes       ▼ No
      │    Block 429      Increment Counter
      │    (Upgrade CTA)  Allow Processing
      ▼             │
Allow Unlimited     ▼
                  Finish
```

### Technical Detail Tasks

1. **Stripe Webhook Verification**:
   Parse and verify the incoming request signature. Handle events:
   - `checkout.session.completed` -> update user plan to `pro` or `team`.
   - `customer.subscription.deleted` -> downgrade user plan to `free`.
2. **Quota Counter Reset**:
   Implement a cron job running at `00:00 UTC` daily to reset `daily_conversions_used` back to 0.
3. **Free Tier Countdown Throttling**:
   Enforce wait times in the download routing layer. Return a custom error if a download is requested before the 5-second session cooldown window completes.

---

## Phase 6: Email, WebSockets & Security Rules

### Objective
Ensure immediate feedback to UI layers using WebSockets, automate file email delivery, and protect endpoints from malicious inputs or attacks.

### Key Milestones
- [x] Implement the WebSocket notification routing engine.
- [x] Setup Resend API email template compilation.
- [x] Design path traversal security verifiers.
- [x] Implement sanitization functions targeting SVG files.
- [x] Write backend-level file volume constraints and upload limits.

### Technical Detail Tasks

1. **WebSocket Status Broadcaster**:
   On Celery task completions, publish statuses to Redis Pub/Sub channels. The WebSocket router picks this up and pushes notifications directly to the connected frontend client.
2. **Automated Document Delivery**:
   Send email notifications with download links when async tasks finish if users enabled email delivery settings.
3. **Security Constraints**:
   - Check file name parameters against regex rules to prevent path injection (`../`).
   - Run SVG data uploads through a sanitizer (e.g. `bleach`) before passing to `cairosvg`.

---

## Phase 7: Orchestration, Testing & Launch

### Objective
Tie the services together using Docker Compose configurations, verify overall reliability with comprehensive end-to-end integration tests, and optimize performance.

### Key Milestones
- [ ] Write production-ready `Dockerfile` and `docker-compose.yml` specs.
- [ ] Develop database migrations baseline (`Alembic`).
- [ ] Write full integration tests simulating Guest, Free, and Pro workflows.
- [ ] Set up logging, Sentry error capturing, and Prometheus metric exporters.
- [ ] Deploy and verify backend endpoints.

### Technical Detail Tasks

1. **Integration Test Suite**:
   Create a comprehensive test runner script that triggers:
   - A mock multipart file upload -> async conversion -> task execution assertion -> DB verification -> file cleanup.
2. **Production Orchestration Design**:
   - Configure Nginx to proxy backend calls on port 80/443.
   - Establish Docker Healthchecks checking `/api/v1/health` to restart unhealthy backend containers automatically.
3. **Monitoring and Logging Setup**:
   Ensure `Sentry` wraps all FastAPI router exceptions, alerting dev teams of server issues instantly.

---

## 📈 Phase Resource Allocation & Estimates

| Phase | Est. Duration | Complexity | Primary System Impact |
|---|---|---|---|
| **Phase 1** | 1–2 Weeks | Low | Project scaffolding, testing base |
| **Phase 2** | 2 Weeks | Medium | Auth verification, Database schemas, API keys |
| **Phase 3** | 2 Weeks | Medium | Sync conversion processes (Pillow, PDF manipulation) |
| **Phase 4** | 2 Weeks | High | Async workers, Celery/Redis queue, Object Storage |
| **Phase 5** | 2 Weeks | High | Stripe Billing, Quota management, dynamic delays |
| **Phase 6** | 2 Weeks | Medium | Real-time WebSockets, Emails, Security hardening |
| **Phase 7** | 2 Weeks | Medium | Docker compose, final integration, production launch |

---

<p align="center"><em>ToolKit Backend Implementation Plan — v1.0 — July 2026</em></p>
