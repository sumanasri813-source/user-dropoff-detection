Playwright E2E test skeleton

Prerequisites
- The application must be running locally (default at `http://localhost:8000`).
- Create a test admin user in the database with admin role, or point the test to a staging environment with a known admin user.

Quick start

```bash
python -m pip install -r e2e/requirements.txt
python -m playwright install --with-deps

# Run the example test (assumes app running and env vars set):
E2E_BASE_URL=http://localhost:8000 E2E_ADMIN_USER=admin@example.com E2E_ADMIN_PW=secret pytest -q e2e/test_admin_e2e.py
```

Notes
- The test is a lightweight skeleton that logs in via the API, copies session cookies into a Playwright browser context, then verifies the `XSRF-TOKEN` cookie is present.
- You may expand the tests to cover CSRF-protected actions, CSV exports, and typeahead endpoints.
