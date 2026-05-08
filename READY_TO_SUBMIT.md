# Ready To Submit: One-Session Checklist

This file is the fastest end-to-end flow to run, verify, and present the project in one session.

## 1) Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-demo.txt
```

## 2) One-click demo startup (API + Dashboard)

```powershell
powershell -ExecutionPolicy Bypass -File run_final_process.ps1
```

Expected:
- API health endpoint ready
- Dashboard available at http://127.0.0.1:8502

## 3) Contract tests with saved colored output

```powershell
python -m pytest tests/contract -vv --color=yes 2>&1 | Tee-Object -FilePath .\logs\pytest_contract_output.txt
```

## 4) Full tests with saved colored output

```powershell
python -m pytest -vv --color=yes 2>&1 | Tee-Object -FilePath .\logs\pytest_full_output.txt
```

## 5) Train and regenerate model artifacts

```powershell
python -m src.models.train_model
```

Expected files:
- models/best_model.pkl
- models/final_model.pkl
- results/model_comparison.csv
- results/model_metrics.txt
- results/training_summary.json

## 6) Generate thesis/demo plots

```powershell
python scripts/plot_model_comparison.py
```

Expected plot files:
- results/plots/model_comparison.png
- results/plots/roc_auc.png
- results/plots/precision.png
- results/plots/recall.png
- results/plots/f1.png

## 7) Async DB fallback verification

New async-compatible DB helpers are available in src/db/connection.py:
- get_async_database_url()
- get_async_session_factory()
- get_async_session()

Behavior:
- Uses async SQLAlchemy session when async driver exists.
- Falls back to sync Session automatically when async driver is unavailable.

Run focused test:

```powershell
python -m pytest tests/integration/test_connection_async_fallback.py -q
```

## 8) Final evidence pack for report/thesis

Use these files as appendix evidence:
- logs/pytest_contract_output.txt
- logs/pytest_full_output.txt
- results/model_comparison.csv
- results/model_metrics.txt
- results/training_summary.json
- results/plots/*.png

## 9) If dashboard does not load

Check:
- logs/dashboard.err.log
- logs/demo_api.err.log

Then restart:

```powershell
powershell -ExecutionPolicy Bypass -File run_final_process.ps1 -SkipInstall
```
