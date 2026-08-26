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

async function auditAccessibility(page) {
  return page.evaluate(() => {
    const visible = (element) => {
      const style = getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
    };
    const accessibleName = (element) => {
      const labelledBy = element.getAttribute("aria-labelledby");
      if (labelledBy) {
        const label = labelledBy.split(/\s+/).map((id) => document.getElementById(id)?.textContent || "").join(" ").trim();
        if (label) return label;
      }
      const ariaLabel = element.getAttribute("aria-label")?.trim();
      if (ariaLabel) return ariaLabel;
      const labels = [...(element.labels || [])].map((label) => label.textContent || "").join(" ").trim();
      if (labels) return labels;
      if (element instanceof HTMLImageElement && element.alt.trim()) return element.alt.trim();
      return (element.textContent || element.getAttribute("title") || "").trim();
    };

    const interactive = [...document.querySelectorAll(
      'button, a[href], input:not([type="hidden"]), select, textarea, summary, [role="button"], [role="radio"]',
    )].filter(visible);
    const unnamed = interactive.filter((element) => !accessibleName(element));
    const undersized = interactive.filter((element) => {
      if (element instanceof HTMLAnchorElement && getComputedStyle(element).display === "inline") return false;
      const rect = element.getBoundingClientRect();
      return rect.width < 24 || rect.height < 24;
    });
    const positiveTabIndex = [...document.querySelectorAll("[tabindex]")]
      .filter((element) => Number(element.getAttribute("tabindex")) > 0);
    const hiddenFocusable = [...document.querySelectorAll('[aria-hidden="true"]')]
      .flatMap((root) => [root, ...root.querySelectorAll("*")])
      .filter((element) => visible(element) && element.tabIndex >= 0);
    const ids = [...document.querySelectorAll("[id]")].map((element) => element.id);
    const duplicateIds = ids.filter((id, index) => ids.indexOf(id) !== index);
    const invalidReferences = [...document.querySelectorAll("[aria-labelledby], [aria-describedby], [aria-controls]")]
      .flatMap((element) => ["aria-labelledby", "aria-describedby", "aria-controls"].flatMap((attribute) => {
        const value = element.getAttribute(attribute);
        if (!value) return [];
        return value.split(/\s+/).filter((id) => !document.getElementById(id)).map((id) => `${attribute}:${id}`);
      }));

    return {
      semanticLandmarks: document.querySelectorAll("main").length === 1 && document.querySelectorAll("h1").length === 1,
      namedInteractiveControls: unnamed.map((element) => element.outerHTML.slice(0, 160)),
      minimumControlTargets: undersized.map((element) => {
        const rect = element.getBoundingClientRect();
        return `${accessibleName(element)}:${rect.width.toFixed(1)}x${rect.height.toFixed(1)}`;
      }),
      noPositiveTabIndex: positiveTabIndex.map((element) => element.outerHTML.slice(0, 160)),
      noAriaHiddenFocus: hiddenFocusable.map((element) => element.outerHTML.slice(0, 160)),
      uniqueIds: [...new Set(duplicateIds)],
      validAriaReferences: invalidReferences,
    };
  });
}

try {
  for (const [name, width, height] of [
    ["desktop", 1453, 726],
    ["mobile", 390, 844],
    ["reflow320", 320, 844],
  ]) {
    const context = await browser.newContext({
      viewport: { width, height },
      permissions: ["clipboard-read", "clipboard-write"],
      reducedMotion: "reduce",
    });
    const page = await context.newPage();
    page.setDefaultTimeout(70_000);
    await page.addInitScript(() => {
      window.__driftlineScrollBehaviors = [];
      const originalScrollIntoView = Element.prototype.scrollIntoView;
      Element.prototype.scrollIntoView = function scrollIntoView(options) {
        window.__driftlineScrollBehaviors.push(
          typeof options === "object" && options ? options.behavior || "auto" : "auto",
        );
        return originalScrollIntoView.call(this, options);
      };
    });
    const consoleErrors = [];
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    });

    await page.goto(baseUrl.href, { waitUntil: "networkidle" });
    const mainAriaSnapshot = await page.getByRole("main").ariaSnapshot();
    const skipLink = page.getByRole("link", { name: "Skip to main content" });
    await skipLink.focus();
    await page.waitForFunction(() => {
      const element = document.activeElement;
      if (!(element instanceof HTMLAnchorElement) || element.textContent?.trim() !== "Skip to main content") return false;
      const rect = element.getBoundingClientRect();
      return rect.top >= 0 && rect.left >= 0 && rect.bottom <= innerHeight && rect.right <= innerWidth;
    });
    const skipLinkVisibleOnFocus = await skipLink.evaluate((element) => {
      const rect = element.getBoundingClientRect();
      return rect.top >= 0 && rect.left >= 0 && rect.bottom <= innerHeight && rect.right <= innerWidth;
    });
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
    const intakeResponsePromise = page.waitForResponse((response) => (
      response.request().method() === "POST"
      && new URL(response.url()).pathname === "/api/decision-twin/intake"
    ));
    await page.getByRole("button", { name: "Build my decision brief" }).click();
    const intakeResponse = await intakeResponsePromise;
    if (!intakeResponse.ok()) {
      throw new Error(`Decision intake failed for ${name}: HTTP ${intakeResponse.status()} ${await intakeResponse.text()}`);
    }
    await page.getByText(/PM-provided context · unverified/).first().waitFor();
    const intakeResultFocused = await page.locator("#decision-room-title").evaluate((element) => document.activeElement === element);

    const selectedRadio = page.getByRole("radio", { checked: true });
    const originalRadioName = await selectedRadio.innerText();
    await selectedRadio.focus();
    await page.keyboard.press("ArrowRight");
    const nextRadio = page.getByRole("radio", { checked: true });
    const nextRadioName = await nextRadio.innerText();
    const arrowMovedFocus = await nextRadio.evaluate((element) => document.activeElement === element);
    await page.keyboard.press("ArrowLeft");
    const restoredRadio = page.getByRole("radio", { checked: true });
    const keyboardRadioRoving = nextRadioName !== originalRadioName
      && arrowMovedFocus
      && (await restoredRadio.innerText()) === originalRadioName
      && (await restoredRadio.evaluate((element) => document.activeElement === element));

    const decisionUrl = page.url();
    const caseId = new URL(decisionUrl).searchParams.get("decision");
    const decisionTitle = await page.locator("#decision-room-title").innerText();
    const decisionQuestion = await page.locator("#decision-room-title + p").innerText();
    await page.getByRole("button", { name: "Copy decision brief" }).click();
    await page.getByRole("button", { name: "Copied" }).waitFor();
    await page.getByLabel("Human approver").fill("Independent PM");
    const approve = page.getByRole("button", { name: /^Approve:/ });
    const approvalLabel = await approve.innerText();
    await approve.focus();
    await page.keyboard.press("Enter");
    await page.getByText(/Attach the real measurement when the review window closes/).waitFor();
    await page.getByText(/Measurement opens/).waitFor();
    const approvalResultFocused = await page.locator("#learning-receipt-title").evaluate((element) => document.activeElement === element);
    const body = await page.locator("body").innerText();
    const bodyLower = body.toLowerCase();

    const controlPlane = page.locator("details.legacy-workflow-details");
    if (!(await controlPlane.evaluate((element) => element.open))) {
      await controlPlane.locator("summary").click();
    }
    const evidenceTrigger = page.getByRole("button", { name: "View source evidence" });
    await evidenceTrigger.focus();
    await page.keyboard.press("Enter");
    const evidenceDialog = page.getByRole("dialog", { name: "Source evidence" });
    await evidenceDialog.waitFor();
    const dialogAriaSnapshot = await evidenceDialog.ariaSnapshot();
    const modalInitialFocus = await evidenceDialog.evaluate((element) => (
      element.contains(document.activeElement)
      && document.activeElement?.getAttribute("aria-label") === "Close source evidence"
    ));
    const backgroundInert = await page.evaluate(() => [
      document.querySelector(".skip-link"),
      document.querySelector(".sidebar"),
      document.getElementById("main-content"),
    ].every((element) => element?.inert));
    const dialogFitsViewport = await evidenceDialog.evaluate((element) => {
      const rect = element.getBoundingClientRect();
      return rect.top >= 0 && rect.left >= 0 && rect.right <= innerWidth && rect.bottom <= innerHeight;
    });
    await page.keyboard.press("Shift+Tab");
    const reverseTabTrapped = await evidenceDialog.evaluate((element) => element.contains(document.activeElement));
    await page.keyboard.press("Escape");
    await evidenceDialog.waitFor({ state: "detached" });
    const modalFocusRestored = await evidenceTrigger.evaluate((element) => document.activeElement === element);
    const backgroundRestored = await page.evaluate(() => [
      document.querySelector(".skip-link"),
      document.querySelector(".sidebar"),
      document.getElementById("main-content"),
    ].every((element) => element && !element.inert));

    await page.getByRole("button", { name: "Copy view-only link" }).click();
    await page.getByRole("button", { name: "Copied view-only link" }).waitFor();
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
    const sharedMutation = await restored.request.post(
      new URL(`/api/decision-twin/${caseId}/outcomes/measured`, baseUrl).href,
      {
        data: {
          expected_generation: 1,
          measurement_id: `browser-shared-${name}`,
          primary_value: 46,
          risk_value: 4,
          source_label: "Shared browser audit",
        },
      },
    );
    const sharedMutationBody = await sharedMutation.json();
    const accessibility = await auditAccessibility(page);

    results[name] = {
      approvalLabel,
      clearApprovalLabel: approvalLabel === "Approve: Run a bounded test",
      conciseDistinctTitle: decisionTitle === "Mid-market admins decision review" && decisionTitle !== decisionQuestion.replace(/[ ?.]+$/, ""),
      opaqueCase: Boolean(caseId && /^[a-z0-9][a-z0-9_-]{2,100}$/.test(caseId)),
      pmProvidedVisible: body.includes("PM-provided context · unverified"),
      internalActionVisible: body.includes("Bounded internal action executed"),
      namedApproverVisible: body.includes("Named human approval") && body.includes("Independent PM"),
      copiedReturnLinkMatches: copiedReturnLink === decisionUrl,
      sharedLinkReadOnly: restoredLower.includes("read-only shared view")
        && sharedMutation.status() === 403
        && sharedMutationBody.detail === "This shared decision link is read-only."
        && (await restored.getByLabel("Human approver").count()) === 0,
      decisionStateOnly: bodyLower.includes("decision state only"),
      externalWritesNone: bodyLower.includes("external writes") && bodyLower.includes("none"),
      windowLocked: body.includes("Driftline will reject early measurements at the API boundary"),
      earlyMeasurementBlocked: early.status() === 409 && String(earlyBody.detail).startsWith("Measurement window opens at "),
      freshContextRestored: restoredLower.includes("workflow completion rate") && restoredLower.includes("measurement opens") && restoredLower.includes("bounded internal action executed") && restoredLower.includes("named human approval") && restoredLower.includes("independent pm"),
      skipLinkVisibleOnFocus,
      keyboardRadioRoving,
      keyboardApprovalCompleted: body.includes("Named human approval") && body.includes("Independent PM"),
      intakeResultFocused,
      approvalResultFocused,
      modalInitialFocus,
      modalBackgroundInert: backgroundInert,
      modalReverseTabTrapped: reverseTabTrapped,
      modalFocusRestored,
      modalBackgroundRestored: backgroundRestored,
      modalFitsViewport: dialogFitsViewport,
      reducedMotionActive: await page.evaluate(() => matchMedia("(prefers-reduced-motion: reduce)").matches),
      noSmoothScrollUnderReducedMotion: await page.evaluate(() => window.__driftlineScrollBehaviors.every((behavior) => behavior !== "smooth")),
      mainAccessibilityTree: mainAriaSnapshot.includes('heading "Product decisions, with evidence" [level=1]')
        && mainAriaSnapshot.includes('region "Turn conflicting evidence into a decision your team can defend."'),
      dialogAccessibilityTree: dialogAriaSnapshot.includes('dialog "Source evidence"')
        && dialogAriaSnapshot.includes('button "Close source evidence"')
        && dialogAriaSnapshot.includes('button "Close evidence"'),
      semanticLandmarks: accessibility.semanticLandmarks,
      namedInteractiveControls: accessibility.namedInteractiveControls.length === 0,
      minimumControlTargets: accessibility.minimumControlTargets.length === 0,
      noPositiveTabIndex: accessibility.noPositiveTabIndex.length === 0,
      noAriaHiddenFocus: accessibility.noAriaHiddenFocus.length === 0,
      uniqueIds: accessibility.uniqueIds.length === 0,
      validAriaReferences: accessibility.validAriaReferences.length === 0,
      accessibilityFindings: accessibility,
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
    .filter(([key, value]) => !["approvalLabel", "accessibilityFindings"].includes(key) && value !== true)
    .map(([key, value]) => `${viewport}.${key}=${JSON.stringify(value)}`),
);
console.log(JSON.stringify({ results, failures }, null, 2));
if (failures.length > 0) process.exitCode = 1;
