FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# Use a dedicated non-root user for runtime hardening.
RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements-prod.txt ./
RUN pip install -r requirements-prod.txt

COPY --chown=app:app . .

# Ensure runtime-writable directories exist for non-root execution.
RUN mkdir -p /app/logs /app/results /app/data/processed /app/models \
	&& chown -R app:app /app

USER app

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "src.api.app:app", "--log-level", "info"]
