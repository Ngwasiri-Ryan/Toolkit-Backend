# ToolKit Backend Setup Guide

This guide provides step-by-step instructions to configure, run, and verify the ToolKit backend platform.

---

## 1. Prerequisites
Ensure you have the following installed:
- **Python**: Version `3.12.x`
- **Docker**: Desktop version (for containerized execution)
- **Git**: For version control

---

## 2. Option A: Local Python Virtual Environment Setup

This is the fastest method for local development and testing.

### Step 2.1: Initialize Environment
Navigate to the `backend` directory, create a virtual environment, and activate it:
```bash
cd backend
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate
```

### Step 2.2: Install Dependencies
Install all required packages:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2.3: Configure Environment Variables
Copy `.env.example` to `.env` and fill in the values:
```bash
cp .env.example .env
```
*Note: If Stripe, Resend, or AWS variables are left blank, the application automatically activates local mock configurations.*

### Step 2.4: Database Migrations
Initialize the SQLite database schema by running the Alembic migration history:
```bash
alembic upgrade head
```

### Step 2.5: Start FastAPI Server
Start Uvicorn in development auto-reload mode:
```bash
uvicorn app.main:app --reload
```
The server will start on **`http://127.0.0.1:8000`**. You can access the interactive API docs at **`http://127.0.0.1:8000/api/v1/docs`**.

---

## 3. Option B: Docker Compose Setup (Full Stack)

This is the recommended method to run the complete environment including Redis brokers and the Celery background workers.

### Step 3.1: Build and Launch Services
In the `backend` directory, run:
```bash
docker compose up --build
```
This automatically downloads, configures, and spins up:
- **`toolkit_redis`**: Message broker on port `6379`.
- **`toolkit_api`**: FastAPI server on port `8000`.
- **`toolkit_worker`**: Celery background processing worker.

### Step 3.2: Clean Up and Restart
To stop the services and clean up database volumes or container networks:
```bash
docker compose down --remove-orphans
```

---

## 4. Run Automated Verification Tests
To run the full 19-test suite (auth, conversions, Stripe webhooks, rate limiting, and security rules):
```bash
pytest app/tests/ -v --tb=short
```
