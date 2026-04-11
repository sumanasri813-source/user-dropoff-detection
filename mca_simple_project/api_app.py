from flask import Flask, jsonify, request
import joblib
import pandas as pd
from pathlib import Path

app = Flask(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_ROOT / "models" / "dropoff_model.pkl"
model = joblib.load(MODEL_PATH)

REQUIRED_FIELDS = [
    "days_signup_age",
    "recency_days",
    "frequency_total",
    "session_duration_avg",
    "feature_count_used",
]


@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.post("/predict")
def predict():
    payload = request.get_json(silent=True) or {}

    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    try:
        row = pd.DataFrame([payload])[REQUIRED_FIELDS]
        proba = float(model.predict_proba(row)[:, 1][0])
        pred = int(proba >= 0.5)

        return (
            jsonify(
                {
                    "dropoff_probability": round(proba, 4),
                    "predicted_label": pred,
                    "risk_level": "high" if proba >= 0.7 else "medium" if proba >= 0.4 else "low",
                }
            ),
            200,
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
