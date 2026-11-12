# PeyajFlow

PeyajFlow is a Bangladesh-first onion supply-chain platform. The first milestone builds a traceable trade from a farmer's stock lot to a buyer's confirmed order, starting with the Pabna-to-Dhaka pilot.

The current foundation serves a Bangla and English workspace status page backed by a FastAPI service and PostgreSQL readiness checks. See [work status](WORK_STATUS.md) for verification, the implementation order, and outstanding work. The [original handoff](PeyajFlow_Codex_Master_Handoff.md) remains the product and architecture reference.

## Run locally

Install Node.js 22 or later, pnpm 10.34.9, and Docker with Compose. Python 3.13 and uv are required for host-native API development.

```sh
docker compose up --build -d
pnpm install --frozen-lockfile
pnpm dev
```

Open `http://localhost:3000` for Bangla or `http://localhost:3000/en` for English. The API serves OpenAPI documentation at `http://127.0.0.1:8000/docs`. Its `/health/live` checks the application process and `/health/ready` returns HTTP 200 only when PostgreSQL is reachable and its Alembic revision matches the application. Compose runs migrations before the API starts and stores database files in a named volume.

Compose defaults are for local development. Copy the root `.env.example` to `.env` to override ports or PostgreSQL credentials. For custom local passwords, use URL-safe characters because Compose interpolates the password into the connection URL. Copy `apps/web/.env.example` to `apps/web/.env.local` to change the server-side API address when running Next.js on the host. Neither port nor database credentials are needed in the browser.

### Run the API on the host

Start PostgreSQL alone with `docker compose up -d db`. In `services/api`, copy `.env.example` to `.env` and adjust the connection URL if needed.

```sh
uv sync --locked
uv run --env-file .env alembic upgrade head
uv run --env-file .env uvicorn app.main:app --reload
```

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

For the PostgreSQL integration check, point `DATABASE_URL` to a disposable local test database. Run `uv run --locked alembic upgrade head`, `uv run --locked alembic check`, and `uv run --locked pytest -q` against that database. The database integration test skips when the variable is absent.
