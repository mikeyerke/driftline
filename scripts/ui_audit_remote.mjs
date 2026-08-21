import { mkdir } from "node:fs/promises";
import { chromium } from "/var/folders/5x/sfc5z0cn04g36dpqyzd4sghc0000gn/T/tmp.Knj1dS52MO/node_modules/playwright/index.mjs";

const url = "https://driftline-xvxczqg62a-uc.a.run.app/";
const out = "/tmp/driftline-ui-audit";
await mkdir(out, { recursive: true });
const browser = await chromium.launch({
  headless: true,
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
const consoleErrors = [];
const pageErrors = [];
page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });
page.on("pageerror", (error) => pageErrors.push(String(error)));
await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60_000 });
await page.waitForLoadState("networkidle", { timeout: 60_000 });
await page.waitForTimeout(1500);
const view = async (name) => {
  await page.screenshot({ path: `${out}/${name}.png`, fullPage: true });
  return page.evaluate(() => ({
    viewportWidth: window.innerWidth,
    documentWidth: document.documentElement.scrollWidth,
    bodyWidth: document.body.scrollWidth,
    horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
    headings: [...document.querySelectorAll("h1,h2")].map((node) => node.textContent.trim()).slice(0, 30),
    buttons: [...document.querySelectorAll("button")].map((node) => node.textContent.trim()).filter(Boolean).slice(0, 30),
    dialogs: document.querySelectorAll('[role="dialog"]').length,
  }));
};
const desktop = await view("desktop-initial");
await page.getByRole("button", { name: "View source evidence" }).first().click();
await page.getByRole("dialog").waitFor();
const evidenceOpen = await view("desktop-evidence");
await page.getByRole("button", { name: "Close source evidence" }).click();
await page.getByRole("button", { name: "Run scan" }).click();
await page.getByText("Scan complete", { exact: false }).waitFor({ timeout: 180_000 });
await page.waitForTimeout(500);
const workflow = await view("desktop-pending-approval");
await page.getByRole("button", { name: "Open evidence" }).first().click();
await page.getByRole("dialog").waitFor();
const pendingEvidence = await view("desktop-pending-evidence");
await page.getByRole("button", { name: "Close source evidence" }).click();
await page.setViewportSize({ width: 390, height: 844 });
await page.waitForTimeout(500);
const mobile = await view("mobile-pending-approval");
console.log(JSON.stringify({ desktop, evidenceOpen, workflow, pendingEvidence, mobile, consoleErrors, pageErrors }, null, 2));
await browser.close();
