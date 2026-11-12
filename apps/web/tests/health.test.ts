import assert from "node:assert/strict";
import test from "node:test";
import { readHealth } from "../lib/health.ts";

const base = "http://localhost:8000";

test("reads current readiness from the configured API", async () => {
  const health = await readHealth(base, async (url, options) => {
    assert.equal(String(url), `${base}/health/ready`);
    assert.equal(options?.cache, "no-store");
    return Response.json({ database: "ready" });
  });
  assert.deepEqual(health, { api: "online", database: "ready" });
});

test("distinguishes a reachable API from an unavailable database", async () => {
  const health = await readHealth(base, async () =>
    Response.json({ database: "migration_required" }, { status: 503 }),
  );
  assert.deepEqual(health, { api: "online", database: "migration_required" });
});

test("shows an unavailable API when the request fails or its contract is invalid", async () => {
  const expected = { api: "offline", database: "unknown" };
  assert.deepEqual(
    await readHealth(base, async () => {
      throw new TypeError("network error");
    }),
    expected,
  );
  assert.deepEqual(
    await readHealth(
      base,
      async () => new Response("Bad Gateway", { status: 503 }),
    ),
    expected,
  );
  assert.deepEqual(
    await readHealth(base, async () =>
      Response.json({ database: "unconfigured" }),
    ),
    expected,
  );
});
