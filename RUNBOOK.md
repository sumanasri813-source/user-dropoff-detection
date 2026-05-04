# CI Runbook and Local Test Run

This runbook documents how to run the project's test matrix locally and in CI using `docker-compose.ci.yml` and GitHub Actions.

Local quick steps

1. Create and activate your Python virtualenv and install deps:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

2. Install Playwright browsers (required for e2e):

```bash
python -m pip install -r e2e/requirements.txt
python -m playwright install --with-deps
```

3. Start the API (test env):

```bash
SESSION_SECRET_KEY=test-session SECRET_KEY=test-jwt .venv/bin/python -m src.api.app
```

4. Run the full test suite:

```bash
pytest -q
```

CI using Docker Compose

- The file `docker-compose.ci.yml` defines `db`, `redis`, and `app` services. The `app` service builds the project and runs the test command.
- GitHub Actions workflow `/.github/workflows/ci-tests.yml` runs `docker-compose -f docker-compose.ci.yml up --build --abort-on-container-exit` and fails the job if tests fail.

Notes
- If your CI runner cannot run Playwright system deps inside Docker, consider running e2e tests separately on the runner (using `python -m playwright install --with-deps`) or switch to Playwright GitHub Action.
