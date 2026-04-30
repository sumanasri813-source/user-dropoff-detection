# Deployment Guide

Complete deployment instructions for User Dropoff Detection API and Dashboard.

---

## Table of Contents
1. [Local Deployment](#local-deployment)
2. [Render Deployment](#render-deployment)
3. [AWS EC2 Deployment](#aws-ec2-deployment)
4. [Railway Deployment](#railway-deployment)
5. [Performance & Monitoring](#performance--monitoring)

---

## Local Deployment

### Prerequisites
- Python 3.12+
- pip or conda
- SQLite3 (included with Python)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Generate Data & Train Model
```bash
python src/data/generate_synthetic_data.py
python src/models/train_model.py
python src/evaluation/evaluate_model.py
```

### Step 3: Start API Server
```bash
python -m src.api.app
# Server runs on http://127.0.0.1:5000
```

### Step 4: Start Streamlit Dashboard (in new terminal)
```bash
python -m streamlit run streamlit_dashboard.py
# Dashboard runs on http://localhost:8501
```

### Step 5: Test API (Optional)
```bash
curl -X POST http://127.0.0.1:5000/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-local-key" \
  -d '{
    "days_signup_age": 180,
    "recency_days": 15,
    "frequency_total": 45,
    "session_duration_avg": 12.5,
    "feature_count_used": 8,
    "device_type": "desktop",
    "os_type": "windows",
    "user_segment": "premium",
    "region": "north"
  }'
```

---

## Render Deployment

### Prerequisites
- GitHub account with repository
- Render account (https://render.com)

### Step 1: Create GitHub Repository
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/user-dropoff-detection.git
git push -u origin main
```

### Step 2: Create `Dockerfile`
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p logs data/raw data/processed models results

# Expose ports
EXPOSE 5000 8501

# Run both API and dashboard
CMD gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 src.api.app:app & \
    streamlit run streamlit_dashboard.py --server.port 8501 --server.address 0.0.0.0
```

### Step 3: Create `render.yaml`
```yaml
services:
  - type: web
    name: dropoff-detection-api
    runtime: python
    pythonVersion: 3.12
    buildCommand: pip install -r requirements.txt && python src/models/train_model.py
    startCommand: gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 src.api.app:app
    envVars:
      - key: FLASK_ENV
        value: production
    autoDeploy: true

  - type: web
    name: dropoff-detection-dashboard
    runtime: python
    pythonVersion: 3.12
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run streamlit_dashboard.py --server.port $PORT --server.address 0.0.0.0
    envVars:
      - key: API_URL
        value: https://dropoff-detection-api.onrender.com
    autoDeploy: true
```

### Step 4: Deploy on Render
1. Go to https://render.com/dashboard
2. Click "New +" → "Web Service"
3. Select your GitHub repository
4. Set:
   - **Name**: `dropoff-detection-api`
   - **Runtime**: Python 3.12
   - **Build Command**: `pip install -r requirements.txt && python src/models/train_model.py`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 4 src.api.app:app`
5. Add environment variable: `FLASK_ENV=production`
6. Click "Deploy"

Repeat for dashboard service with:
- **Start Command**: `streamlit run streamlit_dashboard.py --server.port $PORT --server.address 0.0.0.0`
- **Environment**: `API_URL=https://dropoff-detection-api.onrender.com`

---

## AWS EC2 Deployment

### Step 1: Launch EC2 Instance
```bash
# Use Ubuntu 22.04 LTS
# t3.medium or larger recommended
# Open ports: 5000 (API), 8501 (Dashboard), 22 (SSH)
```

### Step 2: Connect and Setup
```bash
ssh -i your-key.pem ubuntu@your-instance-ip

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python 3.12
sudo apt-get install -y python3.12 python3.12-venv python3-pip

# Install system dependencies
sudo apt-get install -y build-essential libssl-dev libffi-dev

# Clone repository
git clone https://github.com/YOUR_USERNAME/user-dropoff-detection.git
cd user-dropoff-detection
```

### Step 3: Create Virtual Environment
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Train Model
```bash
python src/data/generate_synthetic_data.py
python src/models/train_model.py
python src/evaluation/evaluate_model.py
```

### Step 5: Create Systemd Services

**For API** (`/etc/systemd/system/dropoff-api.service`):
```ini
[Unit]
Description=User Dropoff Detection API
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/home/ubuntu/user-dropoff-detection
Environment="PATH=/home/ubuntu/user-dropoff-detection/venv/bin"
ExecStart=/home/ubuntu/user-dropoff-detection/venv/bin/gunicorn \
    --workers 4 \
    --bind 0.0.0.0:5000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    src.api.app:app

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**For Dashboard** (`/etc/systemd/system/dropoff-dashboard.service`):
```ini
[Unit]
Description=User Dropoff Detection Dashboard
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/user-dropoff-detection
Environment="PATH=/home/ubuntu/user-dropoff-detection/venv/bin"
ExecStart=/home/ubuntu/user-dropoff-detection/venv/bin/streamlit run \
    streamlit_dashboard.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --logger.level=info

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Step 6: Enable and Start Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable dropoff-api
sudo systemctl enable dropoff-dashboard
sudo systemctl start dropoff-api
sudo systemctl start dropoff-dashboard

# Check status
sudo systemctl status dropoff-api
sudo systemctl status dropoff-dashboard
```

### Step 7: Configure Nginx Reverse Proxy
```bash
sudo apt-get install -y nginx

# Create config at /etc/nginx/sites-available/dropoff
sudo nano /etc/nginx/sites-available/dropoff
```

```nginx
upstream api {
    server 127.0.0.1:5000;
}

upstream dashboard {
    server 127.0.0.1:8501;
}

server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://dashboard/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable and start Nginx
sudo ln -s /etc/nginx/sites-available/dropoff /etc/nginx/sites-enabled/
sudo systemctl enable nginx
sudo systemctl start nginx
```

---

## Railway Deployment

### Prerequisites
- Railway account (https://railway.app)
- GitHub connected to Railway

### Step 1: Push Code to GitHub
```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### Step 2: Create `Procfile`
```
api: gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 src.api.app:app
dashboard: streamlit run streamlit_dashboard.py --server.port $PORT --server.address 0.0.0.0
```

### Step 3: Configure on Railway
1. Go to https://railway.app/dashboard
2. Click "New Project" → "Deploy from GitHub"
3. Select your repository
4. Add plugin: PostgreSQL (for production database)
5. Set environment variables:
   - `FLASK_ENV=production`
   - `DATABASE_URL=postgresql://...` (provided by Railway)
   - `API_KEY=your-secure-key`

### Step 4: Deploy
```bash
# Railway CLI
npm install -g @railway/cli
railway link

# Deploy
railway deploy
```

---

## Performance & Monitoring

### Monitoring Setup

1. **Logs**: Check at `logs/` directory
   ```bash
   # View API logs
   tail -f logs/api.log
   
   # View prediction audit trail
   tail -f logs/audit.jsonl
   ```

2. **Health Check**:
   ```bash
   curl http://your-domain/health
   ```

3. **Metrics**:
   ```bash
   curl http://your-domain/monitor
   ```

### Production Checklist

- [ ] SSL/TLS certificate installed (HTTPS)
- [ ] Rate limiting enabled (100 req/min per API key)
- [ ] Logging configured (JSON structured logs)
- [ ] Database backups enabled
- [ ] Health checks configured in load balancer
- [ ] Error alerts configured (Slack/PagerDuty)
- [ ] API documentation accessible
- [ ] Postman collection for API testing
- [ ] Performance monitoring enabled
- [ ] Model performance tracking enabled

### Scaling Recommendations

| Load | Recommendation |
|------|---|
| <100 req/min | Single t3.micro instance |
| 100-1000 req/min | t3.small with load balancer |
| >1000 req/min | Horizontal scaling with 3+ instances |

### Database Migration (SQLite → PostgreSQL)

For production, migrate from SQLite to PostgreSQL:

```bash
# Update config.yaml
database:
  type: postgresql
  host: your-rds-endpoint
  port: 5432
  database: dropoff_db
  user: postgres
  password: your-secure-password
```

Update connection string in `src/db/connection.py`:
```python
DATABASE_URL = "postgresql+psycopg2://user:password@host:5432/dropoff_db"
```

---

## Troubleshooting

### API Won't Start
```bash
# Check for port conflicts
lsof -i :5000

# Check logs
tail -f logs/api.log

# Test model loading
python -c "import joblib; joblib.load('models/final_model.pkl')"
```

### Dashboard Connection Issues
```bash
# Verify API is running
curl http://127.0.0.1:5000/health

# Check Streamlit configuration
streamlit config show

# Restart dashboard
systemctl restart dropoff-dashboard
```

### Database Connection Errors
```bash
# Test database
python -c "from src.db.connection import get_session_factory; get_session_factory()"

# Reset database
rm mlops/dev.db
python -c "from src.db.connection import init_database; init_database()"
```

---

## Support & Documentation

- API Docs: `http://your-domain/api/docs`
- GitHub: https://github.com/YOUR_USERNAME/user-dropoff-detection
- Postman Collection: `Postman_Collection.json`
- Status Page: `http://your-domain/health`
