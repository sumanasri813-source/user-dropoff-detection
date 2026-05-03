**Run the API with Docker (gunicorn, Python 3.11)**

Build the image locally:

```bash
docker build -t user-dropoff-detection:gunicorn -f Dockerfile .
```

Run the container mounting model, processed data and results from your workspace:

```bash
docker run -d --name user-dropoff-gunicorn \
  -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/data/processed:/app/data/processed \
  -v $(pwd)/results:/app/results \
  user-dropoff-detection:gunicorn
```

Check health:

```bash
curl http://127.0.0.1:8000/health
```

Example `/predict` request (JSON body):

```json
{
  "days_signup_age": 250,
  "recency_days": 45,
  "frequency_total": 9,
  "session_duration_avg": 6.5,
  "feature_count_used": 2,
  "device_type": "mobile",
  "os_type": "android",
  "user_segment": "free",
  "region": "north"
}
```

Push the image to Docker Hub (replace `<user>` and ensure you're logged in):

```bash
docker tag user-dropoff-detection:gunicorn <user>/user-dropoff-detection:gunicorn
docker push <user>/user-dropoff-detection:gunicorn
```

Notes
- The image uses `requirements-prod.txt` (minimal runtime deps). If you need dev tools, build with the full `requirements.txt`.
- If you prefer `gunicorn` in your local environment rather than Docker, ensure you run it in Python 3.11 to avoid `pkg_resources` issues.
- The container now runs as a non-root user (`app`) for better security.
- CI workflow `.github/workflows/docker-image.yml` builds the image and can publish to GHCR on `main`/tags.
