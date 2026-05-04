# Production Deployment & CI/CD Guide

This guide provides the complete setup for deploying to production with automated testing and monitoring.

## Getting Started

This project includes:
- ✅ Unit tests running on every push (GitHub Actions)
- ✅ E2E tests (Playwright) available on demand
- ✅ CSRF protection with double-submit cookies
- ✅ Admin session-based authentication
- ✅ Audit logging with filters and CSV export
- ✅ Environment variable validation (fail-fast on missing secrets)
- ✅ Security headers (HSTS, CSP, X-Frame-Options)
- ✅ Sentry error monitoring (optional)
- ✅ Observability integration (Prometheus, Datadog, logs)

## Documentation Links

Before deploying, read these guides in order:

1. **[CI_CD_SETUP.md](CI_CD_SETUP.md)** — Complete guide for GitHub Actions setup
   - How to run unit tests locally and in CI
   - How to run E2E tests on demand
   - Environment variables and secrets management
   - Production checklist
   - Docker deployment example

2. **[GITHUB_ACTIONS_SECRETS.md](GITHUB_ACTIONS_SECRETS.md)** — Step-by-step secrets setup
   - Create GitHub repository secrets for E2E tests
   - Security best practices for CI/CD credentials
   - Troubleshooting common issues

3. **[DEPLOYMENT.md](DEPLOYMENT.md)** — Production hardening checklist
   - Session secret separation
   - CSRF and security headers
   - Environment-specific configurations
   - Verified setup guide

4. **[DEPLOYMENT_SYSTEMD.md](DEPLOYMENT_SYSTEMD.md)** — systemd service setup
   - Linux systemd unit file example
   - How to manage the service (start, stop, logs)
   - Secrets management with EnvironmentFile

5. **[OBSERVABILITY.md](OBSERVABILITY.md)** — Monitoring and alerting
   - Sentry error tracking (optional)
   - Prometheus metrics export
   - Datadog APM integration
   - Alert thresholds and dashboards

## Quick Deploy Checklist

For your first production deployment:

```bash
# 1. Generate secrets (run locally, save securely)
python -c "import secrets; print('SESSION_SECRET_KEY:', secrets.token_hex(32))"
python -c "import secrets; print('JWT_SECRET_KEY:', secrets.token_hex(32))"

# 2. Set environment variables in your deployment platform
# (AWS Secrets Manager, Azure Key Vault, etc.)
export SESSION_SECRET_KEY=<generated-secret>
export JWT_SECRET_KEY=<generated-secret>
export ENABLE_SECURITY_HARDENING=true

# 3. Run locally to verify
PYTHONPATH=/path/to/app SESSION_SECRET_KEY=$SESSION_SECRET_KEY \
  JWT_SECRET_KEY=$JWT_SECRET_KEY FLASK_ENV=production python src/api/app.py

# 4. Run unit tests
pytest -q tests/unit

# 5. Deploy to your server/container platform
# Use the startup script: startup/run.sh (guided by startup/env_validator.py)

# 6. Configure GitHub Actions secrets for E2E testing
# See GITHUB_ACTIONS_SECRETS.md

# 7. Run E2E tests manually in GitHub Actions
# Go to Actions tab → E2E → Run workflow (on demand)
```

## Environment Validation

The app validates all required environment variables on startup and fails fast if any are missing:

```bash
# This runs automatically when the app starts
python startup/env_validator.py

# To run manually for testing:
SESSION_SECRET_KEY=test JWT_SECRET_KEY=test python startup/env_validator.py
```

If validation fails, you'll see:
```
Missing required environment variables: SESSION_SECRET_KEY, JWT_SECRET_KEY
```

## Example: Deploy with Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Set environment
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Run validation on startup
RUN python startup/env_validator.py || true

# Start app
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "src.api.app:app"]
```

Build and run:
```bash
docker build -t user-dropoff-api .
docker run \
  -e SESSION_SECRET_KEY=<your-secret> \
  -e JWT_SECRET_KEY=<your-secret> \
  -e ENABLE_SECURITY_HARDENING=true \
  -e SENTRY_DSN=https://... \
  -p 8000:8000 \
  user-dropoff-api
```

## CI/CD Pipeline Status

Your repository now has two GitHub Actions workflows:

### Workflow 1: Unit Tests (Automatic)
- **File:** `.github/workflows/ci.yaml`
- **Trigger:** Every push to main, all pull requests
- **Tests:** Unit tests + environment validator
- **Status:** Check the Actions tab after each push

### Workflow 2: E2E Tests (Manual)
- **File:** `.github/workflows/e2e.yaml`
- **Trigger:** Manual via GitHub Actions "Run workflow" button
- **Tests:** Playwright browser tests
- **Requires:** GitHub Actions secrets (see GITHUB_ACTIONS_SECRETS.md)

## Troubleshooting

### App fails to start
Check that `SESSION_SECRET_KEY` and `JWT_SECRET_KEY` are set:
```bash
echo $SESSION_SECRET_KEY  # Should output: (not empty)
echo $JWT_SECRET_KEY       # Should output: (not empty)
```

### Unit tests fail locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests with verbose output
pytest -v tests/unit

# Check for missing dependencies
pip list | grep <package-name>
```

### E2E tests fail in CI
See [GITHUB_ACTIONS_SECRETS.md](GITHUB_ACTIONS_SECRETS.md#troubleshooting) for common issues.

### Sentry not capturing errors
1. Verify `SENTRY_DSN` is set (optional)
2. Check Sentry project settings
3. Look at app logs for `sentry_init_failed` messages

## Support

For issues or questions:
1. Check the troubleshooting sections in the docs above
2. Run `pytest -v tests/unit` locally
3. Review GitHub Actions logs in the Actions tab
4. Check `docs/` directory for additional guides

## Next Steps

1. ✅ Read [CI_CD_SETUP.md](CI_CD_SETUP.md)
2. ✅ Read [GITHUB_ACTIONS_SECRETS.md](GITHUB_ACTIONS_SECRETS.md) and add secrets
3. ✅ Push code to trigger CI
4. ✅ Monitor the first CI run in Actions tab
5. ✅ Deploy to staging using your preferred method
6. ✅ Run E2E tests against staging
7. ✅ Deploy to production

That's it! Your project is production-ready.
