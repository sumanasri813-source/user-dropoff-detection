import os

import pytest
import requests

playwright_sync_api = pytest.importorskip(
    "playwright.sync_api", reason="playwright is not installed in this CI job"
)
sync_playwright = playwright_sync_api.sync_playwright

BASE = os.getenv("E2E_BASE_URL", "http://localhost:8000")
ADMIN_USER = os.getenv("E2E_ADMIN_USER", "admin@example.com")
ADMIN_PW = os.getenv("E2E_ADMIN_PW", "password")


def login_via_api(session: requests.Session) -> None:
    resp = session.post(
        f"{BASE}/admin/login", json={"email": ADMIN_USER, "password": ADMIN_PW}
    )
    assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"


def test_admin_login_and_csrf():
    """Skeleton E2E: log in via API, import cookies into Playwright, verify XSRF-TOKEN cookie."""
    s = requests.Session()
    login_via_api(s)

    # Transfer cookies from requests session into Playwright context
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        cookies = []
        for c in s.cookies:
            cookies.append(
                {
                    "name": c.name,
                    "value": c.value,
                    "domain": "localhost",
                    "path": c.path or "/",
                }
            )

        if cookies:
            context.add_cookies(cookies)

        page = context.new_page()
        page.goto(f"{BASE}/admin/dashboard")

        ctx_cookies = context.cookies()
        names = [c["name"] for c in ctx_cookies]
        assert "XSRF-TOKEN" in names, f"XSRF-TOKEN cookie not found: {names}"

        browser.close()
