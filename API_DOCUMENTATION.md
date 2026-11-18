# PeyajFlow — API Documentation

Complete catalog of every API endpoint, what it does, who can call it, and where it lives.

**Tech stack:** FastAPI (Python) backend at `services/api` + Next.js 16 frontend at `apps/web`
**Base URL (local):** `http://127.0.0.1:8000` — all business APIs prefixed `/v1`
**Auth:** `Authorization: Bearer <token>` (httpOnly cookie `peyajflow_session` on the web app)
**Roles:** `farmer` · `buyer` · `agent` · `admin`
**Auto docs:** `/docs` (Swagger) · `/redoc` · `/openapi.json`

---

## Table of Contents

1. [Health & Status](#1-health--status)
2. [Authentication & Identity](#2-authentication--identity)
3. [Stock / Lots](#3-stock--lots)
4. [Buyer Demand & Matching](#4-buyer-demand--matching)
5. [Trade: Offers & Orders](#5-trade-offers--orders)
6. [Inspection & Condition](#6-inspection--condition)
7. [Storage Risk](#7-storage-risk)
8. [Hold-or-Sell Advice](#8-hold-or-sell-advice)
9. [Market Data & Forecasts](#9-market-data--forecasts)
10. [Logistics (Transport)](#10-logistics-transport)
11. [Settlement / Payments](#11-settlement--payments)
12. [Notifications & SMS](#12-notifications--sms)
13. [Admin / Operations](#13-admin--operations)
14. [Voice (Bangla Call Simulator)](#14-voice-bangla-call-simulator)
15. [Twilio Webhooks (SMS & Voice)](#15-twilio-webhooks-sms--voice)
16. [Next.js Web Routes](#16-nextjs-web-routes)
17. [Next.js Server Actions](#17-nextjs-server-actions)
18. [Summary](#18-summary)

---

## 1. Health & Status

> **File:** `services/api/app/main.py` · **Auth:** None

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health/live` | Liveness probe — always `{"status":"ok"}` |
| GET | `/health/ready` | Readiness: checks DB connectivity + Alembic migration head. Returns `503` if DB is down or migrations are pending |

**Used for:** Docker/Render health checks (`render.yaml` `healthCheckPath`).

---

## 2. Authentication & Identity

> **Files:** `services/api/app/auth.py`, `services/api/app/credentials.py` · **Prefix:** `/v1`

| Method | Path | Purpose | Roles / Notes |
|--------|------|---------|---------------|
| GET | `/v1/auth/demo` | List available demo identities (name, role) for the demo picker | No auth · `404 demo_disabled` unless demo mode is on |
| POST | `/v1/auth/demo` | Demo login → issues a session token (201) | No auth · optional `access_key` · rate-limited 30/60s per IP |
| POST | `/v1/auth/password` | Username/password sign-in → session token (201) | Rate-limited (IP + account) · scrypt KDF · non-demo orgs only |
| DELETE | `/v1/auth/session` | Logout — revokes the current session token (204) | Auth required |
| GET | `/v1/me` | Get current user profile (role, org, district, language, verified, is_demo) | Auth required |
| PATCH | `/v1/me` | Update own profile (name, district, language) | Auth required |
| GET | `/v1/delegations` | List agent delegations granted by a farmer (paginated) | Roles: FARMER, AGENT |
| PUT | `/v1/delegations/{agent_id}` | Grant delegation to a **verified** agent (204) | Role: FARMER only |
| DELETE | `/v1/delegations/{agent_id}` | Revoke a delegation (204) | Role: FARMER only |

---

## 3. Stock / Lots

> **File:** `services/api/app/lots.py` · **Prefix:** `/v1/lots`

| Method | Path | Purpose | Roles / Notes |
|--------|------|---------|---------------|
| GET | `/v1/lots` | List lots scoped to the actor (page size 50) | Auth · query: `offset`, `unverified_only` |
| POST | `/v1/lots` | Register a new lot (label, district, variety, storage, dates, grade, quantity) | Auth · `request_key` for idempotency |
| POST | `/v1/lots/delegated/{farmer_id}` | Agent registers a lot **on behalf of a farmer** | Requires an active delegation |
| GET | `/v1/lots/{lot_id}` | Lot detail: stock, reservations, movements, verification status | Auth |
| PATCH | `/v1/lots/{lot_id}` | Edit lot fields | Role: FARMER · row-locked |
| POST | `/v1/lots/{lot_id}/movements` | Record a stock movement (sale / loss / purchase / etc.) · `LOSS_REPORTED` is forced negative | Auth · `request_key` idempotency |
| POST | `/v1/lots/{lot_id}/verification` | Agent/admin verifies lot quantity (`verified_kg` must lie within reserved..available) | Roles: AGENT, ADMIN |

---

## 4. Buyer Demand & Matching

> **File:** `services/api/app/demand.py` · **Prefix:** `/v1`

| Method | Path | Purpose | Roles / Notes |
|--------|------|---------|---------------|
| GET | `/v1/buyer-requests` | List buyer demand requests (paginated) | Role: BUYER |
| POST | `/v1/buyer-requests` | Create a buyer demand (variety, grade, district, delivery window, quantity, price ceiling) | Role: BUYER · 201 |
| GET | `/v1/buyer-requests/{request_id}` | Read a single demand | Role: BUYER |
| POST | `/v1/buyer-requests/{request_id}/close` | Close a demand (idempotent if already closed) | Role: BUYER |
| GET | `/v1/matches` | **Supply matching** — browse listed lots filtered by district, variety, grade, quantity, verification, price/freight assumptions; returns a ranked supply page | Auth · query: `district`, `variety`, `minimum_grade`, `minimum_kg`, `verified_only`, `request_id`, `ranked`, `preferred_district`, `price_assumption_bdt_kg`, `preferred_freight_bdt`, `offset` |

---

## 5. Trade: Offers & Orders

> **File:** `services/api/app/trade.py` · **Prefix:** `/v1`

| Method | Path | Purpose | Roles / Notes |
|--------|------|---------|---------------|
| GET | `/v1/offers` | List offers visible to the actor (paginated) | Demo-scoped |
| GET | `/v1/offers/{offer_id}` | Offer detail incl. activity/event history | `404` if out of scope |
| POST | `/v1/offers` | Create/send an offer (qty, price, delivery district, transport, validity, optional link to a buyer request) | Roles: FARMER, BUYER · `request_key` idempotency · checks lot availability |
| POST | `/v1/offers/{offer_id}/respond` | Respond: `accept` \| `reject` \| `counter` \| `withdraw` | Requires `version` (optimistic concurrency) + `confirm` for accept · `409 invalid_transition` / `offer_expired` · accept creates an order |
| GET | `/v1/orders` | List orders for the actor (paginated) | Auth |
| GET | `/v1/orders/{order_id}` | Order detail + action history | Auth |
| POST | `/v1/orders/{order_id}/transition` | Advance order state: `dispatch` (farmer), `receive` (buyer), `cancel`, `dispute` | `confirm` required · `409 invalid_transition` · auto-expires confirmed orders past `expires_at` · publishes notifications + lot events |

---

## 6. Inspection & Condition

> **File:** `services/api/app/inspection.py` · **Prefix:** `/v1/lots/{lot_id}`

| Method | Path | Purpose | Roles / Notes |
|--------|------|---------|---------------|
| GET | `/v1/lots/{lot_id}/inspections` | List inspections for a lot (with observation rows) | Auth + lot access |
| POST | `/v1/lots/{lot_id}/inspections` | **Multipart upload**: `observations` (JSON ≤4096), `images` (2–4 files), `consent` | Roles: FARMER, AGENT · 13 MB body limit · images resized/validated (Pillow) · stored local or S3 · 201 |
| GET | `/v1/lots/{lot_id}/inspection-photos/{photo_id}` | Serve a raw inspection photo as `image/jpeg` | `Cache-Control: private, no-store` · `404` if photo not in lot |
| POST | `/v1/lots/{lot_id}/inspections/{inspection_id}/review` | Condition review: set/clear `flags` with a `reason` (second-opinion review) | Auth + lot access |

---

## 7. Storage Risk

> **File:** `services/api/app/risk.py` · **Prefix:** `/v1/lots/{lot_id}`

| Method | Path | Purpose | Roles / Notes |
|--------|------|---------|---------------|
| GET | `/v1/lots/{lot_id}/risk` | Storage-risk view: combines latest inspection, spoilage/loss model, and price exposure | Auth · lot-scoped |

---

## 8. Hold-or-Sell Advice

> **File:** `services/api/app/advice.py` · **Prefix:** `/v1/lots/{lot_id}`

| Method | Path | Purpose | Roles / Notes |
|--------|------|---------|---------------|
| GET | `/v1/lots/{lot_id}/recommendation` | Recommendation with **default assumptions** → SELL / HOLD + rationale | Auth |
| POST | `/v1/lots/{lot_id}/recommendation` | Recommendation with user-supplied assumptions: `series`, `offer_id`, `horizon_days`, `loss_pct`, transport/fees/storage/finance costs, `use_loss_model`, hypothetical prices, `assumptions_reviewed` | Auth · `assumptions_reviewed` required for full output |

---

## 9. Market Data & Forecasts

> **Files:** `services/api/app/market_data.py`, `services/api/app/forecast.py` · **Prefix:** `/v1`

| Method | Path | Purpose | Roles / Notes |
|--------|------|---------|---------------|
| GET | `/v1/market/series` | List available price series (series key + district metadata) | Auth |
| GET | `/v1/market/prices` | Price observations · query: `series` (64-hex key), `limit` 1–100 (default 30) | Auth · only approved data |
| GET | `/v1/market/forecasts` | Quantile forecast with confidence bands + backtest metrics for `series`, `horizon` ∈ {7, 14, 28} | `422 invalid_input` for other horizons |
| GET | `/v1/admin/data-imports` | List CSV import batches (paginated) | Role: ADMIN |
| POST | `/v1/admin/data-imports` | Upload market CSV (`label`, `synthetic`, `csv`) → parse + validation issues, staged for review | Role: ADMIN · 201 · client caps CSV at 400 KB |
| GET | `/v1/admin/data-imports/{batch_id}` | Preview batch detail + parsed observations/issues | Role: ADMIN |
| POST | `/v1/admin/data-imports/{batch_id}/review` | Approve/reject a staged batch (idempotent on same decision) | Role: ADMIN · approval publishes prices |

---

## 10. Logistics (Transport)

> **File:** `services/api/app/logistics.py` · **Prefix:** `/v1`

| Method | Path | Purpose | Roles / Notes |
|--------|------|---------|---------------|
| GET | `/v1/orders/{order_id}/logistics` | Logistics view for an order: transport request, quotes (incl. expiry), booked status | Auth · participants only |
| POST | `/v1/logistics/quote-requests` | Request transport for a confirmed order (`pickup_on`, `handling`, `request_key`) | 201 · idempotent |
| POST | `/v1/logistics/quote-requests/{request_id}/quotes` | Record a provider quote (provider, source_ref, pickup date, capacity, freight/handling, validity) | **Role: ADMIN** · `409 idempotency_conflict` on duplicate provider+ref · `422 logistics_insufficient_capacity` · publishes notification · 201 |
| POST | `/v1/logistics/quote-requests/{request_id}/book` | Book a quote (`quote_id`) | Requires responsible party · `409 logistics_quote_expired` / `invalid_transition` · idempotent if already booked |
| POST | `/v1/logistics/quote-requests/{request_id}/cancel` | Cancel a request | Requires responsible party · idempotent if already cancelled |

---

## 11. Settlement / Payments

> **File:** `services/api/app/settlement.py` · **Prefix:** `/v1`

| Method | Path | Purpose | Roles / Notes |
|--------|------|---------|---------------|
| GET | `/v1/orders/{order_id}/settlement` | Payment/settlement history for an order | Auth (participants) |
| POST | `/v1/orders/{order_id}/settlement` | Buyer **reports a payment** (reference, `request_key`, `confirm`) → status `reported` | Role: BUYER · 201 · `confirm` required |
| GET | `/v1/admin/settlements` | Admin review queue: reported payments for delivered orders (50/page, `offset`) | Role: ADMIN |
| POST | `/v1/orders/{order_id}/settlement/{payment_id}/review` | Admin approves/rejects a reported payment (`decision`, `evidence_reference`) | Role: ADMIN · `409 payment_already_reviewed` / `payment_requires_delivery` · blocks reference matching its own evidence |

---

## 12. Notifications & SMS

> **File:** `services/api/app/notifications.py` · **Prefix:** `/v1`

| Method | Path | Purpose | Roles / Notes |
|--------|------|---------|---------------|
| GET | `/v1/notifications` | In-app inbox (unread counts, paginated, `offset` ≤ 10000) | Auth · scoped to membership |
| POST | `/v1/notifications/read-all` | Mark all notifications as read (204) | Auth |
| POST | `/v1/notifications/{alert_id}/read` | Mark one notification as read (204) | Auth |
| GET | `/v1/notifications/preferences` | Get SMS / quiet-hour preferences | Auth |
| PUT | `/v1/notifications/preferences` | Save preferences (`sms_enabled`, `quiet_start/end`, Asia/Dhaka quiet hours) | `422 sms_verified_phone_required` if SMS enabled without a verified phone or in demo |

---

## 13. Admin / Operations

> **File:** `services/api/app/admin.py` · **Prefix:** `/v1/admin`

| Method | Path | Purpose | Roles / Notes |
|--------|------|---------|---------------|
| GET | `/v1/admin/overview` | Ops dashboard counts (lots, orders, SMS deliveries, disputes, etc.) | Role: ADMIN · demo-scoped |
| GET | `/v1/admin/verifications` | List accounts pending verification (`pending_only`, `offset`) | Role: ADMIN |
| PUT | `/v1/admin/verifications/{membership_id}` | Approve/reject a member verification (`verified` bool) | Role: ADMIN · audited |
| GET | `/v1/admin/data-quality` | Data-quality metrics per series/dimension | Role: ADMIN |
| GET | `/v1/admin/audit` | Audit-log search: `action` (prefix), `resource_id`, `offset` ≤ 10000 | Role: ADMIN · demo-scoped |
| GET | `/v1/admin/disputes` | List disputed orders (50/page) | Role: ADMIN |
| POST | `/v1/admin/disputes/{order_id}/resolve` | Resolve a dispute (`note`, `confirmed`) | Role: ADMIN · row-locked · requires prior dispute action history |

---

## 14. Voice (Bangla Call Simulator)

> **File:** `services/api/app/voice.py` · **Prefix:** `/v1/voice`

| Method | Path | Purpose | Roles / Notes |
|--------|------|---------|---------------|
| POST | `/v1/voice/calls` | Start a simulated call session (201) | **Demo-only** · `404 demo_disabled` unless demo org + demo mode/showcase key |
| GET | `/v1/voice/calls/{call_id}` | Call transcript/history (entries, intents, confirmations) | Owner-only (`actor_id` match) |
| POST | `/v1/voice/calls/{call_id}/intent` | Submit a Bangla phrase + tool params → returns recognized intent + pending entry (+ `demo_code` for confirmation) | `409 voice_call_expired` if call not active · `422` on ambiguous/invalid input |
| POST | `/v1/voice/calls/{call_id}/confirm` | Confirm a pending action with the numeric `digits` code | Code hashed, single-use, expiring · executes real backend tools |
| DELETE | `/v1/voice/calls/{call_id}` | End the call (204) | Idempotent |
| GET | `/v1/voice/tasks` | List assistance/help tasks visible to the actor | Task scope by role |
| POST | `/v1/voice/tasks` | Request assistance (`kind`, `note`, `lot_id`) (201) | Roles: FARMER, BUYER, AGENT · audited |
| POST | `/v1/voice/tasks/{task_id}/resolve` | Resolve a help task | Roles: AGENT (own scope), ADMIN |

---

## 15. Twilio Webhooks (SMS & Voice)

> **Files:** `services/api/app/notifications.py`, `services/api/app/telephony.py` · **Prefix:** `/v1/webhooks`

All webhook endpoints verify **Twilio signatures** (no user auth) and have a **12 KB body limit**.

### SMS Delivery & Opt-Out

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/webhooks/messaging/twilio/status` | Twilio SMS delivery-status callback (204) |
| POST | `/v1/webhooks/messaging/twilio/opt-out` | Twilio Advanced Opt-Out (STOP) callback → disables further queued SMS |

### Carrier Voice (TwiML)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/webhooks/telephony/twilio` | Inbound call → returns TwiML `<Gather>` menu + greeting · validates `CallSid` (`CA`+32 hex) |
| POST | `/v1/webhooks/telephony/twilio/menu` | Keypad selection (1 = overview, 2 = help) → TwiML `<Say>` |
| POST | `/v1/webhooks/telephony/twilio/status` | Call status callback → upserts carrier call state (204) · `400 provider_callback_invalid` on bad status/Sid |

Setup docs: `docs/DEPLOYMENT.md`

---

## 16. Next.js Web Routes

> **Files:** `apps/web/app/(index)/route.ts`, `apps/web/app/[locale]/workspace/photos/[lot]/[photo]/route.ts`

| Method | Path | Purpose | Notes |
|--------|------|---------|-------|
| GET | `/` | Redirects root to `/bn` (307) | No auth |
| GET | `/{locale}/workspace/photos/{lot}/{photo}` | Server-side proxy that streams the inspection photo from `GET /v1/lots/{lot}/inspection-photos/{photo}` | Forwards Bearer token from `peyajflow_session` cookie · preserves `image/jpeg`, `private, no-store`, `nosniff` · maps errors to empty response with same status |

---

## 17. Next.js Server Actions

> **Files:** `apps/web/app/[locale]/workspace/actions.ts`, `operations-actions.ts`, `pilot-actions.ts`

These are `"use server"` actions invoked from forms. They proxy to the FastAPI backend and end in `redirect()`.

### `actions.ts` — Core workspace mutations

| Action | Backend calls |
|--------|---------------|
| `signIn` | `POST /v1/auth/demo` → sets httpOnly cookie |
| `passwordSignIn` | `POST /v1/auth/password` |
| `signOut` | `DELETE /v1/auth/session` → clears cookie |
| `mutate` (generic form dispatcher) | `PATCH /v1/me` · `POST /v1/lots` · `POST /v1/lots/delegated/{id}` · `PATCH /v1/lots/{id}` · `POST /v1/lots/{id}/movements` · `POST /v1/lots/{id}/verification` · `POST /v1/buyer-requests` · `POST /v1/buyer-requests/{id}/close` · `POST /v1/offers` · `POST /v1/offers/{id}/respond` · `POST /v1/orders/{id}/transition` · `POST /v1/lots/{id}/inspections` (multipart, 2–4 images ≤3 MB each, consent required) · `POST /v1/lots/{id}/inspections/{sub}/review` |

### `operations-actions.ts` — Operations panel mutations

| Action | Backend calls |
|--------|---------------|
| `operate` | `read-alert` → `POST /v1/notifications/{id}/read` · `read-all` → `POST /v1/notifications/read-all` · `preferences` → `PUT /v1/notifications/preferences` · `verify` → `PUT /v1/admin/verifications/{id}` · `resolve` → `POST /v1/admin/disputes/{id}/resolve` · `report-payment` → `POST /v1/orders/{id}/settlement` · `review-payment` → `POST /v1/orders/{id}/settlement/{payment_id}/review` · `grant/revoke-agent` → `PUT/DELETE /v1/delegations/{id}` · `request-help` → `POST /v1/voice/tasks` · `resolve-help` → `POST /v1/voice/tasks/{id}/resolve` |

Destructive ops require a `confirm` checkbox.

### `pilot-actions.ts` — Pilot / demo mutations

| Action | Backend calls |
|--------|---------------|
| `pilotMutate` | `import` → `POST /v1/admin/data-imports` (CSV ≤400 KB) · `review` → `POST /v1/admin/data-imports/{id}/review` · `transport` → `POST /v1/logistics/quote-requests` · `quote` → `POST /v1/logistics/quote-requests/{id}/quotes` · `book`/`cancel` → `POST .../{id}/book` \| `.../{id}/cancel` · `start-call` → `POST /v1/voice/calls` · `resolve-task` → `POST /v1/voice/tasks/{id}/resolve` |
| `runAdvice` | `POST /v1/lots/{lotId}/recommendation` with full assumption set · returns advice result without redirect |
| `runVoice` | Voice turn loop: `POST /v1/voice/calls/{id}/intent` · `POST .../confirm` · `DELETE /v1/voice/calls/{id}` · `GET /v1/voice/calls/{id}` · tracks one-time confirmation `demo_code` |

---

## 18. Summary

### Endpoint counts

| Layer | Count |
|-------|-------|
| FastAPI endpoints (source-defined) | **78** |
| Next.js route handlers | **2** |
| Next.js server actions (8 actions, ~25 distinct mutating ops) | **8** |
| Implicit FastAPI endpoints (`/docs`, `/redoc`, `/openapi.json`) | **3** |
| **Total HTTP endpoints** | **~83** |

### HTTP method distribution (backend)

| Method | Count |
|--------|-------|
| GET | 26 |
| POST | 40 |
| PUT | 4 |
| PATCH | 2 |
| DELETE | 4 |

### Source files

**Backend (`services/api/app/`):**
`main.py` · `auth.py` · `credentials.py` · `lots.py` · `demand.py` · `trade.py` · `inspection.py` · `risk.py` · `market_data.py` · `forecast.py` · `advice.py` · `logistics.py` · `settlement.py` · `voice.py` · `telephony.py` · `notifications.py` · `admin.py`

**Frontend (`apps/web/app/`):**
`(index)/route.ts` · `[locale]/workspace/photos/[lot]/[photo]/route.ts` · `[locale]/workspace/{actions,operations-actions,pilot-actions}.ts`

### Global behavior

- **Auth:** `Authorization: Bearer <43-char token>` resolved against hashed `sessions` table → `401 sign_in_required` / `401 session_expired`
- **Roles:** `require_role()` → `403 role_forbidden`
- **Rate limits:** 120 req/60s per member (production); sign-in stricter (100/5min per IP, 8/15min per account) → `429 rate_limited`
- **Body size limits:** `/v1/webhooks/*` 12 KB · `*/inspections` 13 MB · `/v1/auth/*` 16 KB · everything else 2 MB → `413`
- **Hardening:** `X-Request-ID`, `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`
- **Error normalization:** validation → `422 invalid_input` · DB errors → `503 database_unavailable` · uncaught → `500 service_unavailable`
- **Idempotency:** mutations accept `request_key` and journal/replay — duplicate requests return the original receipt
- **Demo scoping:** all queries filtered by `organizations.is_demo == actor.is_demo`
- **Background workers (not HTTP):** offer-expiry sweep (20s) · SMS delivery processor (15s) · rate-limit pruning (10min) — `main.py` lifespan
