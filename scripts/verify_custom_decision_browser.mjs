#!/usr/bin/env node

import { createRequire } from "node:module";
import { resolve } from "node:path";

const baseUrl = new URL(process.env.CUSTOM_BROWSER_BASE_URL || "http://127.0.0.1:5173/");
const loopbackHosts = new Set(["127.0.0.1", "localhost", "::1", "[::1]"]);
if (!loopbackHosts.has(baseUrl.hostname) && process.env.CUSTOM_BROWSER_ALLOW_REMOTE !== "true") {
  throw new Error("Custom-decision browser verification is loopback-only unless CUSTOM_BROWSER_ALLOW_REMOTE=true is explicitly set.");
}

function loadPlaywright() {
  const attempts = [];
  const roots = [
    process.env.PLAYWRIGHT_MODULE_ROOT,
    resolve("frontend"),
  ].filter(Boolean);
  for (const root of roots) {
    try {
      return createRequire(resolve(root, "package.json"))("playwright");
    } catch (error) {
      attempts.push(`${root}: ${error.code || error.message}`);
    }
  }
  throw new Error(
    "Playwright is required for this optional browser gate. Set PLAYWRIGHT_MODULE_ROOT " +
    `to a package root that contains playwright. Attempts: ${attempts.join("; ")}`,
  );
}

const { chromium } = loadPlaywright();
const browser = await chromium.launch({ headless: true });
const results = {};

try {
  for (const [name, width, height] of [
    ["desktop", 1453, 726],
    ["mobile", 390, 844],
  ]) {
    const context = await browser.newContext({
      viewport: { width, height },
      permissions: ["clipboard-read", "clipboard-write"],
    });
    const page = await context.newPage();
    page.setDefaultTimeout(70_000);
    const consoleErrors = [];
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    });

    await page.goto(baseUrl.href, { waitUntil: "networkidle" });
    await page.getByRole("button", { name: "Use my decision" }).click();
    await page.getByLabel("Decision question").fill("Should we expand the beta to every mid-market account next month?");
    await page.getByLabel("Current commitment").fill("Launch to every mid-market account on September 15.");
    await page.getByLabel("Why now").fill("Sales committed the date and the allocation decision is due Friday.");
    await page.getByLabel("Strongest signal in favor").fill("Beta users complete the core workflow faster and renewal intent improved.");
    await page.getByLabel("Strongest risk signal").fill("Admins report permission confusion and support volume is rising.");
    await page.getByRole("button", { name: "Continue to operating contract" }).click();
    await page.getByLabel("Affected segment").fill("Mid-market admins");
    await page.getByLabel("Action owner").fill("Taylor, Product Lead");
    await page.getByLabel("Primary outcome metric").fill("Workflow completion rate");
    await page.getByLabel("Risk guardrail metric").fill("Failed workflow rate");
    await page.getByLabel("Unit").fill("%");
    await page.getByLabel("Review window").selectOption("3");
    await page.getByLabel("Outcome baseline").fill("38");
    await page.getByLabel("Success threshold", { exact: true }).fill("45");
    await page.getByLabel("Risk baseline").fill("3");
    await page.getByLabel("Stop threshold", { exact: true }).fill("8");
    await page.getByRole("button", { name: "Build my decision brief" }).click();
    await page.getByText(/PM-provided context · unverified/).first().waitFor();

    const decisionUrl = page.url();
    const caseId = new URL(decisionUrl).searchParams.get("decision");
    const decisionTitle = await page.locator("#decision-room-title").innerText();
    const decisionQuestion = await page.locator("#decision-room-title + p").innerText();
    await page.getByRole("button", { name: "Copy decision brief" }).click();
    await page.getByRole("button", { name: "Copied" }).waitFor();
    await page.getByLabel("Human approver").fill("Independent PM");
    const approve = page.getByRole("button", { name: /^Approve / });
    const approvalLabel = await approve.innerText();
    await approve.click();
    await page.getByText(/Attach the real measurement when the review window closes/).waitFor();
    await page.getByText(/Measurement opens/).waitFor();
    const body = await page.locator("body").innerText();
    const bodyLower = body.toLowerCase();

    await page.getByRole("button", { name: "Copy return link" }).click();
    await page.getByRole("button", { name: "Copied return link" }).waitFor();
    const copiedReturnLink = await page.evaluate(() => navigator.clipboard.readText());
    const early = await page.request.post(
      new URL(`/api/decision-twin/${caseId}/outcomes/measured`, baseUrl).href,
      {
        data: {
          expected_generation: 1,
          measurement_id: `browser-early-${name}`,
          primary_value: 46,
          risk_value: 4,
          source_label: "Browser audit aggregate",
        },
      },
    );
    const earlyBody = await early.json();

    const restoreContext = await browser.newContext({ viewport: { width, height } });
    const restored = await restoreContext.newPage();
    const restoredErrors = [];
    restored.on("console", (message) => {
      if (message.type() === "error") restoredErrors.push(message.text());
    });
    await restored.goto(decisionUrl, { waitUntil: "networkidle" });
    await restored.getByText(/Attach the real measurement when the review window closes/).waitFor();
    const restoredLower = (await restored.locator("body").innerText()).toLowerCase();

    results[name] = {
      approvalLabel,
      conciseDistinctTitle: decisionTitle === "Mid-market admins decision review" && decisionTitle !== decisionQuestion.replace(/[ ?.]+$/, ""),
      opaqueCase: Boolean(caseId && /^[a-z0-9][a-z0-9_-]{2,100}$/.test(caseId)),
      pmProvidedVisible: body.includes("PM-provided context · unverified"),
      internalActionVisible: body.includes("Bounded internal action executed"),
      namedApproverVisible: body.includes("Named human approval") && body.includes("Independent PM"),
      copiedReturnLinkMatches: copiedReturnLink === decisionUrl,
      decisionStateOnly: bodyLower.includes("decision state only"),
      externalWritesNone: bodyLower.includes("external writes") && bodyLower.includes("none"),
      windowLocked: body.includes("Driftline will reject early measurements at the API boundary"),
      earlyMeasurementBlocked: early.status() === 409 && String(earlyBody.detail).startsWith("Measurement window opens at "),
      freshContextRestored: restoredLower.includes("workflow completion rate") && restoredLower.includes("measurement opens") && restoredLower.includes("bounded internal action executed") && restoredLower.includes("named human approval") && restoredLower.includes("independent pm"),
      noConsoleErrors: consoleErrors.length === 0 && restoredErrors.length === 0,
      noHorizontalOverflow: await page.evaluate(() => document.documentElement.scrollWidth === innerWidth),
    };

    await restoreContext.close();
    await context.close();
  }
} finally {
  await browser.close();
}

const failures = Object.entries(results).flatMap(([viewport, checks]) =>
  Object.entries(checks)
    .filter(([key, value]) => key !== "approvalLabel" && value !== true)
    .map(([key, value]) => `${viewport}.${key}=${JSON.stringify(value)}`),
);
console.log(JSON.stringify({ results, failures }, null, 2));
if (failures.length > 0) process.exitCode = 1;
