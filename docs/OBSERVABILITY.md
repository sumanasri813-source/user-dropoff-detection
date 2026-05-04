**Observability Integration Notes**

Purpose
- Provide practical guidance to integrate logging, errors, metrics, and alerts for production.

Principles
- Emit structured JSON logs from the app (timestamp, level, request_id, path, user_id, message, extras).
- Capture unhandled exceptions and breadcrumbs with an error monitoring service (Sentry, Rollbar).
- Export metrics (counters, latencies, gauges) to Prometheus or a metrics backend (Datadog).
- Define clear alerting thresholds for critical errors, high error-rate, CSRF validation spikes, and failed background jobs.

Suggested components and quick setup

- Sentry (error monitoring)
  - Env var: `SENTRY_DSN` (leave empty to disable).
  - Install: `pip install sentry-sdk`
  - Init in `src/api/app.py` early using `sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'), traces_sample_rate=0.1)` and attach request_id as a tag.

- Datadog (APM & metrics)
  - Env vars: `DD_AGENT_HOST`, `DD_TRACE_ENABLED`, `DD_ENV`.
  - Install: `pip install ddtrace datadog`
  - Use DogStatsD for custom metrics or forward Prometheus metrics to Datadog.

- Prometheus (metrics)
  - The app already exposes monitoring snapshot endpoints. Deploy a Prometheus scrape job to fetch `/monitor` or instrument `collector` to expose `/metrics` in Prometheus format.
  - Define target scrape interval and retention according to traffic.

- Logs
  - Ensure `src/utils/logger.py` emits JSON when `LOG_FORMAT=json`. Include `request_id` and `service` tags.
  - Forward logs to a centralized aggregator (Stackdriver/CloudWatch/Datadog/ELK).

- Alerts & Dashboards
  - Alert on: sustained 5xx rate (>1% traffic), sudden spike in CSRF failures, job worker down, high error rate in health checks.
  - Dashboards: requests/sec, p50/p95 latencies, error rate, CSRF failure rate, background worker status.

Operational notes
- Local dev: disable external integrations by not setting DSNs/keys and rely on console logs and test metrics.
- Staging: enable Sentry + metrics, test alerts with synthetic traffic before production.
- Production: enable full tracing, retention, and sampling rules to control costs.

Env vars checklist

- SESSION_SECRET_KEY (required)
- JWT_SECRET_KEY (required)
- SENTRY_DSN (optional)
- DD_AGENT_HOST (optional)
- ENABLE_SECURITY_HARDENING (optional)

Next steps
- Add minimal Sentry init to `src/api/app.py` guarded by `SENTRY_DSN` and attach `g.request_id`.
- Consider adding a Prometheus `/metrics` endpoint (using `prometheus_client`) to expose collector metrics.
