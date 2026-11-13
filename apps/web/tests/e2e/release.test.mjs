import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import AxeBuilder from "@axe-core/playwright";
import { chromium } from "playwright-core";

const web = process.env.E2E_WEB_ORIGIN ?? "http://127.0.0.1:3000";
const api = process.env.E2E_API_ORIGIN ?? "http://127.0.0.1:8000";
const base = `${web}/en/workspace`;

async function post(route, data, token) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${api}/v1/${route}`, {
    method: "POST",
    headers,
    body: JSON.stringify(data),
  });
  assert.ok(response.ok, `${route}: ${response.status}`);
  return response.json();
}

async function signIn(browser, identity, width) {
  const context = await browser.newContext({
    viewport: { width, height: 850 },
  });
  const page = await context.newPage();
  await page.goto(base);
  await page.getByLabel("Account", { exact: true }).selectOption(identity);
  await page.getByRole("button", { name: "Open workspace" }).click();
  await page.getByRole("heading", { name: "Workspace", exact: true }).waitFor();
  return page;
}

async function checkScreen(page, file) {
  assert.ok(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  );
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  assert.deepEqual(
    result.violations.map(({ id, nodes }) => [
      id,
      nodes.map(({ target }) => target),
    ]),
    [],
  );
  const output = process.env.RELEASE_SCREENSHOT_DIR;
  if (output && file) {
    await mkdir(output, { recursive: true });
    await page.screenshot({
      path: path.join(output, file),
      fullPage: file === "completion-settlement-360.png",
    });
  }
}

test(
  "alerts, operations and offline states work across locales and viewport sizes",
  { timeout: 120_000 },
  async () => {
    const browser = await chromium.launch({
      channel: process.env.PLAYWRIGHT_CHANNEL,
    });
    try {
      const farmer = await signIn(browser, "farmer", 360);
      const admin = await signIn(browser, "admin", 1440);
      const buyer = await signIn(browser, "buyer", 1280);
      const { token: farmerToken } = await post("auth/demo", {
        identity: "farmer",
      });
      const { token: buyerToken } = await post("auth/demo", {
        identity: "buyer",
      });
      const day = new Intl.DateTimeFormat("sv-SE", {
        timeZone: "Asia/Dhaka",
      }).format(new Date());
      const label = `Release lot ${randomUUID().slice(0, 8)}`;
      const lot = await post(
        "lots",
        {
          label,
          district: "Pabna",
          variety: "Taherpuri",
          storage_type: "Ventilated shed",
          harvest_on: day,
          stored_on: day,
          grade: "A",
          listed: true,
          quantity: "1000",
          unit: "kg",
          request_key: randomUUID(),
        },
        farmerToken,
      );
      const offer = await post(
        "offers",
        {
          lot_id: lot.id,
          quantity_kg: "200",
          price_bdt_kg: "45.55",
          delivery_district: "Dhaka",
          transport: "buyer",
          request_key: randomUUID(),
        },
        buyerToken,
      );
      await farmer
        .getByRole("navigation", { name: "Workspace navigation" })
        .getByRole("link", { name: "Alerts" })
        .click();
      await farmer.getByRole("heading", { name: "Alerts" }).waitFor();
      const alert = farmer
        .locator("li")
        .filter({ has: farmer.locator(`a[href$="/offers/${offer.id}"]`) });
      await alert.getByRole("link", { name: "New offer received" }).waitFor();
      await checkScreen(farmer, "release-alerts-360.png");
      await alert
        .getByRole("button", { name: "Mark read", exact: true })
        .click();
      await alert.getByText("Read", { exact: true }).waitFor();
      await farmer.context().setOffline(true);
      const offline = farmer
        .getByRole("status")
        .filter({ hasText: "You are offline." });
      await offline.waitFor();
      await farmer.context().setOffline(false);
      await offline.waitFor({ state: "hidden" });
      await farmer.goto(`${base}/operations`);
      await farmer
        .getByRole("alert")
        .filter({ hasText: "Your role does not allow this action." })
        .waitFor();

      const { order_id: order } = await post(
        `offers/${offer.id}/respond`,
        {
          version: offer.version,
          action: "accept",
          confirm: true,
          request_key: randomUUID(),
        },
        farmerToken,
      );
      for (const [action, token] of [
        ["dispatch", farmerToken],
        ["dispute", buyerToken],
      ]) {
        await post(
          `orders/${order}/transition`,
          { action, confirm: true, request_key: randomUUID() },
          token,
        );
      }

      await admin.goto(`${base}/operations`);
      await admin.getByRole("heading", { name: "Operations" }).waitFor();
      await admin
        .getByRole("link", { name: "Accounts awaiting verification" })
        .waitFor();
      await checkScreen(admin, "release-operations-1440.png");
      const sections = admin.getByRole("navigation", {
        name: "Operations sections",
      });
      await sections.getByRole("link", { name: "Disputes" }).click();
      const dispute = admin
        .locator("li")
        .filter({ has: admin.locator(`a[href$="/orders/${order}"]`) });
      await dispute
        .locator("summary")
        .filter({ hasText: "Resolve dispute" })
        .click();
      await dispute
        .getByLabel("Operator note")
        .fill("Fictional release test resolution");
      await dispute.getByRole("checkbox").check();
      await dispute.getByRole("button", { name: "Save resolution" }).click();
      await dispute.waitFor({ state: "hidden" });
      await sections.getByRole("link", { name: "Audit" }).click();
      await admin.getByLabel("Event prefix").fill("order.");
      await admin.getByLabel("Record ID").fill(order);
      await admin.getByRole("button", { name: "Search events" }).click();
      await admin
        .getByText("order.dispute_resolved", { exact: true })
        .waitFor();
      assert.equal(
        await admin.getByText("Fictional release test resolution").count(),
        0,
      );
      await admin.setViewportSize({ width: 768, height: 950 });
      await admin.getByRole("link", { name: "বাংলা" }).click();
      await admin.getByRole("heading", { name: "নিরীক্ষার ইতিহাস" }).waitFor();
      assert.equal(await admin.locator("html").getAttribute("lang"), "bn");
      assert.equal(new URL(admin.url()).searchParams.get("resource_id"), order);
      await checkScreen(admin, "release-audit-bn-768.png");

      await buyer.goto(`${base}/orders/${order}`);
      const receive = buyer
        .locator("details")
        .filter({ hasText: "Confirm receipt" });
      await receive.locator("summary").click();
      await receive.getByRole("checkbox").check();
      await receive.getByRole("button", { name: "Confirm receipt" }).click();
      const report = buyer
        .locator("details")
        .filter({ hasText: "Report payment" });
      await report.locator("summary").click();
      const reference = `FIXTURE-${randomUUID().slice(0, 8)}`;
      await report.getByLabel("Transaction reference").fill(reference);
      await report.getByRole("checkbox").check();
      await report
        .getByRole("button", { name: "Submit payment report" })
        .click();
      await buyer.getByText("Payment reported", { exact: true }).waitFor();
      await admin.goto(`${base}/operations?view=settlements`);
      await admin
        .getByRole("heading", { name: "Review payment reports" })
        .waitFor();
      const entry = admin.locator("li").filter({ hasText: reference });
      await entry.locator("summary").click();
      await entry.getByLabel("Review decision").selectOption("verified");
      await entry
        .getByLabel("Independent evidence reference")
        .fill("FIXTURE-INDEPENDENT-CHECK");
      await entry.getByRole("checkbox").check();
      await entry.getByRole("button", { name: "Save payment review" }).click();
      await entry.waitFor({ state: "hidden" });
      await farmer.goto(`${base}/orders/${order}`);
      await farmer.getByText("Payment verified", { exact: true }).waitFor();
      await checkScreen(farmer, "completion-settlement-360.png");

      const agent = await signIn(browser, "agent", 768);
      const accessId = await agent
        .locator("p")
        .filter({ hasText: "Agent access ID to share with a farmer" })
        .locator("code")
        .textContent();
      const secondFarmer = await signIn(browser, "farmer-two", 390);
      await secondFarmer.goto(`${base}/agents`);
      await secondFarmer.getByLabel("Agent access ID").fill(accessId);
      await secondFarmer
        .getByLabel("I authorize this agent to access and assist with my lots.")
        .check();
      await secondFarmer.getByRole("button", { name: "Grant access" }).click();
      await secondFarmer.getByText(/Jalil/).waitFor();
      await agent.goto(`${base}/stock`);
      const registration = agent
        .locator("details")
        .filter({ hasText: "Register a lot" });
      await registration.locator("summary").click();
      await registration.getByLabel("Farmer who owns this lot").selectOption({
        label: await registration
          .getByRole("option", { name: /Salma/ })
          .textContent(),
      });
      const newLabel = `Delegated ${randomUUID().slice(0, 8)}`;
      await registration.getByLabel("Lot name").fill(newLabel);
      await registration.getByLabel("Variety").fill("Taherpuri");
      await registration.getByLabel("Storage type").fill("Ventilated shed");
      await registration.getByLabel("Quantity", { exact: true }).fill("100");
      await registration.getByRole("button", { name: "Save lot" }).click();
      await agent.getByRole("heading", { name: newLabel }).waitFor();
      const delegatedLot = new URL(agent.url()).pathname;
      await secondFarmer.goto(`${web}${delegatedLot}`);
      await secondFarmer.getByRole("heading", { name: newLabel }).waitFor();
      await secondFarmer.goto(`${web}${delegatedLot}/inspections`);
      const help = secondFarmer
        .locator("details")
        .filter({ hasText: "Request inspection help" });
      await help.locator("summary").click();
      const note = `Please inspect ${newLabel}`;
      await help.getByLabel("What help do you need?").fill(note);
      await help.getByRole("button", { name: "Send request" }).click();
      await secondFarmer.getByText(note, { exact: true }).waitFor();
      await agent.goto(`${base}/help`);
      const request = agent.locator("li").filter({ hasText: note });
      await request.getByRole("button", { name: "Mark resolved" }).click();
      await request.getByText("Resolved", { exact: true }).waitFor();
      await secondFarmer.goto(`${base}/agents`);
      const revoke = secondFarmer
        .locator("details")
        .filter({ hasText: "Revoke access" });
      await revoke.locator("summary").click();
      await revoke.getByRole("checkbox").check();
      await revoke.getByRole("button", { name: "Confirm revocation" }).click();
      await secondFarmer.getByText("No active grants on this page.").waitFor();
      await agent.goto(`${web}${delegatedLot}`);
      await agent.getByText("This record was not found.").waitFor();
    } finally {
      await browser.close();
    }
  },
);
