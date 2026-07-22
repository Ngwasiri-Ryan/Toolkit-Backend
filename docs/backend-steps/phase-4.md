# Phase 4: Celery Task Queue, AI, Storage & Billing Workflows

## 1. Overview
Phase 4 implements the asynchronous task execution architecture, AI models, cloud and local storage abstraction, real-time WebSocket job notifications, and the architectural process mapping for billing integration.

---

## 2. Process Architecture Diagrams

### 2.1 Asynchronous Processing & WebSocket Notification Sequence
```mermaid
sequenceDiagram
    autonumber
    actor User as Client / Web App
    participant API as FastAPI Router
    participant DB as SQLite / PostgreSQL
    participant Redis as Redis Broker / PubSub
    participant Worker as Celery Worker
    participant Storage as S3 / Local Storage

    User->>API: POST /api/v1/images/remove-background (Upload File)
    API->>Storage: Save Input File
    API->>DB: Create DBJob (Status = "pending")
    API->>Redis: Enqueue Celery Task (job_id)
    API-->>User: 200 OK {"job_id": "uuid", "status": "pending"}

    par WebSocket Subscription
        User->>API: WS /ws/jobs/{job_id}
        API->>Redis: Subscribe to "job:{job_id}" channel
    and Async Task Execution
        Worker->>Redis: Pull Task (job_id)
        Worker->>DB: Update DBJob (Status = "processing")
        Worker->>Storage: Fetch Input File
        Worker->>Worker: Run AI Model (rembg / reportlab / pypandoc)
        Worker->>Storage: Save Output File
        Worker->>DB: Update DBJob (Status = "completed", output_path)
        Worker->>Redis: Publish "completed" to "job:{job_id}"
    end

    Redis-->>API: PubSub Notification ("completed")
    API-->>User: WS JSON Message {"job_id": "uuid", "status": "completed"}
    User->>API: GET /api/v1/jobs/{job_id}/download
    API->>Storage: Fetch Output Bytes
    API-->>User: File Binary Stream
```

---

### 2.2 Billing & Subscription Process Mapping
```mermaid
flowchart TD
    A[User Request] --> B{User Auth & Plan Check}
    B -->|Pro Plan| C[Bypass Daily Quota Limits]
    B -->|Free Plan| D{Daily Conversions < 5?}
    
    D -->|Yes| E[Increment daily_conversions_used]
    D -->|No| F[Return 429 Too Many Requests]
    F --> G[Display Upgrade CTA / Ad Trigger]

    C --> H[Enqueue Heavy Job to Celery]
    E --> H

    G --> I[User Clicks Upgrade to Pro]
    I --> J[POST /api/v1/billing/checkout]
    J --> K[Stripe Checkout Session]
    K --> L[User Completes Payment]
    L --> M[Stripe Webhook Event: checkout.session.completed]
    M --> N[POST /api/v1/billing/webhook]
    N --> O[Update User Plan to 'pro' in DB]
    O --> P[User Enjoys Unlimited Conversions]
```

---

## 3. Core Technical Components

### 3.1 Background Worker (`app/tasks/worker.py`)
- **`task_remove_background(job_id)`**: Executes AI background removal (`rembg`) on images with automatic error catching.
- **`task_convert_document(job_id, target_format)`**: Converts Markdown and DOCX documents to PDF using `pypandoc` and cross-platform `reportlab`.

### 3.2 Unified Storage Service (`app/services/storage.py`)
- Supports local disk storage (`./local_storage/`) with seamless fallback if AWS S3 credentials are not set.

### 3.3 Job Polling & Real-time WebSockets (`app/routers/jobs.py` & `app/routers/websocket.py`)
- `GET /api/v1/jobs/{job_id}`: Poll job status, execution error (if any), and timestamp metadata.
- `GET /api/v1/jobs/{job_id}/download`: Secure file streaming with appropriate Content-Type headers.
- `/ws/jobs/{job_id}`: Low-latency Redis PubSub WebSocket stream with automatic SQLite/Postgres DB polling fallback when Redis is offline.

---

## 4. Verification & Tests (`app/tests/test_phase4.py`)
- `test_background_removal_flow`: End-to-end test for file upload, task execution, status update, and output download.
- `test_document_conversion_flow`: End-to-end document conversion flow.
- `test_job_websocket_flow`: Tests WebSocket real-time status push and fallback loop.
