import assert from "node:assert/strict";
import test from "node:test";
import { GET } from "../app/(index)/route.ts";

test("redirects the workspace root to Bangla on the current origin", () => {
  const response = GET();
  assert.equal(response.status, 307);
  assert.equal(response.headers.get("Location"), "/bn");
});
