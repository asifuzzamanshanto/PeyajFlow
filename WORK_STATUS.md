# PeyajFlow work status

Last updated November 12, 2026 (Asia/Dhaka).

## Work completed

- Reviewed the master handoff, the supplied 311 × 59 transparent logo, and the existing workspace. The workspace started with those two files and no Git history or remote.
- Initialized Git on `chore/repo-foundation`. Preserved the owner files and used the handoff's dependency order below.
- Implemented the F00 source files for a pnpm Next.js workspace, a FastAPI API, PostgreSQL and a baseline Alembic revision, local Compose, environment examples, and CI.
- Connected the localized workspace to API readiness. It reports online, unavailable, unconfigured, and migration-required conditions based on server responses. There is no seeded business data in this slice.
- Integrated the unmodified interim lockup and a mark-only favicon. See [asset provenance](docs/BRAND_ASSET_PROVENANCE.md) for source and crop details.
- Attempted to inspect the public demo. See [demo audit](docs/DEMO_AUDIT.md) for the access result.

## Verification and delivery

| Check | Status |
| --- | --- |
| Web dependencies, format, lint, typecheck, unit tests, and production build | Frozen install, format, lint, typecheck, 4 unit tests, and production build passed |
| API dependencies, lint, format, and health tests | Locked sync, Ruff lint and formatting, and 3 API tests passed |
| PostgreSQL migration and readiness | One Alembic head. Upgrade, baseline rollback, and re-upgrade passed on disposable PostgreSQL 18.6. Alembic reported no metadata drift. The running API returned HTTP 503 before migration and HTTP 200 afterward |
| Docker Compose stack | Configuration validated. Container build and PostgreSQL 16 smoke pending a running Docker engine |
| Responsive browser smoke | Production build passed Edge/Playwright checks at 360, 390, 768, 1280, and 1440 px. Verified Bangla default, same-origin redirect, language switching, keyboard skip, status refresh, loaded logo, and no horizontal overflow. The 360 px run also verified the migration-required state |
| Accessibility and visual review | Automated axe checks reported zero violations at 360 and 1440 px. Sampled text pairs measured at least 5.47:1. [Mobile](docs/design-reviews/foundation-360.png) and [desktop](docs/design-reviews/foundation-1440.png) screenshots |
| GitHub PR and CI run | Pending an authorized remote |
| Render and Vercel deployment | Pending later deployment work and authorized services |
| Pilot and field validation | Pending working product workflows and pilot participants |

## Implementation queue

| ID | Work | State |
| --- | --- | --- |
| F00 | Monorepo, local database and API, CI, responsive workspace shell | Implemented and verified with the native stack. Docker and GitHub CI runs pending |
| Brand | Owner-logo integration, responsive usage, contrast, and design evidence | Initial integration in F00. Standalone brand review, wider UI placements, and vector asset pending |
| F01 | Users, organizations, roles, safe demo sessions and authorization | Next |
| F02 | Farmer lots, quantity units, ownership and immutable stock ledger | Pending F01 |
| F03 | Buyer demand and search of eligible supply | Pending F02 |
| F04 | Buyer offers, farmer confirmation and atomic order reservation | Pending F03 |
| F05 | Inspection uploads and manual review | Pending F02 |
| F06 | Visible-condition assessment with abstention and evidence | Pending F05 |
| F07 | Storage-risk rules and missing-data handling | Pending F05 |
| F08 | Dated market observations, CSV import and data quality | Pending |
| F09 | Forecast baselines, temporal backtests and uncertainty | Pending F08 |
| F10 | Hold/sell scenario comparisons and insufficient-data state | Pending F07–F09 |
| F11 | Matching, landed cost and logistics quote workflow | Pending F04 |
| F12 | Bangla call simulator with confirmation through the same order API | Pending F04 |
| F13 | Live telephony adapter and verified carrier integration | Pending F12 and carrier access |
| F14 | In-app alerts and optional SMS adapter | Pending transaction events |
| F15 | Admin operations, provenance, audit and disputes | Pending core modules |
| F16 | Responsive design, accessibility and localization across product routes | Pending workflow screens |
| F17 | Production hardening, rollback, observability and deployment | Pending working workflows and provider access |

## Decisions and risks

- F00 uses a single Alembic baseline so readiness can detect an empty or stale schema from the start. The identity feature introduces the first business tables.
- The app uses server-side API requests. Browser CORS and cookie behavior will be reviewed when identity and authenticated mutations are introduced.
- Early screens use the supplied raster. The owner vector master and field review of Bangla wording remain pending.
- The first end-to-end milestone is one farmer lot, one buyer offer, one explicit acceptance, and one persisted stock reservation visible to both actors. Inspection, price models and voice build on those permissions and transaction rules.
- Update this file after each feature with what changed, checks that ran, remaining work, and confirmed PR or deployment evidence when available.

## Next implementation slice

Start F01 with persistent users, organizations, and memberships. Resolve actor and organization from server-managed sessions, implement explicitly labeled demo sign-in, and verify session expiry and cross-role denial before adding lot writes. Record the actor and authorization contract in the feature tests and OpenAPI schema.
