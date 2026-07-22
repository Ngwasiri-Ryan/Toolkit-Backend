# Phase 2: Database, Auth & API Key Layer

## 1. Overview
Phase 2 builds the persistence and security infrastructure: SQLite/PostgreSQL models using SQLAlchemy, user registration routines, Supabase JWT verification, and cryptographically secure API key generation and header authentication.

---

## 2. Database Models (`app/models/database.py`)

### 2.1 Schema Definitions
- **`DBUser`**: User profile tracking `email`, `plan` (`free`/`pro`), `stripe_customer_id`, `daily_conversions_used`, and `last_reset_at`.
- **`DBJob`**: Asynchronous conversion job records tracking `user_id`, `session_id`, `tool`, `status` (`pending`, `processing`, `completed`, `failed`), `input_path`, `output_path`, `error`, `created_at`, and `expires_at`.
- **`DBAPIKey`**: Developer API key records storing key metadata and `key_hash` (`sha256`).

---

## 3. Authentication & API Key System

### 3.1 API Key Format
- Generated prefix: `tk_live_` followed by 32 cryptographically secure random alphanumeric characters.
- Stored as a `sha256` hash in the database.
- Transmitted via `X-API-Key` HTTP header.

### 3.2 Dual Authentication Dependency (`app/core/auth.py`)
- Accepts either Bearer JWT tokens or `X-API-Key` headers.
- Automatically resolves or auto-provisions user records in `DBUser`.

---

## 4. Verification & Tests (`app/tests/test_phase2.py`)
- `test_user_registration`: Verifies user registration and DB session management.
- `test_api_key_header_authorization`: Validates key generation, hashing, and `X-API-Key` authentication.
