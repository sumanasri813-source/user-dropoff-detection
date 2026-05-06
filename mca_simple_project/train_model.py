from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split


def main() -> None:
    project_root = Path(__file__).resolve().parent
    data_path = project_root / "data" / "user_data.csv"
    model_dir = project_root / "models"
    model_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_path)

    feature_cols = [
        "days_signup_age",
        "recency_days",
        "frequency_total",
        "session_duration_avg",
        "feature_count_used",
    ]

    X = df[feature_cols]
    y = df["dropoff"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)

    print(f"Accuracy: {acc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, preds))

    model_path = model_dir / "dropoff_model.pkl"
    joblib.dump(model, model_path)
    print(f"Saved model: {model_path}")


if __name__ == "__main__":
    main()
