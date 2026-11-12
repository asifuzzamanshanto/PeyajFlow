# PeyajFlow work status

Last updated November 12, 2026 (Asia/Dhaka).

## Work completed

- Reviewed the master handoff, the supplied 311 × 59 transparent logo, and the existing workspace. The workspace started with those two files and no Git history or remote.
- Initialized Git on `chore/repo-foundation`. Preserved the owner files and used the handoff's dependency order below.
- Implemented the F00 source files for a pnpm Next.js workspace, a FastAPI API, PostgreSQL and a baseline Alembic revision, local Compose, environment examples, and CI.
- Connected the localized workspace to API readiness. It reports online, unavailable, unconfigured, and migration-required conditions based on server responses. There is no seeded business data in this slice.
- Integrated the unmodified interim lockup and a mark-only favicon. See [asset provenance](docs/BRAND_ASSET_PROVENANCE.md) for source and crop details.
- Audited the public demo at desktop and mobile sizes. See [demo audit](docs/DEMO_AUDIT.md).

### Pilot milestone F01–F07

| Feature | Delivered | Evidence |
| --- | --- | --- |
| F01 | Persisted users, organizations, role memberships, delegated agents, and expiring demo sessions | API tests cover role denial, revocation, expiry, and demo rejection in production |
| F02 | Lot registration and editing, stated kg-per-maund conversion, separate reported and verified quantities, and immutable movements | PostgreSQL tests cover access, duplicate requests, and competing losses |
| F03 | Buyer demand, eligible supply, verification labels, and filters and pagination | API tests cover private field projection, unlisted lots, grade filtering, verified stock, and pagination |
| F04 | Offers and counteroffers, versioned terms and history, acceptance, order receipts, dispatch, receipt confirmation, cancellation, dispute, and automatic expiry | PostgreSQL tests cover competing acceptances, exactly-once reservation, idempotent replay, expiry release, and cross-role order views |
| F05 | Structured inspections, consent, private uploads and gallery, sanitized image bytes, and review audit | Tests cover MIME and size rejection, EXIF removal, unauthorized image access, and persisted review records |
| F06 | Photo-quality checks with abstention, manual visible observations, owner corrections, and agent/operator review | Tests verify low-quality evidence and distinct submitted, corrected, and reviewed provenance |
| F07 | Evidence-based storage-risk checklist with reason codes, stale and missing-data handling, and inspection urgency | API and rule tests cover review-driven risk, missing measurements, freshness, and threshold boundaries |

### Market and call pilot F08–F12

| Feature | Delivered | Local evidence |
| --- | --- | --- |
| F08 | Role-scoped CSV staging, row-level validation and deduplication, review and approval, source records, unit conversion, and stale/synthetic labels | PostgreSQL tests cover invalid and duplicate rows, approval visibility, access, original units, and provenance |
| F09 | 7-, 14-, and 28-day forecasts with last-value, rolling-median and seasonal baselines, gated quantiles, and publication-aware backtests | Tests verify future-publication exclusion, sparse/stale abstention, baseline fallback and chronological evaluation |
| F10 | Same-quantity sell-now and hold scenarios with price provenance, loss, transport, fees, storage, finance, and cash needs | Tests cover downside and upside math, negative proceeds, hypothetical abstention, and partial sales at a verified offer |
| F11 | Ranked supply by coverage, user-entered landed costs, location, verification and grade. Persistent transport requests, recorded quotes and booking | PostgreSQL tests cover coverage ranking, landed costs, permission checks, capacity, replay and party visibility |
| F12 | Bangla typed-command simulator with optional device playback, read-back, expiring keypad confirmation, order receipts, and an agent request queue | PostgreSQL tests cover unknown intents, wrong lot, stated kg/maund quantity, wrong digits, expiry, disconnect, replay, agent access, and the shared reservation |

## Verification and delivery

| Check | Status |
| --- | --- |
| Local Git | Foundation committed as `bd2271e902f637efc973b03db9b1b7300540074f` on `chore/repo-foundation` |
| Pilot Git | F01–F07 committed as `a92fea9425e339c62a197a54732878fb271ce77f` on `feat/pilot-f01-f07` |
| Market and call Git | F08–F12 committed as `4a205abfc38b0a05051abadc5820bc489f894486` on `feat/market-voice-f08-f12` |
| Web dependencies, format, lint, typecheck, unit tests, and production build | Frozen install, format, lint, typecheck, 4 unit tests, and production build passed |
| API dependencies, lint, format, and health tests | Locked sync, Ruff lint and formatting, and 3 API tests passed |
| PostgreSQL migration and readiness | One Alembic head. Upgrade, baseline rollback, and re-upgrade passed on disposable PostgreSQL 18.6. Alembic reported no metadata drift. The running API returned HTTP 503 before migration and HTTP 200 afterward |
| Docker Compose stack | Configuration validated. Container build and PostgreSQL 16 smoke pending a running Docker engine |
| Responsive browser smoke | Production build passed Edge/Playwright checks at 360, 390, 768, 1280, and 1440 px. Verified Bangla default, same-origin redirect, language switching, keyboard skip, status refresh, loaded logo, and no horizontal overflow. The 360 px run also verified the migration-required state |
| Accessibility and visual review | Automated axe checks reported zero violations at 360 and 1440 px. Sampled text pairs measured at least 5.47:1. [Mobile](docs/design-reviews/foundation-360.png) and [desktop](docs/design-reviews/foundation-1440.png) screenshots |
| Pilot API and database | Ten API tests passed with PostgreSQL 18.6. Alembic upgrade, rollback to the foundation, re-upgrade, and metadata-drift checks passed through `0007_offer_terms`. Ruff lint and formatting passed |
| Pilot browser flow | Production Next.js build, lint, formatting, typecheck, and four web unit tests passed. Playwright verified the farmer, buyer, and agent workflow against the real API and PostgreSQL, with zero automated axe violations on the checked screens. [Desktop order receipt](docs/design-reviews/pilot-order-desktop.png) and [Bangla mobile risk](docs/design-reviews/pilot-risk-mobile.png) |
| F08–F12 verification | Sixteen API tests, four web unit tests, and both Playwright workflows passed. The production build and migrations through `0010_voice` passed. Rollback to `0007_offer_terms`, re-upgrade, and Alembic metadata check passed on disposable PostgreSQL 18.6. Checked browser screens reported zero automated axe violations. [Price outlook](docs/design-reviews/pilot-price-outlook.png), [mobile call receipt](docs/design-reviews/pilot-voice-mobile.png), and [transport booking](docs/design-reviews/pilot-transport-quotes.png) |
| GitHub PR and CI run | Pending an authorized remote |
| Render and Vercel deployment | Pending later deployment work and authorized services |
| Pilot and field validation | Pending working product workflows and pilot participants |

## Implementation queue

| ID | Work | State |
| --- | --- | --- |
| F00 | Monorepo, local database and API, CI, responsive workspace shell | Implemented and verified with the native stack. Docker and GitHub CI runs pending |
| Brand | Owner-logo integration, responsive usage, contrast, and design evidence | Initial integration in F00. Standalone brand review, wider UI placements, and vector asset pending |
| F01 | Users, organizations, roles, safe demo sessions and authorization | Implemented in the local pilot |
| F02 | Farmer lots, quantity units, ownership and immutable stock ledger | Implemented in the local pilot |
| F03 | Buyer demand and search of eligible supply | Implemented in the local pilot |
| F04 | Buyer offers, farmer confirmation and atomic order reservation | Implemented in the local pilot |
| F05 | Inspection uploads and manual review | Implemented in the local pilot |
| F06 | Visible-condition assessment with abstention and evidence | Implemented with manual observations and image-quality rules |
| F07 | Storage-risk rules and missing-data handling | Implemented with a rule-based checklist |
| F08 | Dated market observations, CSV import and data quality | Implemented and verified locally |
| F09 | Forecast baselines, temporal backtests and uncertainty | Implemented and verified locally. Real-series validation pending |
| F10 | Hold/sell scenario comparisons and insufficient-data state | Implemented and verified locally |
| F11 | Matching, landed cost and logistics quote workflow | Implemented and verified locally with recorded quotes |
| F12 | Bangla call simulator with confirmation through the same order transaction | Implemented and verified locally in simulation |
| F13 | Live telephony adapter and verified carrier integration | Next, subject to carrier access |
| F14 | In-app alerts and optional SMS adapter | Pending transaction events |
| F15 | Admin operations, provenance, audit and disputes | Pending core modules |
| F16 | Responsive design, accessibility and localization across product routes | Pending workflow screens |
| F17 | Production hardening, rollback, observability and deployment | Pending working workflows and provider access |

## Decisions and risks

- F00 uses a single Alembic baseline so readiness can detect an empty or stale schema from the start. The identity feature introduces the first business tables.
- Next.js forwards authenticated requests server-side. The browser uses an HTTP-only cookie and same-origin actions. The pilot uses fictional identities in development/test, with production OTP enrollment pending provider integration.
- Offers do not reserve stock until the recipient confirms. Confirmed stock is reserved for up to 48 hours. The operator can view the same order history as the parties. Payment verification is outside this pilot milestone.
- Private photo storage retains metadata-stripped JPEG evidence. The local adapter is verified. The S3-compatible adapter requires verification with a configured private bucket.
- Image checks assess photo quality. Visible condition comes from human observations and reviews. Storage-risk rules are advisory thresholds, with field calibration and a trained classifier left for later evidence.
- Early screens use the supplied raster. The owner vector master and field review of Bangla wording remain pending.
- Market forecasts use approved observations and original publication dates. The supplied sample is fictional and isolated by series. Forecast metrics are retrospective and real-series field validation is pending.
- Matching uses explicit buyer assumptions and operators record quotes received from transporters. Booking is recorded in PeyajFlow. Carrier-side confirmation and tracking remain external.
- The simulator uses typed commands and optional browser-provided Bangla playback. Web and simulated confirmations share the same transaction, and the simulator requires a demo session.
- Update this file after each feature with what changed, checks that ran, remaining work, and confirmed PR or deployment evidence when available.

## Next implementation slice

F13 adds the carrier adapter and verifies provider-authenticated callbacks. It requires an approved provider and carrier access. The local F12 simulator remains the repeatable acceptance path.
