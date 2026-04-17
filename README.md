# User Drop-Off Detection in Web Applications

Production-oriented machine learning system that predicts user churn risk and exposes secured inference APIs for operational use.

## Problem Statement

Digital products lose revenue when high-risk users leave before intervention. This project predicts user drop-off probability early enough to trigger retention actions.

Business objective:
- Identify high-risk users before churn
- Provide low-latency API inference
- Enable monitored, repeatable training and evaluation through CI/CD

## Architecture and CI/CD Pipeline

Core components:
- Data pipeline: synthetic generation and preprocessing
- Feature engineering: behavioral + categorical risk features
- Model training: multi-model candidate selection with persisted best model
- Evaluation: threshold analysis, quality metrics, business-value scoring
- API layer: secured Flask endpoints for prediction, health, monitoring, and CRUD
- Monitoring: runtime metrics snapshots and alert artifacts

CI/CD workflow stages in [.github/workflows/mlops-ci-cd.yml](.github/workflows/mlops-ci-cd.yml):
1. Test Stage
2. Train Stage
3. Evaluate Stage
4. Deploy Dev or Staging or Production (branch-based)

## Repository Structure

- src/: application and ML source code
- src/data/: data generation and preprocessing entrypoints
- src/features/: feature engineering logic
- src/models/: training pipeline
- src/evaluation/: evaluation pipeline and reporting
- src/api/: production API routes and services
- mlops/: environment configs, deployment helpers, monitoring artifacts
- tests/: contract and integration tests
- data/: raw and processed datasets
- models/: serialized model artifacts
- results/: evaluation and training outputs

## How to Run the Project

Recommended environment:
- Python 3.11
- Virtual environment

Install:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-demo.txt
```

One-click demo path:
1. Open Command Palette
2. Run Tasks: Run Task
3. Choose Run final demo process

Equivalent terminal command:

```powershell
powershell -ExecutionPolicy Bypass -File run_final_process.ps1
```

Manual pipeline commands:

```powershell
python -m src.data.run_data_step
python -m src.features.build_features
python -m src.models.train_model
python -m src.evaluation.evaluate_model
python -m src.api.app
```

## API Usage

Base URL:
- http://127.0.0.1:5000

Auth model:
- Protected routes require X-API-Key when security.require_auth is true

Set local key (Windows):

```powershell
$env:API_KEY="dev-local-key"
```

Health:

```powershell
curl -H "X-API-Key: dev-local-key" http://127.0.0.1:5000/health
```

Single prediction:

```powershell
curl -X POST http://127.0.0.1:5000/predict -H "Content-Type: application/json" -H "X-API-Key: dev-local-key" -d "{\"days_signup_age\":10,\"recency_days\":2,\"frequency_total\":20,\"session_duration_avg\":12.5,\"feature_count_used\":4,\"device_type\":\"mobile\",\"os_type\":\"android\",\"user_segment\":\"free\",\"region\":\"north\"}"
```

Batch prediction:

```powershell
curl -X POST http://127.0.0.1:5000/predict-batch -H "Content-Type: application/json" -H "X-API-Key: dev-local-key" -d "{\"records\":[{\"days_signup_age\":10,\"recency_days\":2,\"frequency_total\":20,\"session_duration_avg\":12.5,\"feature_count_used\":4,\"device_type\":\"mobile\",\"os_type\":\"android\",\"user_segment\":\"free\",\"region\":\"north\"}]}"
```

## Model Details

Training pipeline highlights:
- Candidate models: logistic regression and random forest, optional XGBoost when available
- Preprocessing: numeric imputation and scaling, categorical imputation and one-hot encoding
- Selection metric: ROC-AUC (best model persisted)
- Persisted artifacts:
  - models/final_model.pkl
  - models/best_model.pkl
  - results/model_comparison.csv
  - results/training_summary.json

Evaluation outputs:
- results/evaluation_metrics.json
- results/evaluation_summary.txt
- results/threshold_analysis.csv

## Results

The project produces recruiter-ready evidence across model quality, threshold optimization, and operational readiness.

Primary metrics tracked:
- ROC-AUC
- F1 Score
- Precision and Recall
- Business-value score from confusion-matrix outcomes

Deployment readiness indicators:
- Contract tests for secured endpoints
- Health and monitor endpoints with runtime metrics
- CI/CD gates that block low-quality models

## Reproducibility and Versioning

To avoid model deserialization issues, runtime and training environments should use the same scikit-learn major/minor version.

Current demo runtime pin:
- scikit-learn==1.8.0 in requirements-demo.txt

Recommended production approach:
1. Pin exact dependency versions for train and serve environments
2. Store model metadata with library versions at training time
3. Retrain model whenever major framework versions change

## Final Submission Checklist

- CI pipeline passes Test, Train, Evaluate stages
- API protected routes behave correctly with and without key
- Final model and evaluation artifacts are generated
- README, DEMO flow, and run scripts are consistent
