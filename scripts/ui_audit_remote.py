from pathlib import Path

from playwright.sync_api import sync_playwright


URL = "https://driftline-xvxczqg62a-uc.a.run.app/"
OUT = Path("/tmp/driftline-ui-audit")
OUT.mkdir(parents=True, exist_ok=True)


def audit_view(page, name: str) -> dict[str, object]:
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
    metrics = page.evaluate(
        """() => ({
          viewportWidth: window.innerWidth,
          documentWidth: document.documentElement.scrollWidth,
          bodyWidth: document.body.scrollWidth,
          horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
          headings: [...document.querySelectorAll('h1,h2')].map((node) => node.textContent.trim()).slice(0, 30),
          buttons: [...document.querySelectorAll('button')].map((node) => node.textContent.trim()).filter(Boolean).slice(0, 30),
          dialogs: document.querySelectorAll('[role="dialog"]').length,
        })"""
    )
    return metrics


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
    console_errors: list[str] = []
    page_errors: list[str] = []
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_load_state("networkidle", timeout=60_000)
    page.wait_for_timeout(1500)
    desktop = audit_view(page, "desktop-initial")
    page.get_by_role("button", name="View source evidence").first.click()
    page.get_by_role("dialog").wait_for()
    evidence_open = audit_view(page, "desktop-evidence")
    page.get_by_role("button", name="Close source evidence").click()

    run = page.get_by_role("button", name="Run scan")
    run.click()
    page.get_by_text("Scan complete", exact=False).wait_for(timeout=180_000)
    page.wait_for_timeout(500)
    workflow = audit_view(page, "desktop-pending-approval")
    page.get_by_role("button", name="Open evidence").first.click()
    page.get_by_role("dialog").wait_for()
    pending_evidence = audit_view(page, "desktop-pending-evidence")
    page.get_by_role("button", name="Close source evidence").click()

    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(500)
    mobile = audit_view(page, "mobile-pending-approval")
    print({
        "desktop": desktop,
        "evidence_open": evidence_open,
        "workflow": workflow,
        "pending_evidence": pending_evidence,
        "mobile": mobile,
        "console_errors": console_errors,
        "page_errors": page_errors,
    })
    browser.close()
