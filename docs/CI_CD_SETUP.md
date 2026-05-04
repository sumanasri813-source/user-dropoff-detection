**CI/CD Setup Guide for Production**

Overview
- GitHub Actions runs unit tests on every push and PR (`.github/workflows/ci.yaml`).
- E2E tests can be run manually on demand via workflow_dispatch (`.github/workflows/e2e.yaml`).
- All pipelines validate environment variables early and fail fast on missing secrets.

Quick Start

1. Push code to your repository:
```bash
git add .
git commit -m "Production security and deployment setup"
git push origin main
```

2. GitHub Actions will automatically run unit tests on the push.

3. To run E2E tests:
   - Go to your GitHub repository → Actions tab
   - Select the "E2E" workflow
   - Click "Run workflow"
   - Fill in the required secrets (see below)
   - The workflow will run Playwright tests against your staging/prod environment

GitHub Actions Secrets Setup

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

- `E2E_BASE_URL`: Full URL of your testing environment (e.g., `https://staging-api.example.com` or `http://localhost:5000`).
- `E2E_ADMIN_USER`: Admin username or email for testing (e.g., `admin@example.com`).
- `E2E_ADMIN_PW`: Password for the admin account (use a test account, not production credentials).

Steps to add secrets:
1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each secret with the name and value
4. Repeat for all three secrets

Environment Variables for Deployment

When deploying to production or staging, ensure the following env vars are set:

- `SESSION_SECRET_KEY` (required): Random string for signing session cookies. Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`
- `JWT_SECRET_KEY` (required): Random string for signing JWT tokens. Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`
- `API_KEY` (optional): API key for non-browser clients.
- `FLASK_ENV` or `ENABLE_SECURITY_HARDENING` (optional): Set to "production" to enable HSTS and Secure cookies.
- `SENTRY_DSN` (optional): Sentry error monitoring DSN; leave empty to disable.
- `AUDIT_RETENTION_DAYS` (optional): Number of days to retain audit logs; default 90.

Best practices for secrets:
- Never commit secrets to version control
- Use your cloud provider's secrets manager (AWS Secrets Manager, Azure Key Vault, etc.)
- Or use environment files with strict file permissions in your deployment
- Rotate secrets periodically (every 90 days recommended)

Deployment Workflows

Unit Tests (on every push):
- Runs `pytest -q tests/unit`
- Validates env vars with `startup/env_validator.py`
- Fails if required secrets are missing

E2E Tests (manual, on demand via workflow_dispatch):
- Runs Playwright tests against a live environment
- Requires `E2E_BASE_URL`, `E2E_ADMIN_USER`, `E2E_ADMIN_PW` secrets
- Install and runs Playwright browsers in CI
- Keeps credentials in GitHub Secrets (never in logs or code)

Troubleshooting CI Failures

1. Unit test failures:
   - Check the CI logs in Actions tab
   - Run locally: `pytest -q tests/unit`
   - Common issues: missing dependencies, schema changes, fixture issues

2. E2E test failures (if running):
   - Verify `E2E_BASE_URL` is accessible from GitHub Actions runners
   - Check that admin credentials are correct
   - View Playwright reports in Actions artifacts

3. Env validator failing:
   - Ensure `SESSION_SECRET_KEY` and `JWT_SECRET_KEY` are set as GitHub Secrets
   - For CI: secrets are injected as environment variables automatically
   - For local dev: set in `.env` or shell environment before running

Production Checklist

Before deploying to production:
- [ ] All unit tests passing locally and in CI
- [ ] Environment variables set in secrets manager or deployment platform
- [ ] HTTPS enabled on production domain
- [ ] HSTS header enabled (via `ENABLE_SECURITY_HARDENING=true`)
- [ ] Admin account created with strong password (stored securely, not in code)
- [ ] Sentry DSN configured (optional but recommended for error tracking)
- [ ] Database backups enabled
- [ ] Monitoring and alerting set up (logs, metrics, health checks)
- [ ] Audit logs retention configured
- [ ] Session and JWT secrets rotated and stored securely

Example Deployment (systemd)

See [DEPLOYMENT_SYSTEMD.md](./DEPLOYMENT_SYSTEMD.md) for systemd service setup.

Example Deployment (Docker)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
ENV SESSION_SECRET_KEY=${SESSION_SECRET_KEY}
ENV JWT_SECRET_KEY=${JWT_SECRET_KEY}
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "src.api.app:app"]
```

Build and run:
```bash
docker build -t user-dropoff-api .
docker run -e SESSION_SECRET_KEY=<secret> -e JWT_SECRET_KEY=<secret> -p 8000:8000 user-dropoff-api
```

Next Steps

1. Configure GitHub Secrets for E2E testing
2. Push code to trigger CI
3. Monitor the first run in Actions tab
4. Deploy to staging using your preferred method
5. Run E2E tests against staging
6. Deploy to production following your release process
