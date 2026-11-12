# PeyajFlow deployment and recovery

The production configuration uses a Render API and private PostgreSQL database, Vercel for the Next.js workspace, and a private S3-compatible bucket for inspection photos. The repository includes both platform configurations and a release smoke command. A workspace owner needs to connect the repository and approve provider accounts, billing, and data location before importing the blueprint.

## Prepare the release

1. Run the web and API checks, then verify the container and restore jobs in CI against the intended commit. Record the tested image or commit and Alembic revision.
2. Create a dedicated private photo bucket with encryption, public access blocked, and versioning enabled. Set `S3_BUCKET` and the appropriate `S3_REGION`, `S3_ENDPOINT` for a compatible provider, and least-privilege runtime credentials in Render's secret settings. The API needs object write, read, and delete permissions for this bucket. Retain backups according to the agreed inspection consent and retention policy.
3. Import `render.yaml` into the approved Render workspace. It selects Singapore and paid instances for a pre-deploy migration hook. Confirm plan availability, costs, and backup retention in that workspace. Set `APP_ENV=production` and `DEMO_MODE=false`. Keep carrier and SMS disabled until the provider checks below pass. [Render Blueprint specification](https://render.com/docs/blueprint-spec) · [Render pricing](https://render.com/pricing)
4. The pre-deploy hook runs `/app/.venv/bin/python -m app.migrate`. PostgreSQL permits one migration runner at a time. Take and verify a backup before the hook applies a revision to pilot data. Check `/health/live` and `/health/ready` after the deploy. Readiness returns `migration_required` when the running API and schema are on different revisions. Preview schema changes on a restored copy before using a rolling deployment.
5. In Vercel, set the project root to `apps/web`, include source files outside the root so the build sees the pnpm workspace and lockfile, and use Node.js 24. Set server-side `API_INTERNAL_BASE_URL` to the deployed Render HTTPS origin. Use the default secure session cookie setting. Deploy the same commit and open the Bangla and English workspace URLs. The browser compresses large inspection batches to 3 MB of image data before sending the form, leaving room for multipart overhead. [Vercel project configuration](https://vercel.com/docs/project-configuration/vercel-json) · [Vercel Function limits](https://vercel.com/docs/functions/limitations)
6. After the first smoke and recovery checks pass, configure production deployments from protected `main`. Point Vercel previews at a staging API and keep preview writes separate from pilot data. Enable Render's CI-gated deploy trigger after verifying the required GitHub checks. [Render deploy settings](https://render.com/docs/deploys)

Provision a production account through an authorized terminal that has database access. Use an operator identity for administration and a dedicated least-privilege account for recurring smoke tests. The CLI prompts for the passphrase. Use `--prompt-verified-phone` only when the operator has independently verified a phone number, then have the account holder opt in through Alerts. OTP enrollment is pending provider integration.

```sh
/app/.venv/bin/python -m app.credentials release-operator --role admin \
  --name 'Release Operator' --district Pabna --organization PeyajFlow
/app/.venv/bin/python -m app.credentials release-operator --replace-password
```

Run the release smoke from the repository root. Supply `SMOKE_USERNAME` and `SMOKE_PASSWORD` as environment secrets for the optional signed-in checks. The smoke verifies liveness, readiness, locale redirect, response headers, sign-in, profile and inbox access, and session revocation. After deployment, sign in through the HTTPS workspace and verify one sanitized private photo upload and retrieval with consent, including a retrieval denial from a different account. Record the date, deploy IDs, and observed results.

```sh
SMOKE_API_ORIGIN=https://api.example.invalid \
SMOKE_WEB_ORIGIN=https://app.example.invalid \
SMOKE_EXPECT_PRODUCTION=1 pnpm smoke
```

## Verify the carrier and SMS services

Set `PUBLIC_API_ORIGIN` to the exact public HTTPS origin Twilio uses in its callback URLs. Store `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` in Render. Send signed form-encoded POSTs to the paths below. PeyajFlow verifies the signature and account and records a fingerprint to handle retries. [Twilio request validation](https://www.twilio.com/docs/usage/security)

| Feature | Configuration and acceptance |
| --- | --- |
| Carrier | Set `TELEPHONY_PROVIDER=twilio`. Point the inbound number at `/v1/webhooks/telephony/twilio` and its status callback at `/v1/webhooks/telephony/twilio/status`. The inbound response sends keypad selections to `/v1/webhooks/telephony/twilio/menu`. Optionally set `TWILIO_VOICE_GREETING_URL` to an authorized HTTPS recording. Test inbound, menu selection, no input, disconnect, and duplicate status. The default public menu is in English. Live caller identification, account linking, speech recognition, and private actions are outside this adapter. The Bangla demo simulator remains the acceptance path for voice trades. [Twilio Gather](https://www.twilio.com/docs/voice/twiml/gather) |
| SMS | Set `SMS_PROVIDER=twilio` and `TWILIO_MESSAGING_SERVICE_SID` to a service approved for the destination. Configure signed Advanced Opt-Out callbacks to `/v1/webhooks/messaging/twilio/opt-out`. Outbound sends specify `/v1/webhooks/messaging/twilio/status`. Verify consent, quiet hours in Asia/Dhaka, a delivery receipt, and STOP with an approved test number. STOP disables further queued SMS. A message already being sent cannot be recalled. [Twilio message resource](https://www.twilio.com/docs/messaging/api/message-resource) · [Twilio Advanced Opt-Out](https://www.twilio.com/docs/messaging/tutorials/advanced-opt-out) |

During an incident, set the affected provider flag to `disabled` and redeploy the API. The in-app inbox remains available. Use Operations to check pending sends, sends needing review, and recent carrier callbacks. Reconcile `unknown` sends with the provider before contacting a user again. A send with an uncertain outcome is excluded from automatic retries.

## Back up and restore

Keep scheduled managed PostgreSQL backups and an encrypted copy accessible to the recovery operator. Record backup and restore timestamps, the Alembic head, and the photo backup version. Restore tests need an isolated database and bucket with outbound integrations disabled. Use the provider's PostgreSQL client connection string via `PGDATABASE` and secure credentials, or configure the standard `PG*` variables. The commands below assume a new empty restore database and PostgreSQL client tools compatible with the server. [PostgreSQL `pg_dump`](https://www.postgresql.org/docs/current/app-pgdump.html) · [PostgreSQL `pg_restore`](https://www.postgresql.org/docs/current/app-pgrestore.html)

```sh
pg_dump -Fc --no-owner -f peyajflow.dump
pg_restore --dbname="$RESTORE_DATABASE" --exit-on-error --single-transaction \
  --no-owner peyajflow.dump
psql "$RESTORE_DATABASE" -Atc 'SELECT version_num FROM alembic_version'
```

Verify the restored revision, representative inventory balances and order history, inbox records, and a private photo retrieved from the matching bucket backup. Then run readiness and the smoke command against the isolated restore. Use fictitious data for rehearsals when possible. The CI container job exercises the PostgreSQL dump and restore path with disposable data.

## Monitor and roll back

- Monitor readiness, 5xx and 429 rates, provider queue counts, and the age of the last verified backup. The API includes `X-Request-ID` and logs production request method, route template, status, and duration. Record request IDs when investigating an incident.
- Before switching back to a previous web or API deployment, compare its expected API and Alembic revisions. Use the previous API image only when compatible with the current schema. For incompatible changes, pause writes and decide whether a reviewed forward migration or a coordinated database and photo restore is appropriate. Identify records accepted after the restore point and reconcile them before reopening trades.
- Re-run release smoke and verify a known order, inbox, and private photo after recovery. Record the restored revisions and any unresolved delivery or order state.
