# PeyajFlow

PeyajFlow is a Bangladesh-first onion supply-chain platform. The first milestone builds a traceable trade from a farmer's stock lot to a buyer's confirmed order, starting with the Pabna-to-Dhaka pilot.

The bilingual pilot workspace supports sign-in with fictional accounts, stock and weight history, buyer demand, offers, reserved orders, photo inspections, human condition review, and storage-risk triage. See [work status](WORK_STATUS.md) for verification and remaining work. The [original handoff](PeyajFlow_Codex_Master_Handoff.md) is the product and architecture reference.

## Run locally

Install Node.js 22 or later, pnpm 10.34.9, and Docker with Compose. Python 3.13 and uv are required for host-native API development. Copy `apps/web/.env.example` to `apps/web/.env.local` for the local HTTP session cookie setting.

```sh
docker compose up --build -d
docker compose exec api python -m app.seed
pnpm install --frozen-lockfile
pnpm dev
```

Open `http://localhost:3000/bn/workspace` for Bangla or `http://localhost:3000/en/workspace` for English. The API serves OpenAPI at `http://127.0.0.1:8000/docs`. Its `/health/live` checks the process and `/health/ready` checks PostgreSQL and the current Alembic revision. Compose migrates before starting the API and persists PostgreSQL and private inspection photos in named volumes.

Compose defaults are for local development. Copy the root `.env.example` to `.env` to override ports or PostgreSQL credentials. For custom local passwords, use URL-safe characters because Compose interpolates the password into the connection URL. Copy `apps/web/.env.example` to `apps/web/.env.local` to change the server-side API address when running Next.js on the host. Neither port nor database credentials are needed in the browser.

### Run the API on the host

Start PostgreSQL alone with `docker compose up -d db`. In `services/api`, copy `.env.example` to `.env` and adjust the connection URL if needed.

```sh
uv sync --locked
uv run --env-file .env alembic upgrade head
uv run --env-file .env python -m app.seed
uv run --env-file .env uvicorn app.main:app --reload
```

### Try the pilot

1. Sign in as **Rahim** and list a 1,000 kg lot in Pabna. Enter kilograms or enter maunds with the agreed kg-per-maund conversion.
2. Sign in as **Jalil** in a separate browser session and verify Rahim's stock. Jalil is assigned to Rahim's lots.
3. Sign in as **Nadia**, create a demand, find matching supply, and make an offer for 200 kg. As Rahim, review and confirm the offer. Both sessions see the same order and Rahim's lot shows the reservation.
4. As Rahim, submit a storage inspection with two to four photos and manual observations. As Jalil, review the evidence. Open **Storage risk** to see the reasons, missing evidence, and suggested inspection urgency.

Demo accounts require `APP_ENV=development` or `test` together with `DEMO_MODE=true`. Production environments reject demo login and demo sessions. Live OTP enrollment requires a provider integration. Cookie security defaults to HTTPS. Set `APP_COOKIE_SECURE=false` for a local HTTP preview only.

Local photo mode requires `PHOTO_STORAGE=local` in development or test. Set `PHOTO_DIR` to override the private directory. Hosted photo storage uses `PHOTO_STORAGE=s3` and `S3_BUCKET`, with optional `S3_ENDPOINT` and `S3_REGION`. Use runtime AWS credentials or `S3_ACCESS_KEY_ID` and `S3_SECRET_ACCESS_KEY`. Configure a private bucket. Authorized clients retrieve sanitized JPEGs through the API. Uploads accept JPEG, PNG, and WebP with a 3 MiB and 12 megapixel limit per photo.

Storage risk is a checklist triage result. The current rules consider evidence freshness, reported moisture, odor and visible defects, curing, ventilation, measured humidity, and measured temperature. Photo rules flag evidence quality. People record and review visible defects. The pilot keeps the submitted observation and correction history. [UC Davis dry-onion handling reference](https://postharvest.ucdavis.edu/produce-facts-sheets/onions-dry)

### Checks

```sh
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
cd services/api
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -q
```

For API integration tests, set both `DATABASE_URL` and `TEST_DATABASE_URL` to a disposable PostgreSQL database. Run `uv run --locked alembic upgrade head`, `uv run --locked alembic check`, and `uv run --locked pytest -q` against it. Tests create fictional records and exercise concurrent transactions.

With the seeded API and web workspace running against a disposable database, install Chromium with `pnpm --filter @peyajflow/web exec playwright-core install chromium` and run `pnpm test:e2e`. Set `E2E_WEB_ORIGIN` for a different port and `PLAYWRIGHT_CHANNEL=msedge` to use installed Edge. Set `E2E_SCREENSHOT_DIR` to capture visual evidence.
