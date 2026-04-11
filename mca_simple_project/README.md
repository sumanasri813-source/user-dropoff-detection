# MCA Major Project - Simple Version

A beginner-friendly machine learning project for university submission demonstrating silent user drop-off detection.

## What is Included

- `generate_data.py` - Creates 1,000 synthetic user records with dropout probability labels
- `train_model.py` - Trains Logistic Regression classifier (80/20 train-test split)
- `api_app.py` - Flask REST API for predictions (port 5050)
- `dashboard_app.py` - Streamlit interactive dashboard (port 8501)
- `requirements.txt` - Minimal dependencies (6 core packages)
- `run_mca_demo.ps1` - One-click automation script

## 🚀 Quickest Way (Recommended - One-Click Demo)

**Windows PowerShell** - Runs everything automatically:

```powershell
cd mca_simple_project
.\run_mca_demo.ps1
```

This script handles all steps automatically:
1. Creates Python virtual environment
2. Installs all dependencies
3. Generates synthetic data
4. Trains the ML model
5. Starts Flask API (new terminal)
6. Launches Streamlit dashboard (new terminal)

**Total time: ~30-40 seconds!** Dashboard opens automatically.

---

## Manual Step-by-Step Setup (Learning Approach - Windows)

1. Open terminal in project root:

```powershell
cd C:\Users\Sumana Sri\OneDrive\Desktop\project\user-dropoff-detection
```

2. Activate environment:

```powershell
.\venv\Scripts\Activat
e.ps1
```

3. Install simple dependencies:

```powershell
python -m pip install -r mca_simple_project/requirements.txt
```

4. Generate data:

```powershell
python mca_simple_project/generate_data.py
```

5. Train model:

```powershell
python mca_simple_project/train_model.py
```

6. Start API (new terminal):

```powershell
python mca_simple_project/api_app.py
```

7. Start dashboard (another terminal):

```powershell
streamlit run mca_simple_project/dashboard_app.py
```

8. Open dashboard URL shown by Streamlit (usually `http://localhost:8501`).

## API test (optional)

```powershell
curl -X POST http://127.0.0.1:5050/predict -H "Content-Type: application/json" -d "{\"days_signup_age\":200,\"recency_days\":20,\"frequency_total\":10,\"session_duration_avg\":8.5,\"feature_count_used\":4}"
```
