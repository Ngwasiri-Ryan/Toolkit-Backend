# Phase 5: Rate Limiting, Freemium Tier & Stripe Integration

## 1. Overview
Phase 5 implements platform monetization, freemium rate limiting, daily quota resets, ad trigger metrics, and Stripe subscription lifecycle management (checkout sessions and secure webhooks).

---

## 2. Process Architecture & Data Flow

### 2.1 Quota Enforcement & Daily Reset Lifecycle
```mermaid
flowchart TD
    A[Incoming Request to Tool Endpoint] --> B[Extract User Identity via auth.py]
    B --> C{Is User Plan 'pro'?}
    C -->|Yes| D[Allow Request / Bypass Quotas]
    C -->|No| E[Check last_reset_at Timestamp]
    
    E -->|> 24 Hours Ago| F[Reset daily_conversions_used = 0]
    E -->|<= 24 Hours Ago| G[Keep Current Counter]
    
    F --> H{daily_conversions_used >= 5?}
    G --> H
    
    H -->|Yes| I[Return 429 Too Many Requests]
    H -->|No| J[Increment daily_conversions_used]
    J --> K[Process Conversion & Return 200]
```

### 2.2 Stripe Checkout & Webhook Subscription Upgrade Flow
```mermaid
sequenceDiagram
    autonumber
    actor User as User / Web Client
    participant API as ToolKit Billing API
    participant DB as Database (DBUser)
    participant Stripe as Stripe API & Gateway

    User->>API: POST /api/v1/billing/checkout
    API->>Stripe: stripe.checkout.Session.create(price_id, customer_email)
    Stripe-->>API: Session URL (https://checkout.stripe.com/...)
    API-->>User: {"checkout_url": "https://checkout.stripe.com/..."}
    
    User->>Stripe: Complete Card Payment
    Stripe->>API: POST /api/v1/billing/webhook (Event: checkout.session.completed)
    API->>API: Verify Signature (stripe.Webhook.construct_event)
    API->>DB: Update DBUser (plan = "pro")
    
    User->>API: GET /api/v1/billing/usage
    API-->>User: {"plan": "pro", "daily_limit": "unlimited"}
```

---

## 3. Key Components to Implement

### 3.1 Rate Limiting Dependency (`app/core/middleware.py`)
- `check_daily_quota(user: DBUser, db: Session)`: Validates free tier usage against `FREE_DAILY_CONVERSION_LIMIT = 5` and handles automatic 24-hour reset timestamps.

### 3.2 Stripe Billing Router (`app/routers/billing.py`)
- `GET /api/v1/billing/usage`: Exposes user quota usage and plan details for frontend display and ad triggers.
- `POST /api/v1/billing/checkout`: Generates Stripe Checkout sessions for plan upgrades.
- `POST /api/v1/billing/webhook`: Handles `checkout.session.completed` and `customer.subscription.deleted` events.

### 3.3 Test Suite (`app/tests/test_phase5.py`)
- Automated tests verifying rate limit HTTP 429 responses, daily resets, usage statistics, and webhook plan transitions.
