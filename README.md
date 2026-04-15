# User Drop-Off Detection in Web Applications
## Quick Start Guide

### 📋 Project Overview
This project uses Machine Learning to detect users who are likely to leave (drop-off) a web application, enabling proactive intervention strategies.

**Goal:** Build a predictive model that identifies at-risk users 30 days before they become inactive.

---

## 🚀 QUICK START (Next 30 Minutes)

### Step 1: Read the Roadmap
Open `PROJECT_ROADMAP.md` - It contains your complete guide with every tiny step.

### Step 2: Create Project Structure
```bash
# Run these commands in your terminal

# Create directories
mkdir data data\raw data\processed
mkdir src src\data src\features src\models src\evaluation src\api src\dashboard src\utils
mkdir notebooks
mkdir models
mkdir results
mkdir docs
mkdir tests
```

### Step 3: Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate  # On Windows
# or
source venv/bin/activate  # On MacOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Verify Installation
```bash
python -c "import pandas; import sklearn; print('✓ All packages installed!')"
```

---

## 📚 How to Use This Project

1. **Read First:** Start with `PROJECT_ROADMAP.md` - it guides every single step
2. **Follow Phase by Phase:** Don't skip ahead - each phase builds on the previous
3. **Code Along:** Create scripts as described in the roadmap
4. **Test Frequently:** Work incrementally and test after each phase
5. **Document Everything:** Write comments explaining your code

---

## 🎯 Key Phases at a Glance

| Phase | Duration | Focus |
|-------|----------|-------|
| **1** | Week 1 | Setup & Planning |
| **2-3** | Week 2-3 | Data Collection & Analysis |
| **4-5** | Week 4-5 | Feature Engineering & Preprocessing |
| **6-7** | Week 6-7 | Model Development |
| **8-9** | Week 8-9 | Tuning & Evaluation |
| **10-12** | Week 10-12 | Deployment & Documentation |

---

## 📁 What Each Folder Means

```
user-dropoff-detection/
├── data/               ← Store datasets here
├── src/                ← All your code goes here
├── notebooks/          ← Jupyter notebooks for exploration
├── models/             ← Saved trained models
├── results/            ← Plots, metrics, outputs
├── docs/               ← Documentation
└── tests/              ← Unit & integration tests
```

---

## 💡 First Real Task (Phase 1)

1. **Create data directory structure** ✓ (done above)
2. **Create config.yaml** - Configuration file
3. **Start first Jupyter notebook** - For data exploration

---

## ❓ Questions?

Refer to the `PROJECT_ROADMAP.md` - it has answers to everything!

---

**Next Step:** Open `PROJECT_ROADMAP.md` and start with Phase 1! 🎉

---

## ✅ Ready-to-Run Implementation Added

This repository now includes a complete beginner-friendly implementation:

- `STEP_BY_STEP_IMPLEMENTATION.md` - Full execution guide for your project title
- `run_pipeline.py` - Run full ML pipeline in one command
- `src/data/generate_synthetic_data.py` - Synthetic data generator
- `src/features/build_features.py` - Feature dataset builder
- `src/models/train_model.py` - Model training script
- `src/evaluation/evaluate_model.py` - Evaluation script
- `src/api/app.py` - Flask API for prediction

Quick demo command:

```bash
python run_pipeline.py
```

---

## API Key + Filter Examples (Guide/Demo)

### Security Notes

- Protected routes use a shared auth decorator from `src/utils/auth.py`.
- If `security.require_auth` is `true`, requests must include `X-API-Key`.
- `API_KEY` env var takes priority over `security.api_key` in YAML config.
- `/favicon.ico` remains public so browser requests do not create auth noise.

Set your key first:

```bash
set API_KEY=your-secret-key
```

List users (auth required when `security.require_auth: true`):

```bash
curl -H "X-API-Key: %API_KEY%" "http://127.0.0.1:5000/users?limit=5&offset=0&user_segment=premium"
```

List predictions with filters:

```bash
curl -H "X-API-Key: %API_KEY%" "http://127.0.0.1:5000/predictions?risk_level=high&min_probability=0.7&limit=10"
```

Read monitor snapshot:

```bash
curl -H "X-API-Key: %API_KEY%" "http://127.0.0.1:5000/monitor"
```

Make a single prediction:

```bash
curl -X POST -H "Content-Type: application/json" -H "X-API-Key: %API_KEY%" \
	-d "{\"days_signup_age\":10,\"recency_days\":2,\"frequency_total\":20,\"session_duration_avg\":12.5,\"feature_count_used\":4,\"device_type\":\"mobile\",\"os_type\":\"android\",\"user_segment\":\"free\",\"region\":\"north\"}" \
	"http://127.0.0.1:5000/predict"
```

Make a batch prediction:

```bash
curl -X POST -H "Content-Type: application/json" -H "X-API-Key: %API_KEY%" \
	-d "{\"records\":[{\"days_signup_age\":10,\"recency_days\":2,\"frequency_total\":20,\"session_duration_avg\":12.5,\"feature_count_used\":4,\"device_type\":\"mobile\",\"os_type\":\"android\",\"user_segment\":\"free\",\"region\":\"north\"}]}" \
	"http://127.0.0.1:5000/predict-batch"
```

Force persist monitoring data:

```bash
curl -X POST -H "X-API-Key: %API_KEY%" "http://127.0.0.1:5000/monitor/persist"
```

---

## MCA Final 5-Minute Runbook

Use this exact flow for project demo/evaluation.

One-click option in VS Code:
- Open Command Palette -> `Tasks: Run Task` -> choose `Run final demo process`
- This runs `run_final_process.ps1` and prints health output when ready.

1. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

2. Initialize database schema

```bash
python mlops/deployment/db/migrate.py
```

3. Set runtime environment and API key (Windows)

```bash
set APP_ENV=dev
set API_KEY=dev-local-key
```

4. Start API

```bash
python -m src.api.app
```

5. Verify protected health endpoint (new terminal)

```bash
curl -H "X-API-Key: %API_KEY%" "http://127.0.0.1:5000/health"
```

## Final Acceptance Checklist

- API boots without import/runtime errors.
- `/health`, `/monitor`, `/predict`, `/predict-batch`, `/users`, `/predictions` return `401` without key when auth is enabled.
- Same endpoints return successful responses with valid `X-API-Key`.
- DB migration runs and tables are created.
- Contract tests pass for prediction and CRUD flows.
- Monitoring worker starts and metrics endpoints respond.

## Final Output Evidence Files

- `results/evaluation_metrics.json`
- `results/evaluation_summary.txt`
- `results/model_comparison.csv`
- `mlops/monitoring/alerts/alerts.jsonl`
- `metrics/` JSONL snapshots
