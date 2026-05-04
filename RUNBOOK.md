# CI Runbook and Local Test Run

This runbook documents how to run the project's test matrix locally and in CI. GitHub Actions uses a runner-based Playwright setup plus a Docker image build job, while `docker-compose.ci.yml` remains available as an optional local container path.

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
SESSION_SECRET_KEY=test-session JWT_SECRET_KEY=test-jwt .venv/bin/python -m src.api.app
```

4. Run the full test suite:

```bash
pytest -q
```

CI in GitHub Actions

- `.github/workflows/ci-tests.yml` runs three checks in order: formatting/lint, the full pytest suite with Playwright browsers on the runner, and a Docker image build validation.
- `.github/workflows/ci.yaml` continues to guard the unit-test matrix, and the Python versions are quoted so `3.10` does not collapse to `3.1` in YAML.

Notes
- `docker-compose.ci.yml` is still useful for local smoke testing the container path.
- If you only want the container-based path, run the compose file directly with `docker compose -f docker-compose.ci.yml up --build`.
