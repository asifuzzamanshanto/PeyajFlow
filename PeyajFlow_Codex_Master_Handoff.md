# PeyajFlow — Complete Codex Master Handoff (Updated with Owner Logo, 2026-11-12)

Read as source files when possible. Brand identity in `design/BRAND_IDENTITY.md` overrides earlier palette descriptions.


---

## FILE: `README.md`

# PeyajFlow — Codex build handoff

A complete engineering planning pack for a Bangladesh-first onion supply-chain system. **This is a specification/handoff, not the implemented app or a completed deployment.** Start by opening `CODEX_MASTER_PROMPT.md` and then `AGENTS.md`.

## Files
- `CODEX_MASTER_PROMPT.md` — primary Codex invocation and autonomous iteration contract.
- `AGENTS.md` — repository-level agent rules, feature Git loop, safety, evidence and acceptance.
- `docs/ARCHITECTURE_V1.md` — prior finalized detailed technical system architecture and API contracts.
- `product/PRD.md` — personas, scope, journeys, business states and nonfunctional requirements.
- `product/FEATURE_BACKLOG.md` — features as branches/PRs with acceptance checks.
- `design/DESIGN_SYSTEM.md` — visual direction, page UX, accessibility, responsiveness and design review.
- `design/BRAND_IDENTITY.md` — **binding owner-supplied PeyajFlow logo and onion-purple brand system**, placements and implementation checklist.
- `design/assets/` — source screenshot, exact-crop and extracted interim transparent raster logo assets.
- `ops/DEPLOYMENT.md` — Render API/database/worker + Vercel web, env, rollout, smoke and rollback.
- `ops/GIT_WORKFLOW.md` — branch/commit/PR/CI discipline.
- `ops/QUALITY_GATES.md` — tests and evidence required before deployment.
- `.github/workflows/ci.example.yml` — starter CI blueprint (must be adapted to actual monorepo).
- `templates/render.example.yaml` — indicative Render Blueprint, not a guaranteed one-click deploy.
- `templates/env.example` — sample names, never actual secrets.

## Quick start for Codex
1. Open/mount this directory in Codex or copy the files into the new/existing PeyajFlow Git repo.
2. Paste `CODEX_MASTER_PROMPT.md` as the task, or instruct Codex to read and follow it. Codex must read all attached files.
3. Give authorized GitHub, Render and Vercel connections/credentials through their secure integrations/environment settings—not chat or source files.
4. Codex audits repo and demo, implements small tested vertical features and pushes one feature branch/PR at a time.
5. Render/Vercel production URLs are reported only after verified provider deployment and smoke tests.

## Owner logo integration (November 2026 update)
The user-provided purple onion icon and PeyajFlow serif wordmark are now the branding authority. The forest-green starter palette is deprecated. Codex must first inspect `design/BRAND_IDENTITY.md`, integrate an interim extracted logo, implement and verify a brand-only feature PR, and use onion-purple/skin colors across all UI routes. The original supplied screenshot includes unrelated event text and must never be displayed directly in product navigation. Request the owner vector file for crisp production/favicons if possible.

## Current verification boundaries
No PeyajFlow-named repo was found in the currently accessible GitHub repository list in the handoff session. The provided demo site's content was not successfully inspected from this environment. Therefore this pack does not claim to have modified source code, created PRs or deployed the product. Provider and price availability must be checked during implementation.


---

## FILE: `CODEX_MASTER_PROMPT.md`

# Paste this prompt into Codex with this handoff directory attached to the repository

You are the lead product engineer, system architect, research-aware ML engineer, design lead, QA engineer and DevOps engineer implementing PeyajFlow. Your task is to produce a genuinely usable, exceptionally polished, Bangladesh-first onion supply-chain platform, not a marketing landing page or a collection of mockup screens.

**Read the complete repository instructions in `AGENTS.md`, **`design/BRAND_IDENTITY.md`** and every document in this handoff before working.** Work iteratively and autonomously within tool permissions. Do not ask repetitive questions that can be solved by source inspection and reasonable engineering decisions. When an external credential/permission/payment/telephony contract is genuinely missing, use a safe adapter or explicit demo mode, document the blocker, and keep implementing locally.

## First response/action
1. Inspect `pwd`, `git status`, remotes, branch, existing files, package manifests, code, deployment configuration, tests and available environment **without exposing secret values**.
2. Attempt to view `https://peyajflow.boraq.io/` using available browser tooling, across desktop/mobile, and record an audit with actual findings or explicitly state not accessible. Treat the site as an exploratory demo only.
3. Survey the currently installed skills/tooling. Prefer an available vetted frontend-design/UI-UX skill or project-approved skill; if no such skill is installed, do not claim to have it. Read actual skills before relying on them. Use documented standards from `design/DESIGN_SYSTEM.md`; evaluate credible component and icon libraries without adding random dependencies.
4. Prepare a concise implementation plan based on the existing repo, with milestone dependencies, decisions and risks. Avoid arbitrary redesigns. Start the first vertical slice immediately.

## Product mission
PeyajFlow should allow Bangladesh onion farmers, village agents/aggregators, traders and institutional buyers to manage physical stock lots, monitor visible/storage conditions, understand uncertain price trends and tradeoffs, find feasible counterparties, execute auditable deals and track delivery. Admin verifies operations. An optional Bangla telephone assistant enables the same authorized actions via an alternative channel; it never replaces the web application. No promises of eliminated middlemen or guaranteed lower prices. Prioritize Pabna-to-Dhaka pilot reality, intermittent connectivity, low-end devices, Bengali typography and human support pathways.

## Locked architecture
- Monorepo: `apps/web` (Next.js App Router + TypeScript + Tailwind + accessible component primitives), `services/api` (Python FastAPI/Pydantic/SQLAlchemy/Alembic), `services/worker` (Celery where necessary), `packages` (types/API clients), `ml` (baselines/evaluation), `infra`, `docs`.
- PostgreSQL source of truth, S3-compatible blob storage for photos; Redis optional until needed for Celery and rate limiting. Render for API, worker and PostgreSQL; Vercel for the web. Same-origin frontend `/api` proxy strategy or approved CORS allowlist; no secrets in `NEXT_PUBLIC_*`. Docker Compose local stack, seed script, health/readiness endpoints and Alembic migrations.
- OpenAPI is the API contract. Generate frontend typed clients where practical. All mutations require authenticated user/org/role checks and idempotent order/confirmation processing.
- AI methods are evidence-based, versioned, tested against baselines, and safely degradable. Never fabricate live data, precision or accuracy. See architecture and PRD.
- Voice is a telephony adapter + audio STT/TTS + constrained orchestrator + validated domain actions. Real PSTN requires verified provider integration; otherwise clearly labeled simulator reusing identical tools and back-end state.

## Feature delivery order
Follow `product/FEATURE_BACKLOG.md`. First stabilize auth + stock -> buyer offer -> atomic reserved order. Then inspections and evidence/AI -> hold/sell -> voice -> logistics -> observability/polish. The initial presentation-grade demo must be backed by persistent state, not disconnected mock objects.

## Git and CI
Create a dedicated feature branch, commit, push and PR for **every feature**; require checks, track SHA and PR in `docs/FEATURE_STATUS.md`. Feature is complete only when acceptance criteria and all impacted tests pass. Use GitHub Actions. Never bypass branch protection or push secrets. If credentials unavailable, commit locally and record blocker; do not falsely mark pushed. Prefer `gh` CLI when actually authenticated; use direct Git when allowed. Ask for review only when required by configured protections.

## Binding logo and brand identity — updated by project owner
The project owner supplied the PeyajFlow logo: purple onion symbol + dark serif PeyajFlow wordmark. The exact screenshot-derived files are included in `design/assets/`. Read `design/BRAND_IDENTITY.md` before creating UI or design tokens. This supersedes any forest-green/earth-led branding elsewhere. The primary identity is onion purple `#6C319B` and dark wordmark ink `#201E1D`; use deep plum, mauve, warm neutral onion-skin white and restrained amber supporting colors. Preserve logo proportions; use the screenshot-extracted transparent raster only as an interim asset and request a vector source when possible. Prepare a faithful mark-only mobile/favicon treatment. The earlier mobile reference is a visual inspiration only, not a source of live prices or guaranteed returns. Add brand integration as its own committed, tested Git feature (`feat/brand-identity`) with before/after screenshots and PR evidence.

## Design bar
Build a serious, polished B2B/agritech product, not generic AI dashboard aesthetics: confident information hierarchy, refined type scale, user-supplied purple onion logo and sophisticated red-onion/skin palette, editorial data presentation, breathable whitespace, cohesive tokens, Bangla-first readability and one-thumb mobile usability. Use sophisticated responsive layouts and authentic imagery with licenses, not random gradients, glassmorphism, AI robot illustrations or excessive decorative cards. Define and review skeleton, empty, loading, success, error, offline and permission-denied states. Implement working keyboard focus and WCAG-aligned accessibility. Use Playwright screenshots and visual regression on real feature routes. Critique and iterate at least twice per primary screen.

## Final verification and delivery
- Show git history, remote/PR links and CI results; include actual deploy URLs if deployment succeeded, otherwise exact blocker(s).
- Run `pnpm lint`, `pnpm typecheck`, frontend tests, backend `ruff`/`pytest`, migration check, Playwright E2E and production builds; report real outputs.
- Smoke test the real deployed URLs: health, login/OTP or demo auth, stock CRUD, visual inspection, buyer offer and order, voice action simulator, failures, RBAC, file uploads, mobile layout, CORS and websocket/callback paths if used.
- Provide README, architecture decision records, a setup script/Makefile, `render.yaml`, Vercel project settings guidance, `.env.example`, seed fixtures, data provenance log, runbook, demo script, observability and troubleshooting.
- Distinguish verified, simulated, unfinished, pending partner approval. Do not call the platform complete if its core transaction workflow fails.


---

## FILE: `AGENTS.md`

# Codex operating contract — PeyajFlow

This file is binding for coding agents working in the PeyajFlow repository. Read `CODEX_MASTER_PROMPT.md`, `docs/ARCHITECTURE_V1.md`, `product/PRD.md`, `design/DESIGN_SYSTEM.md`, `design/BRAND_IDENTITY.md`, `ops/DEPLOYMENT.md`, and `ops/QUALITY_GATES.md` before implementing. These specifications form a contract; if inconsistent, document the conflict in an ADR and prefer safety, truthful data labeling and working end-to-end transactions over superficial feature completion.

## Mandatory working rules
1. Inspect the current git working tree, README, project layout, environment and recent commits before writing. **Never overwrite or delete work you did not create.** Keep all existing work intact; if repository state is ambiguous, make a new branch and preserve changes.
2. If a repository already exists, use it. Never assume that `peyajflow.boraq.io` hosts source code or that its design is the future product. Inspect its public surface if reachable, record `docs/DEMO_AUDIT.md` with screenshots, route observations, shortcomings and uncertain items; otherwise record inability to access and continue with the specified design system.
3. Implement vertically complete **one feature at a time**, not all UI first. Each feature includes schema/migrations, backend validation, UI states, access control, tests, fixture/demo data, documentation and, when required, voice tool support.
4. Each feature gets its own `feat/<slug>` branch from latest green main, preferably one PR. Make small conventional commits (`feat:`, `test:`, `fix:`, `docs:`, `chore:`), push the feature branch to `origin`, create/update PR, watch checks, fix failures, and merge only after green checks and review requirements. Do not push failing code to main. If PR creation/merge/remote push credentials are unavailable, do the local commit, capture the exact blocker, and continue local work; never report a push/deployment not confirmed by command output.
5. Before committing: format, lint, typecheck, backend unit tests, affected integration tests, and required migration checks. Before PR merge: full CI, E2E happy path and RBAC/authorization checks. If missing tests, create them.
6. Make functional UI: no faux buttons, dead-end forms, hardcoded empty pages, misleading charts, fake live data or pretend phone calls. All data must be explicitly real/verified, manual, estimated, synthetic demo or stale.
7. Backend is the security boundary. Never let a language model execute SQL or invoke unsafe mutations directly. Use a permissioned tool allowlist, validation, confirmation and audit records. Voice and web use the same APIs and transaction rules.
8. Do not promise exact crop life, preventable spoilage or guaranteed profits. One photo flags visible problems only. Price quotes distinguish farmgate, wholesale and retail; show freshness, locality and grade.
9. Never store actual NID scans, raw PINs or personal phone numbers in git. Use environment-managed secrets, hashed tokens and redacted logs. Demo data must use fictional identities and prominent demo labels.
10. Do not make new infrastructure or paid provider commitments without user authorization. Deploy using Render + Vercel **only after** verifying GitHub integrations, service access, credential scope, provider availability and budget. If inaccessible, prepare reproducible manifests and precise unblock instructions.
11. Keep `docs/IMPLEMENTATION_LOG.md`, `docs/FEATURE_STATUS.md`, `docs/DECISIONS.md`, and `docs/DEPLOYMENT_STATUS.md` up to date after every feature. Each status row: feature, branch, commit SHA, PR URL, tests, preview URL, evidence, actual state, blocker.
12. Never claim live telephony, bank settlement, trained Bangladesh-specific AI, validated accuracy, national stock estimates or real marketplace liquidity without evidence. Enable honest demo modes using feature flags.

## Git loop after every feature
```
git status --short
git switch main && git pull --ff-only origin main
git switch -c feat/<specific-slug>
# implement one complete vertical slice; keep migration and tests in same feature
pnpm lint && pnpm typecheck && pnpm test
# also: pytest and relevant integration/e2e tests, see QUALITY_GATES.md
git add <reviewed-files>
git commit -m "feat: <specific outcome>"
git push -u origin feat/<specific-slug>
# create PR via gh pr create if authorized; inspect CI; fix until green
# merge according to branch protection; sync main; start next feature
```
Never run destructive `git reset --hard`, `git clean -fd`, force-push or branch deletion on unreviewed work. If main protections prevent automatic merge, request review; do not bypass them. If no remote, create local branches/commits and provide exact commands to connect one.

## End-to-end definition of done
At least one Pabna farmer can register a lot, upload an inspection, see condition and data-labeled advice, receive a buyer's offer, confirm a partial sale, create exactly one inventory reservation/order, and see state updated on both buyer and farmer views. Bangla voice must use this same backend and require read-back/DTMF confirmation; if telecom access is missing, demonstrate clearly labeled call simulator and state the limitation. Full unit, integration, E2E and authorization tests pass; production env and deployment runbook are documented; there are no critical accessibility blockers.

## Owner-supplied branding override (2026-11-12)
Use the original PeyajFlow logo stored under `design/assets/` and the color tokens in `design/BRAND_IDENTITY.md`. Onion purple `#6C319B` and dark ink `#201E1D` supersede the early green-first proposal. Do not recreate a generic onion logo or present the source screenshot's event-header text as part of the mark. Implement a separate `feat/brand-identity` PR with visual checks. Maintain accurate Bangla data labeling and accessible contrast.


---

## FILE: `design/BRAND_IDENTITY.md`

# PeyajFlow — Official user-provided logo and onion-inspired visual identity

## Authority and provenance
The user explicitly supplied the PeyajFlow logo in November 2026. Its distinguishing properties are a **purple onion-line symbol** paired with a dark **PeyajFlow** serif wordmark. This asset overrides the earlier proposed forest-green brand palette. **Do not redesign, replace, recolor, warp, retype, or invent alternate onion symbols** without a direct owner request. The mark is a supplied raster screenshot; it is not proof of a vector master or font license.

### Provided files
- `assets/peyajflow-logo-reference-original.png`: original screenshot, **reference only**, with unrelated event/header material above the logo; never ship as-is in the UI.
- `assets/peyajflow-wordmark-original-crop.png`: clean rectangular crop of the supplied icon + wordmark, but retains original screenshot background (`#F3F2F2`). Fallback for reference review only.
- `assets/peyajflow-logo-transparent-raster.png`: best-effort background-removed reconstruction **derived from the exact supplied screenshot**, with original symbol/wordmark geometry; use in app while awaiting the original vector artwork; inspect quality at actual size.
- `assets/peyajflow-logo-transparent-3x.png`: enlarged raster convenience export. **Scaling does not create vector sharpness**. Prefer a verified owner-supplied SVG when available.

## Brand color tokens — onion-centric, sophisticated, restrained
Use the supplied logo's sampled icon purple `#6C319B` as brand anchor and wordmark ink `#201E1D`. Complementary tokens are proposed for UI, **not** claims of source colors:

| Token | Hex | Use |
|---|---|---|
| `brand.primary` | `#6C319B` | Identity, highlighted nav, interactive elements with checked contrast |
| `brand.deep` | `#4A1E62` | High-contrast primary CTA, key hero panel |
| `brand.ink` | `#201E1D` | Body/wordmark-aligned typography |
| `brand.plum` | `#361D3E` | Headlines, deep surfaces |
| `brand.mauve` | `#9B75AA` | Secondary accents; only when contrast permits |
| `surface.canvas` | `#FAF7F7` | Light onion-skin canvas |
| `surface.paper` | `#FFFFFF` | Card and table surfaces |
| `surface.lavender` | `#F4EAF8` | Soft supporting surface |
| `surface.rose` | `#F7EAF0` | Subtle red-onion skin tint |
| `border.default` | `#E5DCE7` | Quiet card/form dividers |
| `accent.harvest` | `#DE9F36` | Restrained harvest/amber action highlight |
| `semantic.success` | `#277747` | Success and gain; never imply forecast certainty |
| `semantic.warning` | `#9A5A08` | Caution with icon/text |
| `semantic.danger` | `#B83D4D` | Confirmed adverse conditions and validation errors |

Use purple for brand actions, NOT as a universal semantic meaning. Loss/danger uses labeled red; positive gain uses labeled green; forecast uncertainty is shown by range/band, not a confident green line by default. At minimum verify WCAG 2.2 AA color contrast with actual font sizes and backgrounds. Check whether primary purple on white and white on deep plum meet required contrast; adjust component tokens without changing the logo artwork.

## Logo placements and clear space
1. Desktop: full logo lockup in public header and authenticated navigation sidebar where width is sufficient; preserve proportions and intrinsic ratio.
2. Mobile: use the full logo only when it remains legible; otherwise use the **cropped original onion symbol** only after creating a true asset from the provided symbol. Do not squash wordmark to fit narrow app bars. Textual `PeyajFlow` can accompany symbol if needed.
3. Login/onboarding: full lockup with clear whitespace; no huge hero-sized repetition.
4. Favicon/app icon: mark-only version based on supplied onion symbol; prepare PNG sizes and browser icons with safe padding. Source icon is small: validate at 16, 32, 180 and 512 px. Request vector source for final production assets rather than claiming a perfect enlargement.
5. Footer, emails and PDFs: use an accessible mark and wordmark sized consistently. Prefer dark text on light canvas; do not invert the entire raster on dark backgrounds. If reverse logo needed, request/derive an approved variant while retaining mark geometry.
6. Clear space: at least 0.5× symbol width around the lockup as a starting implementation rule. Do not overlay watermarks, chips, AI sparkles or labels on the mark.
7. Add meaningful alt text `PeyajFlow` to the combined lockup. Decorative icon near visible text should have empty alt. Avoid duplicating logo text in accessibility names.

## Product UI reference
The previously supplied mobile mockup establishes a **visual direction**: onion-purple price hero, pale skin backgrounds, warm amber attention/action cards, clean Bangla-first typography, high information density managed with careful spacing, and role-specific bottom navigation. **It is not evidence of live data.** Its projected prices, 'high' confidence, loss amounts and claimed income improvements must not be copied as factual recommendations. Draw clear distinctions among observed historical prices, modeled projections and hypothetical scenario values.

## Codex implementation checklist
- [ ] Inspect these supplied assets; record source and transformations in `docs/BRAND_ASSET_PROVENANCE.md`.
- [ ] Replace previous forest/leaf palette in code and generated design tokens with this onion palette.
- [ ] Build reusable `<BrandLogo variant="full|symbol" />` with proper sizes and alt treatment.
- [ ] Ship brand previews/screenshots in `docs/design-reviews/`; include contrast checks.
- [ ] Test identity at desktop 1440px, mobile 360px, and low-resolution contexts.
- [ ] Verify no green-first branding remains in navigation, login, empty states or buttons.
- [ ] Source official vector file from project owner when available; keep screenshot-based raster as interim fallback, not an SVG master.
- [ ] Include one independent Git feature branch for brand integration and visual system changes with screenshots, tests, PR and commit hash.


---

## FILE: `design/DESIGN_SYSTEM.md`

# PeyajFlow — product design direction and UI acceptance system

## Design objective
A reliable, sophisticated product that an onion farmer can use under time pressure and a professional wholesale procurement officer can trust. The design should feel like a mature commerce/operations platform with agricultural context; not an 'AI tool' skin, generic SaaS template, government portal imitation, NFT dashboard, overly dark fintech UI or student-hackathon splash screen.

## Demo reference audit
`https://peyajflow.boraq.io/` is an **exploratory demo, not the design source of truth**. The preparatory session could not inspect its page content reliably. Codex must independently verify availability, screenshot it on desktop/mobile where possible, identify its information architecture and strengths/weaknesses in `docs/DEMO_AUDIT.md`. Never assert a screenshot was captured if not. Preserve useful domain ideas, not visual copying. Never deploy to `boraq.io` unless DNS/domain access is authorized.

## Visual identity: red-onion purple, warm onion skin, grounded editorial
**Binding brand contract:** See `design/BRAND_IDENTITY.md` and its supplied `design/assets/` logo files. The user has provided the PeyajFlow onion-symbol + dark serif wordmark. Preserve its geometry and sampled anchor colors. This supersedes the previously suggested forest-green palette.
- Feeling: trustworthy Bangladeshi agricultural commerce grounded in the onion crop, professional operational software and editorial clarity; subtle sophistication rather than ornament.
- Brand colors: supplied onion icon `#6C319B` and wordmark ink `#201E1D`. Proposed UI: deep purple `#4A1E62`, plum `#361D3E`, mauve `#9B75AA`, warm onion-skin canvas `#FAF7F7`, lavender `#F4EAF8`, muted rose `#F7EAF0`, amber `#DE9F36`, sage/green reserved for *positive data state* `#277747` (not default brand). All tokens must be WCAG contrast tested.
- Brand application: use supplied logo on public/auth headers and login; provide a faithful mark-only mobile/favicon asset, preserve clear space and aspect ratio. Never ship screenshot including unrelated event text. Until owner provides a vector master, treat extracted transparent raster as an interim asset.
- Typography: English **Inter** or **Manrope** (licensed self-hosted or hosted via framework), Bangla **Hind Siliguri** / **Noto Sans Bengali**; use fonts with verified licensing, working Bengali glyph coverage, and font-display swap. Use tabular numbers for inventory/price tables. 4/8 px spacing foundation; 12/16/20/24/32+ spacing scales.
- Headings: concise, high contrast, typographic rather than decorative. Restrained caps/letter spacing only in English eyebrow labels. Numbers authoritative, labels visible, unit never ambiguous.
- Icons: consistent Lucide-style stroke icons; meaningful use only. Photographs: authentic Bangladesh crop/warehouse/market context with explicit license/attribution. If no permission, use purposeful product illustrations/diagrams or photographs generated specifically for the project with accurate disclosure.
- Charts: honest axes, district/date/units, confidence ranges, historical vs forecast visually distinguished, source and update time, no chartjunk, explainability tooltips. No charts for fictional data without large DEMO badge.
- UI surfaces: natural paper/shell background, deeply considered white/linen surfaces, delicate 1 px border, subtle elevation only for floating overlays. Gentle red-onion purple gradients are allowed on one primary data/CTA surface when contrast is checked; never overdecorate every card. No glassmorphism, unrelated purple-to-blue gradient, dozens of identical KPI cards, excessive rounded pills, fake live-map dots or giant AI robot art.

## Layout system
- Public site: high-quality editorial home explaining 'what stock exists / when to sell / who can buy'; first-fold clear CTA, dashboard glimpses with factual demo labels, trust/evidence section, role-specific flows. Avoid fabricated testimonials/metrics, fake partner logos.
- App desktop: collapsible left sidebar with icon + short label; slim top bar with district, crop context, language, notifications and profile; content max width ~1440, charts + actionable tables; master-detail interactions rather than tab proliferation.
- App mobile: bottom nav (max 4 primary destinations plus More), meaningful top bar, 48px touch targets, readable form labels, sticky primary actions only when safe, cards for stock data where tables fail; optimistic updates only with recoverable server state.
- Farmer Overview: primary stock and pending action, price observations and freshness, spoilage attention, offers, one next step. Do not overload with 12 summary tiles.
- My Stock: lot cards/table list with verified/estimated status, available/reserved/sold quantities, storage health and quick inspect; detail timeline and evidence gallery.
- Condition Inspection: guided camera capture, framing hints, storage questions, progress and review before submission; show uncertainty and specialist escalation. Never call detection medical/definitive.
- Market & Advice: elegantly presented actual price curves and forecast bands, scenario calculator showing quantities and costs, direct 'hold / sell part / sell' consequences; always display method and source.
- Buyers: structured discovery/search and side-by-side delivered cost; offer creation and negotiation timeline; clear grade/verification badges.
- Order: detail timeline, receipts, quantity reserves, document states, disputes and delivery progress; never fabricate payment state.
- Voice demo: conversation transcript with speaker roles, tool-call audit, simulated-vs-real indicator, current lot, pending confirmation, keypad controls and escalation. Accessible, never fake an actual carrier call.
- Admin: operational data-quality and exception handling, no unnecessary surveillance.

## UX standards
1. One meaningful primary action per screen. Forms show why fields matter; quantity, Tk/kg vs Tk/maund, dates, grade, costs and location must be unambiguous.
2. All interaction states: skeleton/loading, success, no-data, no-permission, offline/degraded, validation error, server error, old-data notice, concurrent conflict, insufficient AI evidence.
3. Sensitive transitions (accept offer, sell quantity, release reservation, mark paid) need full terms, explicit confirmation and unambiguous receipts. Undo where safe; never double-submit.
4. User research proxy: validate Bangla terminology with 2–3 real target users if possible. Don't pretend generic English translations are field-tested. Support English for investors/operations, Bangla for farmers. Dates use Asia/Dhaka and clear year; amounts BDT.
5. WCAG 2.2 AA-oriented: accessible focus, keyboard navigation, ARIA semantics only where needed, alt text, noncolor status cues, readable text at 200% zoom, reduced motion, form errors and announcements. Target >=44px primary touch control size when possible.
6. Responsive screenshots: 360x800, 390x844, 768x1024, 1280x800, 1440x900. Playwright check no horizontal overflow, clipping or blocked modal. Test real tables and long Bangla terms.
7. Performance: avoid heavyweight image/animation libraries, paginate big lists, lazy-load charts, optimize photos and fonts; loading should never block the entire dashboard.

## Design review process — must document evidence
- Phase A: produce route inventory, wireframes/low-fi critical screens and component inventory before polishing.
- Phase B: implement design tokens and one fully functional page (farmer stock overview) before repeating patterns; get screenshot at each target viewport.
- Phase C: first critique: density, alignment, trust cues, chart semantics, hierarchy, typography, Bangla line breaks and accessible affordances. Make corrections.
- Phase D: second critique: connect UI to real backend scenarios, test all states, reduce repeated ornament, check empty/error cases, keyboard and low bandwidth.
- Phase E: screenshot diff and QA report. Track design debt as issues; no unverified 'pixel perfect' claims.

## Skills and resources for Codex
The current handoff environment did not reveal a dedicated installed UI/UX skill. Codex should **discover actual installed skills** (`skills` directory, system skills, configured MCP tools) and use verified design-related skill instructions if present. If permitted by environment and licensing, evaluate authoritative guidance from [Vercel Web Interface Guidelines](https://vercel.com/design/guidelines), [shadcn/ui](https://ui.shadcn.com/), [Radix UI](https://www.radix-ui.com/), [WAI WCAG 2.2](https://www.w3.org/TR/WCAG22/), [Nielsen Norman Group](https://www.nngroup.com/) and the Next.js accessibility documentation. These are references, not proof of a plugin installation. Do not execute unreviewed third-party skill scripts or copy designs indiscriminately.


---

## FILE: `product/PRD.md`

# Product requirements and user flows

## Product north star
A farmer should know: (1) what stock they really possess, (2) what is visibly wrong/at risk, (3) what local prices and uncertain forecasts mean, (4) how much selling versus waiting might net after loss and costs, and (5) which verified buyer can actually transact. The product must turn recommendations into an audited physical-order process. Buyers need provenance, grades and reliable fulfillment. Local agents and traders are participants, not presumed adversaries.

## Primary personas and roles
1. Farmer: owns stock lots, keeps location and harvest/store data, uploads photos, reviews offers, accepts or rejects with confirmation, views orders/payments.
2. Local agent/aggregator (Saathi): with explicit permission registers/verifies lots, adds weigh-in/inspection, assists farmer, records loading; never unilaterally transfers title.
3. Trader/wholesaler/buyer: searches eligible lots, posts requirements, sends offers, places orders, records receipt and dispute.
4. Logistics partner: quotes transport, accepts assignment, tracks shipment; no stock modification permissions.
5. Admin/operator: approves verification, reviews data provenance, resolves disputes, monitors audit logs and provider health. Read logs are redacted.
6. Voice-channel farmer: same farmer identity and authorization; no secondary account or duplicate business logic.

## Primary navigation
Public: Home, How it works, Market insight preview, For farmers, For buyers, Trust & data, Sign in.
Authenticated farmer: Overview, My stock, Inspections, Market prices, Sell advice, Offers & orders, Alerts, Help.
Buyer/trader: Overview, Demand, Browse supply, Offers, Orders, Logistics, Settings.
Agent: Farmer assignments, Stock verification, Inspections, Assistance queue.
Admin: Operations, Market data quality, Lots, Trades, Call sessions, Audit, Model health.

## Detailed end-to-end flow
- Register farmer with Bangla or English name, upazila/district, contact via verified sign-in or explicit demo identity. Record consent and role; protect PII.
- Register lot with estimated quantity in kilograms, harvest date, onion variety, storage place/type, owner, evidence and verification state. Record separate *claimed* and *verified* quantities.
- Upload 2–4 relevant stock photos (whole lot, close-up, suspected damaged bulbs), with consent. Validate type/size, strip EXIF GPS, scan images where feasible, retain original evidence, return visible flags with uncertainty and 'not diagnostic' caveat. Human verification status.
- Enter time-in-storage, humidity/temp if available, ventilation and observed losses. Rule-based storage alert; do not convert a single image into precise perish date.
- Show dated market prices with geography, market type, source, unit and freshness. Model training/evaluation page only if actual dataset adequate. Fallback to seasonality/naive baseline and clearly state.
- Decision page computes realized net sale today versus future scenario distributions after estimated shrinkage, storage, finance, logistics and transaction costs. User inputs editable, default values provenance-labeled. Suggest hold/sell/sell-part only if justified; otherwise 'insufficient evidence'.
- Buyer creates requirement specifying amount, delivery window, location, grade tolerance, expected price and transport terms. Match by verified eligible quantity, delivered cost estimate, distance and quality, with explainability.
- Offer received by farmer; review final terms, confirm via UI or call. Atomic stock reservation, order creation, idempotency key, audit event, notification to both parties. Handle partial lot fulfillment, cancellation, expiration, dispatch and receipt/dispute.
- Payment: display 'pending', 'reported' or 'verified' only according to actual confirmation; do not show unintegrated escrow or instant mobile-money payouts as done.
- Voice: identify caller through permitted auth/verified challenge, handle read-only info, propose mutation, read back quantity/price/party, collect DTMF/PIN or OTP, perform same API operation, create audit trail, permit human takeover.

## Non-functional baseline
- Bengali and English locale; Bengali numbers and units where useful, stable kg system-of-record, correct BDT formatting and local datetime.
- Mobile first, supports low bandwidth and degraded/offline read states; no offline order commitment without server confirmation.
- Test at 360, 390, 768, 1280 and 1440 px; accessibility visible focus, labels and error context; best effort WCAG 2.2 AA.
- Meaningful performance budget: target LCP <2.5s on good midrange connections, CLS <0.1; audit real connection conditions rather than fabricate scores.
- Server-side validation and permission checks for every mutation. PII encrypted where appropriate, audio retention and consent configured.

## Scope and evidence rules
- Not a national onion stock census, licensed lender, insured warehouse receipt system, licensed escrow operator or guaranteed price provider.
- No guarantee of 'AI accuracy' without independent holdout testing, seasonal backtests and confidence interval coverage results.
- No consumer-facing 'reduce waste by X%' claims without measured controlled pilot outcomes.
- Integrations (DAM, weather, SMS, BTRC/carrier, lender, mobile wallet) are adapters with manual/demo fallback until credentials and terms exist.


---

## FILE: `product/FEATURE_BACKLOG.md`

# Ordered vertical-slice backlog — branches, acceptance criteria and tests

Each numbered item is ONE feature branch and PR; keep changes reviewable. Commit more frequently within each branch. Feature handoff must include screenshot (where visual), API contract, migration, seed/fixture, tests and status log. Dependencies must be met before merge.

| ID | Proposed branch | Definition of done / acceptance | Tests |
|---|---|---|---|
| F00 | `chore/repo-foundation` | Monorepo, local Docker, env examples, formatter, CI, health endpoint, docs and basic responsive app shell; no secrets | install/build, smoke, health |
| F01 | `feat/auth-roles` | User/organization membership, farmer/buyer/agent/admin roles, safe demo auth and boundaries | cross-role 403, auth expiry |
| F02 | `feat/stock-lot-ledger` | Create/read/edit with immutable quantity events; claimed vs verified, unit conversion, farmer stock list/detail | negative balance, ownership, concurrent adjustments |
| F03 | `feat/buyer-demands` | Buyer requirements and supply search using real persisted lots, filters, verification labels | access, filters, pagination |
| F04 | `feat/offers-orders` | Offer negotiation, expiration, order creation, atomic reserved quantity; admin/farmer/buyer state parity | concurrency 2x accept, idempotency replay, order FSM |
| F05 | `feat/stock-inspections` | Photo storage, metadata/EXIF stripping, structured inspection and operator review | upload size/type, authorization, audit |
| F06 | `feat/visual-condition` | Classifier/inspection flags or honest rule-based fallback with confidence/provenance and human override | representative fixtures, abstention, robustness |
| F07 | `feat/storage-risk` | Safe rule-based risk with days stored, conditions, measurements; risk explanation, no invented shelf-life | missing sensors, threshold tests |
| F08 | `feat/market-data` | Market observations with source/time/type/unit; CSV ingestion, approval, stale badges and data-quality console | dedup, bad rows, provenance |
| F09 | `feat/price-forecast` | Seasonal/naive baseline + quantile model only when history supports; backtest display, uncertainty | leakage checks, time split, baseline compare |
| F10 | `feat/hold-sell-advice` | Scenarios with transparent costs, losses, confidence, sell-now comparator; abstain where weak | deterministic examples, negative scenarios |
| F11 | `feat/matching-logistics` | Matching rank with grade, location, quantity, delivery cost; quote/transport request workflow | valid rank, no false route prices |
| F12 | `feat/voice-orchestrator` | Bangla tool calls through same backend + per-actor permission and DTMF confirm; usable call simulator | intents, wrong lot, timeout, confirmation, replay |
| F13 | `feat/telephony-adapter` | Real provider callback if access confirmed, otherwise clearly documented stub; webhook signature/replay checks | provider mock, retries, event handling |
| F14 | `feat/notifications` | In-app alerts and provider-gated SMS, unread/read state, idempotent sends | repeat event, opt-out |
| F15 | `feat/admin-operations` | Verifications, source freshness, model health, disputes, audit search and role restrictions | admin RBAC, logs privacy |
| F16 | `feat/design-polish` | All primary workflows mobile/desktop, design consistency, empty/error/loading/permission states, i18n and accessibility review | Playwright screenshots, axe checks |
| F17 | `chore/deployment-hardening` | Render/Vercel integration, migrations, E2E smoke, backups, rate limiting, rollback and docs | production build + deployment health |

Critical demo cut: F00–F05, F07–F10, F12, F15–F17; include F06 if image recognition actually works, otherwise truthful manual-assessment pathway. F11 logistics can begin as quote requests. F13 actual PSTN cannot be guaranteed without carrier access. Do not skip F04 order integrity to spend time on animations.

## Owner logo addendum — required pre-UX feature
Before UI polish, deliver `feat/brand-identity` as a standalone branch/PR: integrate supplied onion logo assets, palette tokens and logo placements per `design/BRAND_IDENTITY.md`; test dark/light backgrounds, mobile header, app icon clarity, Bangla typography and WCAG contrast. Do not include live price claims from the reference mockup. Store exact commit SHA, test/screenshot links and PR in `docs/FEATURE_STATUS.md`. This is a design identity feature, not a change to the end-to-end transaction business logic.


---

## FILE: `docs/ARCHITECTURE_V1.md`

# PeyajFlow — Final System Architecture v1.0

**Date:** 2026-11-12  
**Purpose:** Team implementation contract for an end-to-end, demonstrable hackathon product, with production migration boundaries.  
**Geographic starting point:** Onion-growing areas in Bangladesh, initially Pabna and connecting wholesale buyers in Dhaka.  
**Architecture status:** Design decision, not a claim of implemented, validated, or commercially deployed technology.

## 1. Product definition and non-negotiable decisions

PeyajFlow is a shared platform for onion farmers, local aggregators/traders, verified buyers, transport partners and support agents. It tracks real stock lots, estimates visible condition and storage risk, summarizes price trends and uncertainty, supports hold/sell decisions, matches supply with demand, coordinates logistics, and records order outcomes. A Bangla phone-call assistant is a **second interface**, not a second database or a replacement for the web/PWA. Both interfaces call the same permissioned domain APIs.

Non-negotiable implementation rules:
1. One authoritative stock ledger, with immutable adjustments; never trust client-computed balances.
2. Every AI recommendation includes data freshness, limitations, and a human-readable reason.
3. A single photo can flag visible defects, but cannot establish internal onion condition or exact remaining shelf life.
4. A market price observation is not automatically a farmer's realizable farmgate price; retain source, locality, grade and wholesale/retail/farmgate class.
5. Phone recognition is fallible; high-impact changes require read-back and PIN/DTMF confirmation or OTP, with human escalation.
6. A deal is not paid/settled until the transaction status is independently confirmed. No unlicensed escrow claims.
7. Upazila/national supply estimates cannot be inferred directly from voluntary platform users without correcting sample bias.
8. Each piece of external data is labeled real, manually verified, synthetic, or stale. Synthetic demo values may never masquerade as live observations.

## 2. Deployment architecture

```mermaid
flowchart TB
  subgraph Channels
    F[Farmer PWA]
    T[Trader/Buyer PWA]
    A[Agent/Admin PWA]
    P[Telephone]
  end
  P --> G[Voice provider adapter: call control / IVR / DTMF / media if supported]
  G --> V[Voice orchestrator + guarded tool registry]
  F --> API[FastAPI application]
  T --> API
  A --> API
  V --> API
  subgraph Core[FastAPI modular monolith]
    API --> AUTH[Identity / roles / permissions]
    API --> INV[Stock lots / inspections / movement ledger]
    API --> ORD[Buyer requests / offers / orders / settlements]
    API --> DEC[Advice / risks / forecasts / matching]
    API --> NOT[Notifications / transport / admin]
  end
  Core --> PG[(PostgreSQL + optional PostGIS)]
  Core --> REDIS[(Redis)]
  Core --> OBJ[(S3-compatible media store)]
  Core --> TASK[Celery workers]
  TASK --> ML[Forecast / vision / risk scoring]
  TASK --> ETL[Data ingest: DAM, BAMIS, partner observations]
  TASK --> PG
  TASK --> OBJ
```

**Chosen stack:** Next.js + React + TypeScript + Tailwind PWA; Python 3.12+ FastAPI + SQLAlchemy + Alembic + Pydantic; PostgreSQL; Redis/Celery; S3-compatible photos; pandas, scikit-learn/LightGBM and PyTorch where justified; Docker Compose for local dev and staging. Authentication: OTP/PIN via a verified vendor or clearly disclosed demo-mode OTP. HTTPS everywhere. Optional PostGIS for location queries, but no requirement to add TimescaleDB, Kafka, Kubernetes, a vector database, or multiple microservices at hackathon scale.

One `/apps/web` application with role-based screens is preferable to separate farmer/trader/admin deployments. One `/services/api` deploy with feature modules is the source of truth. Heavy vision inference may later be split into its own worker service without changing the public contract.

## 3. Actors and permissions

| Actor | Main capabilities | Restrictions |
|---|---|---|
| Farmer | Register lots, report storage, inspect, see prices, get advice, list/accept offers, track orders | Only own lots; must authorize irreversible actions |
| Village agent | Assist onboarding, collect photos/weights, verify delegated lots, support calls | Delegation is scoped and audited; cannot silently sell others' stock |
| Aggregator / middleman | Register own stock and sourcing needs, negotiate, provide collection services | Cannot claim to own third-party lots without authority |
| Buyer | Publish purchase requests, review matched lots, make offers, initiate orders | Sees only permitted farmer data; cannot reserve beyond available stock |
| Transport partner | Quote, accept trips, update pickup/delivery | No access to unrelated private farm/price details |
| Admin | Review verification, moderate disputes, manage data sources and provenance, inspect audit trail | Powerful actions require logging, permission checks, and operational separation |

No need to eliminate intermediaries: a transparent aggregation and logistics role is more plausible for Bangladesh's onion value chain.

## 4. Feature modules and acceptance contracts

### A. Identity and onboarding — P0
- Phone-based registration, name, district/upazila/village, preferred language and actor role.
- Farmer/agent relationships; agent delegation and audit trail.
- Verified vs self-reported profile distinction. Avoid storing NID unless necessary and legally reviewed.
- Bangla-first large-button PWA and offline-friendly drafts.

### B. Stock lot management — P0
- Lot record: owner, location, variety, harvest/curing date, initial quantity in **kg**, current available/reserved kg, storage type, grade and verification status.
- Record every stock movement as an event: `HARVEST_ADDED`, `WEIGHED_ADJUSTMENT`, `LOSS_REPORTED`, `RESERVED`, `RESERVATION_RELEASED`, `DISPATCHED`, `DELIVERED`, `RETURNED`.
- Accept local quantity display in maunds, but store kg and explicitly record agreed kg/maund conversion (40 kg is often used in commerce; do not assume universal agreement).
- Reconcile double-booking with database transactions and row-level locking; never compute free stock purely in the browser.
- Multi-lot farmer, partial sales, cancellation and returns.

### C. Storage assessment and visual inspection — P0
- Photo upload with image quality check: minimum visibility, blur, lighting, multiple sampled onions if possible.
- Visible labels: `no_obvious_defect`, `visible_rot_or_mold`, `sprouting`, `physical_damage`, `uncertain_or_low_quality`.
- Structured storage check: days since harvest, curing status, storage type, ventilation, observed smell/moisture, recent weights, temperature/RH if measured.
- Store original image, inspection date, assessor/model version, and evidence; seller can correct flags, agent can review.
- Show **risk band + inspection recommendation**, not an unjustified exact percentage of spoilage or promised shelf-life.
- Optional ESP32 sensor ingestion via HTTPS/MQTT for temperature and humidity; not a prerequisite for all farmers.

### D. Market data and decision intelligence — P0
- Import recorded DAM price reports by market, date, commodity, transaction class, grade where available and source link. Initially use a curated CSV import and source/freshness audits; do not presume a stable public DAM API.
- Weather/agrometeorological advisory feed from BAMIS/approved sources; a manual adapter is fine initially.
- 1/2/4-week price range where enough validated historical data exists, otherwise a clearly labeled seasonal/history baseline.
- Decision engine compares net value of sale now versus hold: expected future available kg × forecast farmgate-realizable price, minus storage, transport, finance and expected quality/quantity loss.
- Recommendations: `SELL`, `HOLD`, `SELL_PART`, or `INSUFFICIENT_DATA`, always with explanation and downside scenario. Recommendations are advisory, not automatic trading orders.

### E. Buyer demand and matching — P0
- Buyer requests: quantity, variety, minimum grade, delivery location, price ceiling/negotiable, desired delivery window, and verified buyer status.
- Offers to a lot or group of lots; seller receives offers and counters/accepts/rejects.
- Match eligibility by stock availability, quality, geolocation, time window, and buyer preferences; then rank by estimated **net farmer proceeds** / total landed cost with transparency.
- Reservations must be time-bound and atomic. Expired/unaccepted reservations release stock automatically.
- Do **not** present buyer enquiry volume as national demand prediction.

### F. Logistics — P1
- Shipment request after acceptance; pick-up and delivery location; quantity, handling type, pickup date.
- Transporter quotation(s): rate, vehicle capacity, proposed pickup time; add routing distance as an estimate, not a guaranteed price.
- Compare delivered proceeds after actual bids, handling, expected loss and fees.
- Statuses: quoted, booked, collected, in transit, delivered, disputed. OR-Tools only once you have multi-stop partner operations and real cost/time constraints.

### G. Order, transaction and settlement — P0
- Quote/order agreed price, unit, grade, quantity and any service fees.
- Immutable order activity, acknowledgements, buyer/seller confirmations, receipt generation and dispute status.
- Payment v1: buyer-entered payment reference plus manual/admin verification, or verified partner sandbox. Never mark paid from the buyer's claim alone.
- No escrow, lending, cash advance or automatic wallet transfer without licensed providers and proper agreements.

### H. Bangla phone assistant — P0 workflow, real PSTN conditional on provider
- Inbound and/or outbound via a telephony-provider adapter; web-based call emulator is a clearly labeled fallback if access to live local numbers is unavailable.
- Voice intents: check prices; my stock; register/adjust quantity; request inspection; obtain hold/sell explanation; check offers; create/counter/accept/reject offer; check orders; schedule transport request; notifications/preferences; connect to agent.
- Call audio -> STT -> bounded intent extraction -> deterministic tool call -> backend result -> Bangla TTS/read-back -> action confirmation -> persisted audit log.
- Financial/order actions require DTMF PIN or OTP and spoken read-back of lot, quantity, price, buyer and amount. Numbers must be interpreted and confirmed deterministically.
- Speech uncertainty -> repeat, keypad fallback, or agent handoff. Never allow unbounded LLM-generated writes or SQL.
- Feature parity means access to the same **business operations**; a basic telephone cannot transmit a diagnostic image. The call can create an inspection request and route an agent/photo-upload link.

### I. Notifications and support — P1
- Event-driven in-app alerts plus provider-based SMS/voice callback for price changes, inspection reminders, buyer offer, reservation expiry, pickup and delivery.
- Consent, quiet hours, retry budget, opt-out and message status tracking.
- Human support queue with handoff transcript/summary and clear disclosure of automated assistance.

### J. Admin and analytics — P0
- Inspect users, lots, data imports, pending verifications, AI runs, support cases, calls and orders.
- Display metrics: verified vs self-reported lots; data freshness; orders completed; disputes; forecast performance; inspected loss rate; time to sale; active districts.
- Dashboard covers **participating platform stock**, not a measured national onion inventory. Optional regional policy analytics require separate sampling/calibration work.

## 5. Core persistent schema

Tables and key fields (all use UUID primary key, timestamps, actor and status where relevant):

| Table | Essential columns |
|---|---|
| `users` / `organizations` / `memberships` | phone, language, roles, verification status, organization link |
| `locations` / `storage_sites` | division, district, upazila, village, optional coordinates, storage type |
| `lots` | owner_id, location_id, variety, harvest_date, grade, initial_kg, available_kg, reserved_kg, last_verified_at |
| `lot_events` | lot_id, actor_id, event_type, delta_kg, related_order_id, evidence_id, idempotency_key |
| `inspections` / `inspection_images` | lot_id, storage observations, image URI, visible flags, model/human label, confidence, reviewer |
| `sensor_readings` | lot/site/device IDs, time, temperature, RH, quality flag (optional) |
| `market_prices` | date, market_id, price_type, unit, low/high, source, collected_at, quality_status |
| `price_forecasts` / `risk_assessments` / `recommendations` | lot or market reference, horizon, low/median/high, model_version, issued_at, expires_at, explanation |
| `buyer_requests` / `offers` | buyer_id, target lot/request, quantity, price, expiry, status |
| `orders` / `order_items` / `reservations` | buyer_id, seller_id, lot_id, agreed kg/price/terms, expiry, status |
| `logistics_quotes` / `shipments` | order, transporter, quote, pickup/delivery, progress, proof |
| `payments` / `payment_evidence` | order, method, claimed_ref, verification status, verified_by |
| `call_sessions` / `assistant_actions` | provider_call_id, user, session, redacted transcript, intent, tool, result, confirmation |
| `notifications` / `support_tickets` | recipient, trigger, channel, status, handoff case |
| `data_imports` / `model_runs` / `audit_logs` | provenance, version, validation report, actor, timestamps |

Database constraints:
- `available_kg >= 0`, `reserved_kg >= 0`, `reserved_kg <= available_kg` (if available_kg represents owned undispatched stock; sellable = available - reserved).
- Reservation and order transitions run in one database transaction using `SELECT ... FOR UPDATE` on involved lot rows and an idempotency key.
- Unique combination of `provider_id + provider_event_id` for webhook deduplication.
- Monetary values use `NUMERIC`/decimal, not float; kg numeric units. ISO UTC timestamps internally, Asia/Dhaka presentation.
- Every important mutation is linked to actor, channel (web/call/admin), and reason.

## 6. API contract (REST v1)

```text
POST   /v1/auth/otp/request                 POST /v1/auth/otp/verify
GET    /v1/me                               PATCH /v1/me
GET    /v1/lots                             POST /v1/lots
GET    /v1/lots/{id}                        POST /v1/lots/{id}/movements
POST   /v1/lots/{id}/inspection-uploads     POST /v1/lots/{id}/inspections
GET    /v1/lots/{id}/risk                   GET  /v1/lots/{id}/recommendation
GET    /v1/market/prices                    GET  /v1/market/forecasts
GET    /v1/buyer-requests                   POST /v1/buyer-requests
GET    /v1/matches                          POST /v1/offers
POST   /v1/offers/{id}/respond              POST /v1/orders
GET    /v1/orders/{id}                      POST /v1/orders/{id}/transition
POST   /v1/logistics/quote-requests        POST /v1/shipments
POST   /v1/payments/{id}/evidence           POST /v1/payments/{id}/verify
GET    /v1/notifications                    GET  /v1/admin/overview
POST   /v1/admin/data-imports              POST /v1/webhooks/telephony/{provider}
```

All responses use versioned JSON schemas, structured error codes and authenticated role checks. Generate OpenAPI automatically and a typed TypeScript client from it. Voice tools wrap these same service operations, rather than duplicating HTTP logic or changing database rows directly.

## 7. Model design and evidence boundaries

### Price forecasting
- Initial comparator: last-value, seasonal naive, and rolling historic median by district/market and class.
- Candidate: lagged feature gradient boosting (LightGBM or scikit-learn HistGradientBoostingRegressor), trained to produce 0.1 / 0.5 / 0.9 quantiles.
- Inputs: lagged market price, harvest calendar, weather/advisories, verified local arrivals where available, import-policy events with recorded dates and sources. Do not use data unavailable at forecast issue time.
- Backtest rolling-origin by months/seasons; report MAE/WAPE, pinball loss, quantile interval empirical coverage against naive baseline.
- Publish AI forecast only where sufficiently superior and calibrated; otherwise mark baseline/insufficient data. Source precision by market and retail/wholesale class.

### Image assessment
- Preprocessing: resolution, lighting/blur check; photo sampling plan; separate visible onion defect classification.
- Short hackathon demonstration: bounded visual-language model or a supervised classifier if a properly labeled dataset exists, with structured output and human override. Explicitly label experimental.
- Production training: locally sourced photos with consent, multiple farms, storage environments, healthy and affected bulbs. Hold out **entire lots/farmers/seasons** in evaluation rather than random frames from the same lot.
- Metrics: per-class precision/recall, high-risk recall, calibration, abstention rate and performance by phone/camera/light.
- Cannot determine hidden rot, bulk lot-wide loss %, or exact remaining shelf life from a single surface photo.

### Spoilage and mass-loss assessment
- Tier 1: conservative rules from days stored, curing, visible condition, storage structure, reported ventilation, weather and measured environmental readings.
- Tier 2: observed change from repeated weighed samples / inspections; train logistic or hazard model only after sufficient longitudinal labels exist.
- Tier 3: survival/mass-loss prediction with uncertainty, validated across local conditions. Report distinct pathways: visible rot, sprouting, moisture loss, physical damage.
- Output inspection urgency and high/medium/low risk, not an unsupported numeric decay trajectory.

### Hold/sell engine

```text
sell_now_net = sellable_kg * verified_realizable_now_price_per_kg
               - sale_cost_now - immediate_transport_cost
hold_net_scenario(t) = expected_sellable_kg(t) * realizable_price_scenario(t)
                       - storage_cost(t) - finance_cost(t) - future_transport_cost(t)
                       - transaction_cost(t)
recommendation = compare downside / median / upside with liquidity_need and buyer offers
```

Show outputs as scenarios plus reason, never guaranteed gain. A `SELL_PART` may be the right result when the farmer has immediate cash needs and wants to retain some stock. If a trusted matched buyer has a confirmed price, prefer that realized offer over a speculative price forecast.

### Matching and logistics
- Start with rules + transparent ranking: qualified quantity, grade, geography, ability to deliver, buyer offer terms and net farmer returns.
- Simple quote comparison first. Add min-cost flow / OR-Tools pickups and deliveries only with real truck rates, time windows, and multi-stop density.

### Bangla speech
- STT `bn-BD` where supported, TTS `bn-BD`, test on low-bandwidth real calls, varied regional dialects and noisy environments.
- Use intent grammar/finite-state dialogue for money amounts, units, place names, yes/no; LLM only for understanding/explanation and tool selection from an allowlist.
- Record WER/intent accuracy by test set; DTMF fallback. No voice-biometric authentication.

## 8. State machines

```text
Lot: DRAFT -> SELF_REPORTED -> VERIFIED -> LISTED -> PARTLY_RESERVED
                                          -> FULLY_RESERVED -> DISPATCHED -> CLOSED
Offer: CREATED -> SENT -> COUNTERED / ACCEPTED / REJECTED / EXPIRED
Order: PENDING_CONFIRMATION -> CONFIRMED -> PICKUP_PLANNED -> DISPATCHED
                                -> DELIVERED -> SETTLEMENT_PENDING -> SETTLED
   alternate branches: CANCELLED / DISPUTED / FAILED
Payment: UNVERIFIED -> EVIDENCE_SUBMITTED -> VERIFIED / REJECTED
Call tool: REQUESTED -> VALIDATED -> READ_BACK -> AUTHORIZED -> COMMITTED / CANCELLED
```

Reservation expiry must be a background task plus expiry verification inside every order transition. A reservation cannot be accepted twice from two devices. A phone call interrupted before confirmation must leave the order unchanged.

## 9. Voice-call flow

Example: farmer says in Bangla, “আমার ২০ মণ পেঁয়াজের জন্য ঢাকার অফারটা গ্রহণ করব।”
1. Telephone provider delivers authenticated call event, or a demo simulator creates the same event format.
2. Voice session resolves phone number to account; for private business data require PIN/OTP where necessary.
3. STT transcribes; intent parser extracts `offer_accept` and quantity. Parse Bangla digits, `মণ`, `কেজি` and market-defined unit conversion.
4. Backend fetches authorized active offers, checks lot availability and price, and returns candidate action details.
5. TTS reads exact buyer, quantity in kg and maunds, total payment, grade, transport responsibility and expected deductions.
6. Farmer confirms by keypad/PIN or OTP; if unclear, no action.
7. Backend uses idempotent transaction to reserve quantity and accept offer.
8. System speaks confirmation and sends in-app/SMS receipt. Same order appears immediately in buyer and farmer web dashboards.

High-impact phone actions: stock sale, changing owner/custodian, receiving sensitive information, payment/loan-related steps. Inactivity or accidental disconnect must not finalize them. Unsupported image capture generates an inspection task, not a false image diagnosis.

## 10. Data acquisition and provenance

| Dataset | Source option | Ingestion plan | Risk |
|---|---|---|---|
| Onion prices | Bangladesh Department of Agricultural Marketing market reports | Curated CSV/manual import initially; automate only if permitted and stable | Market/grade and wholesale-vs-retail mismatch |
| Weather/advice | Bangladesh Agro-Meteorological Information Service (DAE/BAMIS) | Official public advisories with timestamp, cite and source URL | Outdoor weather is not interior storage temperature |
| Farmer stock | User reports, agent weighing/inspection | Self-reported and verified fields separately | Misreporting, selection bias |
| Buyer demand | Buyer requests/orders on platform | Transactional events, not national demand truth | Sparse network effects |
| Image defects | Consent-based lot photo sessions | Evidence and manual ground truth | Camera bias; invisible interior rot |
| Logistics rates | Quotes from participating transporters | Actual quotes and valid until timestamp | Distance does not determine final freight cost |
| National production | DAE/BBS statements where verifiable | Annual contextual indicators, never substitute for active inventory | Different crop years, estimation revisions |

Store `source_url`, `source_record_id`, `collected_at`, `observed_at`, `verified_by`, `is_synthetic`, `valid_until`, `import_batch_id` and quality flag where relevant.

## 11. Security / safety / data governance

- Auth: phone OTP + rate limiting; PIN/OTP for high-impact actions, not caller ID alone.
- Authorization: ownership checks on every resource; scoped delegation for agents; buyer access to agreed lot fields only.
- Never upload sensitive data to arbitrary AI providers by default. Obtain explicit consent for voice recording and image/model processing; disclose AI and calls.
- Redact phone number and any authentication codes in logs/transcripts; minimize retention and offer deletion subject to legal needs.
- Telephony webhook signature validation, replay/deduplication defense, signed media URLs and expiring upload links.
- All credit/payment/escrow functionality off by default until vendor and legal requirements are settled.
- Daily backups, tested restore, audit log, secret manager, health checks and alerting.
- `SIMULATED` watermark for fixtures, fake offers, synthetic photo outcomes or forecasts.
- Compliance review for Bangladesh telecom and personal data requirements before live deployment; no assumed permission to use USSD short codes.

## 12. Repository contract

```text
peyajflow/
  apps/
    web/                  # Next.js role-based PWA
    call-simulator/       # only if separate; same voice webhook contract
  services/
    api/
      app/
        auth/ users/ lots/ inspections/ market_data/ decisions/
        offers/ orders/ logistics/ payments/ notifications/ telephony/ admin/
      migrations/
      tests/
    worker/               # Celery tasks/ETL/media processing
  ml/
    prices/ vision/ spoilage/ evaluations/
  packages/
    api-client/           # generated TS OpenAPI client
    domain-contracts/     # schemas/events shared with channels
  data/
    fixtures/ imports/ labeling-guides/
  infra/
    docker-compose.yml
    Dockerfile.api
    Dockerfile.worker
  docs/
    architecture.md
    api.md
    data-dictionary.md
    sources-register.md
    demo-script.md
    threat-model.md
  .github/workflows/
  README.md
```

Recommend: one repository; automatic formatting/lint/type checks, tests and migrations in CI; feature flags for telephony, external payment, model outputs, sensor feeds and demo mode.

## 13. Build sequence and responsibilities

**Milestone 1 — Transactional vertical slice:** environment/CI, DB migrations, auth, two roles, stock lots, events, buyer request/offer, atomic reservation/order, basic dashboard. This must work before AI polish.

**Milestone 2 — Intelligence:** DAM import UI + provenance, simple market chart and naive baseline, photo upload and inspect flow (manual / experimental model explicitly labeled), risk rules and hold/sell simulator.

**Milestone 3 — Alternative voice channel:** deterministic intent tool registry, Bangla TTS/STT, read-back, DTMF confirmation, local call gateway if independently tested; otherwise realistic call simulator. Implement exact same offer action as PWA.

**Milestone 4 — Complete trade and proof:** logistics quote, order status, settlement evidence, alerts, admin traceability, telemetry/error tracking, integration/E2E tests, credible demo fixture dataset.

Suggested team ownership: frontend/PWA, core backend/DB, AI-data, voice/telephony, QA/demo/integration; people may combine roles. Never block the core platform on a particular external telephony, weather, or payment vendor.

## 14. Acceptance tests (must pass before demo)

1. Farmer creates a 1,000 kg lot; trader sees only eligible public listing data.
2. Agent adds an inspection; uploaded image is stored with provenance and risk status is generated as *experimental/verified* appropriately.
3. Admin imports dated real or clearly synthetic prices; outdated observations show `STALE` not `LIVE`.
4. Advice has a price range/scenario, loss assumption, and basis; missing data yields `INSUFFICIENT_DATA`.
5. Buyer offers to purchase 200 kg; farmer accepts; available stock and reserved stock update once across every channel.
6. Two concurrent buyer acceptance requests cannot reserve more than the lot's sellable quantity.
7. Voice assistant reads a buyer offer, uses PIN/DTMF confirmation, executes same backend transaction, and can retrieve the same order ID.
8. Incorrect transcript, PIN mismatch or call disconnect causes no order creation or modification.
9. Delivery status and settlement evidence are visible; paid status is not accepted without verification.
10. Actor permissions prevent another farmer from changing the lot; critical actions appear in audit log.
11. Demo can run with a clean database + seeded synthetic fixtures, and can be re-run reproducibly.
12. Source link, observed date, and synthetic/experimental badges appear in all decision screens.

## 15. Demo story

Pabna farmer registers stock in kg and local maunds -> uploads sample stock photos -> receives visible defect flags + storage advice -> checks two price scenarios -> sees `SELL_PART` because of a qualified Dhaka buyer offer and condition uncertainty -> buyer submits offer -> farmer calls PeyajFlow in Bangla and accepts part of stock after read-back and PIN -> backend reserves amount atomically -> transport quote appears -> buyer and seller dashboards show one synchronized order -> delivery and verified settlement update the ledger -> admin shows traceable evidence and model limitations.

Use **clearly labeled sample values** in the hackathon narrative. Do not represent a simulated model output or manually seeded price as a deployed agricultural forecasting success.

## 16. Scope boundaries / production roadmap

**Hackathon P0:** identity, stock/inspection, price import/history, baseline and candidate models, interpretable hold/sell advice, buyer offers/orders, stock reservation, Bangla call workflow with tested provider or clearly labeled simulator, admin/audit.  
**Hackathon P1 if capacity:** transport quotation and trip milestones, SMS, sensor demo, offline sync queue.  
**After pilot evidence:** calibrated real-life visual-risk and loss predictions, price model deployment only when better than baseline, extensive voice dialect testing, live telephony/vendor contracts, automated settlement, nationwide demand/stock inference, IoT mass deployment, lending/government dashboards.

**No-go conditions:** stock over-selling; wrong owner access; actual payment marked successful without external verification; phone accepting irreversible action without confirmation; price/rot model falsely presented as validated; inability to distinguish demo and live data.

## 17. Verification references (accessed 2026-11-12)

- Department of Agricultural Marketing reports: https://market.dam.gov.bd/commodity_wise_report?L=E
- Department of Agricultural Marketing daily report: https://market.dam.gov.bd/market_daily_price_report/?L=E
- BAMIS / DAE portal: https://www.bamis.gov.bd/en/page/about-bamis-portal/
- Google Cloud Speech-to-Text supported languages (bn-BD): https://docs.cloud.google.com/speech-to-text/docs/speech-to-text-supported-languages
- Google Cloud Text-to-Speech bn-BD: https://docs.cloud.google.com/text-to-speech/docs/gemini-tts
- BTCL Alaap Cloud Contact Center (IVR; adapter/API requirements to be verified commercially): https://www.alaapcloud.gov.bd/en/contact
- Twilio Bangladesh voice pricing and number caveats: https://www.twilio.com/en-us/voice/pricing/bd and https://www.twilio.com/en-us/sip-trunking/pricing/bd
- 2026 Bangladesh onion IoT storage field study: https://onlinelibrary.wiley.com/doi/10.1111/jfpe.70763
- Onion postharvest storage review: https://onlinelibrary.wiley.com/doi/full/10.1002/fpf2.12009
- scikit-learn quantile boosted tree API: https://sklearn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html
- OR-Tools pickup/delivery methods: https://developers.google.com/optimization/routing/pickup_delivery
- PostgreSQL row locking: https://www.postgresql.org/docs/current/sql-select.html

**Architectural sign-off:** Favor a truthful complete *transactional vertical slice* over a visually impressive collection of disconnected AI demos. The differentiator is an integrated, explainable, traceable cycle from observed stock to a confirmed sale across both web and Bangla phone channels; whether that is truly novel relative to market competitors still needs a dedicated, source-backed comparison.


---

## FILE: `ops/GIT_WORKFLOW.md`

# GitHub branch-by-feature workflow

1. Ensure `git remote -v` matches the authorized PeyajFlow repository. Do not default to a similarly named unrelated repository. Verify `gh auth status` without printing token material.
2. Initialize GitHub Actions CI, configure review policy and branch protection after permissions exist. Require status checks, disallow force-push, prefer squash merge for reviewable history.
3. Follow the feature ordering in `product/FEATURE_BACKLOG.md`. Each feature: create branch, implement backend & UI & tests, inspect `git diff --check`, run tests, commit, push, create PR, review CI output, fix, merge, update implementation log.
4. Every PR includes: user story, test commands/results, screenshots or terminal evidence, DB migration and rollback notes, data source/evidence disclaimer, dependencies and issue linkage.
5. After merge, confirm main CI; verify Vercel/Render deployment status and smoke the URL. Update deployment status SHA and verify no regressions. Then move to next feature.
6. On failure, do not hide it by marking 'done'. Make a small fix commit on same branch, rerun CI, keep a regression test. Revert a faulty production feature with a reviewed commit, not destructive history edits.
7. Weekly or milestone release tags `v0.x.y` only after all gates pass; link changelog and known limitations.

If GitHub repo not available, CodeX should initialize `git`, create reproducible local commits and supply instructions to connect remote. If external tool access is available, create remote only with user's authorization and agreed owner/name/visibility. A private repo is preferred for sensitive experimental data. **No farm PII or secret files should ever enter the repo.**


---

## FILE: `ops/QUALITY_GATES.md`

# Quality gates, CI and release evidence

## Mandatory pipelines
- `pnpm install --frozen-lockfile`, formatting, lint, frontend TypeScript `typecheck`, build, unit tests.
- Python `ruff check`, `ruff format --check`, `pytest` (incl API/integration), dependency vulnerability scan as available.
- Migration validation: Alembic heads == one, apply from empty DB; assert startup matches migration head; check constraints and transactional rollback.
- Playwright chromium smoke after seeded test DB: login, lot create, upload mock inspection, buyer demand, offer, confirmed partial order, remaining quantity, opposite role views. Add responsive screenshots and axe checks.
- Security: request identity cannot be spoofed by client IDs, IDOR on lots/orders/images, invalid voice tools blocked, duplicate webhook/idempotency, upload files safe, row permissions, logs redact PII.
- Condition intelligence: test explicit uncertainty/abstention when no reliable inputs or unsupported categories, seasonal price baselines with temporal splits (no leakage).

## PR gate
A feature PR requires: clear scope, linked checklist, screenshot if visual, schema migration, API specification change, tests, explicit demo/data labeling, risk assessment, rollback concern, green checks. One PR at a time can be safest for a small team; parallel branches permitted only if independent and integrated/tested before merge. Don't merge solely on visual appearance.

## Production release gate
- Last green main SHA, migrations, successful build and smoke, real env readiness, HTTPS/cookies/CORS check, operator read/write test, content security basics, no exposed keys, data backups, health dashboards and rollback path.
- Separate statuses: `implemented`, `tested locally`, `pushed`, `PR merged`, `preview deployed`, `production deployed`, `field validated`. Never collapse them into one checkbox.
- Final status document with timestamp, git SHA, artifact checksum, preview/prod URLs, direct command outputs and remaining blockers.

## Suggested commands (agent must adapt to real monorepo)
```
pnpm install --frozen-lockfile
pnpm lint
pnpm typecheck
pnpm test
pnpm --filter web build
cd services/api && uv sync --frozen && uv run ruff check . && uv run pytest -q
cd ../../ && pnpm exec playwright test
```
Install and pin tooling before claiming these run. In CI use service containers for PostgreSQL/Redis and protected secrets; avoid production credentials.


---

## FILE: `ops/DEPLOYMENT.md`

# Render + Vercel deployment plan — reproducible, honest automation

## Chosen topology
- **Vercel**: `apps/web` Next.js production and preview deployments, connected to the actual GitHub repository.
- **Render**: containerized FastAPI API service, optional Celery background worker, managed PostgreSQL, optional Render Key Value/Redis-compatible broker (subject to availability/pricing). Store images on external S3-compatible service with explicit bucket policy and allowed origins.
- **GitHub Actions**: validate PRs and main. Git push/merge triggers Vercel and Render Git-based deployments after repo/provider connections are approved. `render.yaml` Blueprint can help provision and keep Render settings reproducible; confirm syntax/plan availability in current Render docs before applying.
- Do not put FastAPI + persistent Redis/Celery + model inference into a default Vercel serverless function assuming it runs forever. Long jobs remain on worker; use an explicit managed service.

## Provider authorization boundaries
Codex may prepare all code, configs, scripts, tests, workflows and render blueprint without asking. Actual first-time GitHub repo creation, org access, Vercel import, Render project/service/database provisioning, DNS record change, paid plan activation, phone number acquisition, SMS credit purchase, AI API key configuration and production secret entry require valid connected account permissions and user authorization. Never claim autonomous deployment if those are unavailable. Never print credentials or commit `.env`.

## Repository and environments
- `main`: protected, tested and auto-deploys to production after merge.
- `feat/*`: isolated branch/PR, Vercel preview if connected. API branch preview only if deliberately configured; otherwise use staging API/test fixtures and avoid write access to production.
- `staging`: optional when branch-based previews of backend are needed; prevent accidental migrations against production.
- Env templates: `.env.example` at root + `apps/web/.env.example` and `services/api/.env.example`; document every key, type, defaults and whether sensitive.
- Name public URLs explicitly (`WEB_ORIGIN`, `API_PUBLIC_BASE_URL`, `CORS_ORIGINS`) and avoid `NEXT_PUBLIC_` for secrets.
- In production, authentication cookies: Secure, HttpOnly, SameSite appropriate, and CSRF protections when cookie-based. Rate limiting per user/IP and call webhook, no passwordless demo login enabled.

## Deployment sequence for agent
1. Inspect existing Git remotes and authorized apps. Confirm branch protections and pass CI.
2. Run `docker compose up --build` for API + PostgreSQL + Redis (worker optional); execute migrations, seed only demo environment and health check; validate API docs/OpenAPI.
3. Test `pnpm --filter web build` and static checks with `NEXT_PUBLIC_API_BASE_URL` set correctly, use server-side proxy where feasible.
4. Validate Render Blueprint YAML against current docs; create or import Blueprint only with authorized accounts. API Dockerfile must honor `$PORT` and bind `0.0.0.0`. Deploy API, DB, broker and worker using environment references, not hardcoded passwords.
5. Run non-destructive Alembic `upgrade head` as a single controlled predeploy/release step; do not let parallel API replicas race migrations. Backups and rollback must be planned; never rollback data migrations without review.
6. Import GitHub repo in Vercel with project root `apps/web` / appropriate monorepo build command. Set production and preview env separately, confirm API CORS/rewrite rules.
7. Verify HTTPS production API `/health/live` and `/health/ready`, CORS from frontend, session login and actual DB read/write, S3 upload, worker queue, and all P0 business mutations; test on mobile.
8. Attach custom domain only if DNS control exists. Domain `peyajflow.boraq.io` is **not** automatically owned or controlled by this repo; do not modify it without explicit approval.
9. Configure GitHub/Vercel/Render automatic deploy on passing/merged main. Avoid insecure workflow secrets in fork PRs. Record each deployed URL, SHA and health result.
10. Test rollback by redeploying prior commit only when schema compatible; otherwise provide recovery plan and backups.

## Suggested environment variable inventory
API: `DATABASE_URL`, `REDIS_URL`, `S3_ENDPOINT`, `S3_BUCKET`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `CORS_ORIGINS`, `WEB_ORIGIN`, `JWT_SIGNING_KEY` or managed auth config, `ENVIRONMENT`, `DEMO_MODE`, `MODEL_ARTIFACT_PATH`, `LOG_LEVEL`, `VOICE_WEBHOOK_SECRET`, `STT_PROVIDER_KEY`, `TTS_PROVIDER_KEY`, `SMS_PROVIDER_KEY`.
Web: `API_INTERNAL_BASE_URL` (server-side), `NEXT_PUBLIC_SITE_URL` (public), `NEXT_PUBLIC_DEMO_MODE` (nonsecret only). If provider uses browser-only API origins, document why and allowlist CORS.

## Deployment failure triage
- 502/503: check Render service bind to `$PORT`, health, cold start, DB reachability and application logs.
- 401/cross-origin: inspect cookies, auth domain, CSRF, CORS origins, HTTPS and preflight.
- Migration failure: stop promotion, inspect schema and backup, avoid destructive auto-fixes.
- Upload failure: bucket permissions, max size, content type, signed URL expiry, CORS.
- Worker mismatch: broker URL, queue name, worker process and model artifact path; ensure no unbounded model load.
- CI succeeds but UI broken: smoke tests actual provider preview URL, screenshots, env differences, stale cache.
- Phone not working: distinguish provider account access, inbound number, webhook signature, media/IVR capabilities and STT failures. Switch to explicit simulation and record blocker.

## Cost discipline
Render and Vercel plan quotas/pricing change; verify current offerings before selecting. Prepare `docs/COST_ESTIMATE.md` using actual selected region, service size, PostgreSQL storage, worker uptime, image storage, phone minutes and AI inference. Do not guarantee free persistent DB/worker or free Bangladesh calling.


---

## FILE: `templates/env.example`

# Never commit actual values. Create env files locally and set production secrets in providers.
ENVIRONMENT=development
DEMO_MODE=true
DATABASE_URL=postgresql+psycopg://peyajflow:local-only-password@localhost:5432/peyajflow
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:3000
WEB_ORIGIN=http://localhost:3000
API_PUBLIC_BASE_URL=http://localhost:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3000
NEXT_PUBLIC_DEMO_MODE=true
S3_ENDPOINT=
S3_BUCKET=
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=
JWT_SIGNING_KEY=SET_IN_SECRET_MANAGER
VOICE_WEBHOOK_SECRET=SET_IN_SECRET_MANAGER
STT_PROVIDER_KEY=
TTS_PROVIDER_KEY=
SMS_PROVIDER_KEY=


---

## FILE: `templates/render.example.yaml`

# Example only: Codex should verify latest Render Blueprint syntax, plan and availability
# before adopting as `render.yaml`. Database/env references and worker eligibility depend on account.
services:
  - type: web
    name: peyajflow-api
    runtime: docker
    rootDir: services/api
    dockerfilePath: ./Dockerfile
    healthCheckPath: /health/ready
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: DEMO_MODE
        value: 'false'
      - key: DATABASE_URL
        fromDatabase:
          name: peyajflow-db
          property: connectionString
      - key: CORS_ORIGINS
        sync: false
      - key: JWT_SIGNING_KEY
        generateValue: true
      - key: S3_ENDPOINT
        sync: false
      - key: S3_BUCKET
        sync: false
      - key: S3_ACCESS_KEY_ID
        sync: false
      - key: S3_SECRET_ACCESS_KEY
        sync: false
# Background worker, Redis and migrations are intentionally not added automatically here:
# enable after implementation and plan verification; migrations must run once before promotion.
databases:
  - name: peyajflow-db
    databaseName: peyajflow
    user: peyajflow


---

## FILE: `.github/workflows/ci.example.yml`

# Template only; adapt paths, lockfiles, scripts and Python environment before enabling.
name: ci
on:
  pull_request:
  push:
    branches: [main]
jobs:
  web:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: .
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with:
          version: 10
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm lint
      - run: pnpm typecheck
      - run: pnpm test
      - run: pnpm --filter web build
  api:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_USER: test
          POSTGRES_DB: peyajflow_test
        ports: ['5432:5432']
        options: >-
          --health-cmd 'pg_isready -U test' --health-interval 10s --health-timeout 5s --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: cd services/api && uv sync --frozen
      - run: cd services/api && uv run ruff check .
      - run: cd services/api && uv run ruff format --check .
      - run: cd services/api && uv run pytest -q
        env:
          DATABASE_URL: postgresql+psycopg://test:test@localhost:5432/peyajflow_test
