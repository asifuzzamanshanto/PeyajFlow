import assert from "node:assert/strict";

function origin(name, fallback) {
  const url = new URL(process.env[name] ?? fallback);
  const loopback = ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname);
  assert.ok(
    (url.protocol === "https:" || (loopback && url.protocol === "http:")) &&
      !url.username &&
      !url.password &&
      url.pathname === "/" &&
      !url.search &&
      !url.hash,
    `${name} requires an HTTPS origin or HTTP loopback.`,
  );
  return url;
}

const api = origin("SMOKE_API_ORIGIN", "http://127.0.0.1:8000");
const web = origin("SMOKE_WEB_ORIGIN", "http://127.0.0.1:3000");
const get = (host, path, init) =>
  fetch(new URL(path, host), {
    ...init,
    redirect: "manual",
    signal: AbortSignal.timeout(10_000),
  });

const [live, ready, root, workspace] = await Promise.all([
  get(api, "/health/live"),
  get(api, "/health/ready"),
  get(web, "/"),
  get(web, "/en/workspace"),
]);
assert.equal(live.status, 200, "API liveness");
assert.equal(ready.status, 200, "API readiness");
assert.equal((await ready.json()).database, "ready");
assert.match(ready.headers.get("x-request-id") ?? "", /^[a-f0-9]{32}$/);
assert.equal(root.status, 307, "Web locale redirect");
assert.equal(new URL(root.headers.get("location"), web).pathname, "/bn");
assert.equal(workspace.status, 200, "Sign-in page");
assert.equal(workspace.headers.get("x-frame-options"), "DENY");
assert.match(await workspace.text(), /Sign in/);
console.log(
  "API ready and workspace reachable with expected response headers.",
);

if (process.env.SMOKE_EXPECT_PRODUCTION === "1") {
  assert.equal(
    (await get(api, "/v1/auth/demo")).status,
    404,
    "Production demo is disabled",
  );
}

const user = process.env.SMOKE_USERNAME;
const password = process.env.SMOKE_PASSWORD;
const demo = process.env.SMOKE_DEMO_ID;
assert.equal(
  Boolean(user),
  Boolean(password),
  "Set both smoke account credentials.",
);
assert.ok(!(user && demo), "Select one smoke sign-in mode.");
if (user || demo) {
  const session = await get(api, `/v1/auth/${user ? "password" : "demo"}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(
      user ? { username: user, password } : { identity: demo },
    ),
  });
  assert.equal(session.status, 201, "Smoke sign-in");
  const { token } = await session.json();
  const headers = { Authorization: `Bearer ${token}` };
  try {
    assert.equal(
      (await get(api, "/v1/me", { headers })).status,
      200,
      "Signed-in profile",
    );
    assert.equal(
      (await get(api, "/v1/notifications", { headers })).status,
      200,
      "Signed-in inbox",
    );
  } finally {
    assert.equal(
      (await get(api, "/v1/auth/session", { method: "DELETE", headers }))
        .status,
      204,
      "Smoke sign-out",
    );
  }
  assert.equal(
    (await get(api, "/v1/me", { headers })).status,
    401,
    "Revoked smoke session",
  );
  console.log("Smoke session created, checked, and revoked.");
}
