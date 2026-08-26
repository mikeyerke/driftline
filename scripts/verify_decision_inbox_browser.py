"""Exercise the local multi-decision inbox through real browser interactions."""

from __future__ import annotations

import os
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

BASE_URL = os.environ.get("DRIFTLINE_BROWSER_BASE_URL", "http://127.0.0.1:15173")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def assert_no_overflow(page: Page) -> None:
    overflow = page.evaluate(
        """() => ({
          viewport: document.documentElement.clientWidth,
          page: document.documentElement.scrollWidth,
          inboxClient: document.querySelector('#inbox-section')?.clientWidth || 0,
          inboxScroll: document.querySelector('#inbox-section')?.scrollWidth || 0,
        })"""
    )
    assert overflow["page"] <= overflow["viewport"] + 1, overflow
    assert overflow["inboxScroll"] <= overflow["inboxClient"] + 1, overflow


def wait_for_inbox(page: Page) -> None:
    page.locator("#decision-inbox-title").wait_for()
    page.wait_for_load_state("networkidle")


def main() -> None:
    output = Path("/tmp/driftline-decision-inbox-proof")
    output.mkdir(exist_ok=True)
    console_errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=CHROME)
        context = browser.new_context(viewport={"width": 1453, "height": 726})
        page = context.new_page()
        page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
        page.goto(BASE_URL)
        wait_for_inbox(page)
        assert page.get_by_text("Your decision portfolio is quiet").is_visible()

        for source_id in ("competitor/pricing", "competitor/pricing", "competitor/offerings"):
            response = page.request.post(f"{BASE_URL}/api/workflows/demo?source_id={source_id}")
            assert response.ok, (response.status, response.text())

        page.get_by_role("button", name="Refresh").click()
        page.get_by_text("Needs your decision", exact=True).wait_for()
        inbox_text = page.locator("#inbox-section").inner_text()
        inbox_text_normalized = inbox_text.casefold()
        assert "2\nNeed attention" in inbox_text
        assert "1\nRepeats collapsed" in inbox_text
        assert "Linked to 1 other decision" in inbox_text
        assert "prepared for you" in inbox_text_normalized
        assert "reserved for you" in inbox_text_normalized
        assert "portfolio intelligence" in inbox_text_normalized
        assert "repeated observations consolidated" in inbox_text_normalized
        assert page.get_by_role("button", name="Review decision").count() == 2
        assert_no_overflow(page)
        page.screenshot(path=str(output / "desktop-inbox.png"), full_page=True)

        page.get_by_role("button", name="Review decision").first.click()
        page.locator("#overview-section").wait_for()
        assert "Decision thread restored" in page.locator(".scan-message").get_attribute("title")
        assert_no_overflow(page)
        context.close()

        for width, height, label in ((390, 844, "mobile-390"), (320, 844, "mobile-320")):
            mobile = browser.new_context(viewport={"width": width, "height": height})
            mobile_page = mobile.new_page()
            mobile_page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            mobile_page.goto(BASE_URL)
            wait_for_inbox(mobile_page)
            mobile_page.get_by_text("Needs your decision", exact=True).wait_for()
            assert mobile_page.get_by_role("button", name="Review decision").count() == 2
            assert_no_overflow(mobile_page)
            mobile_page.screenshot(path=str(output / f"{label}.png"), full_page=True)
            mobile.close()

        browser.close()
    assert console_errors == [], console_errors
    print(f"Decision Inbox browser verification PASS · screenshots: {output}")


if __name__ == "__main__":
    main()
