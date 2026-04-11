import numpy as np
import pandas as pd
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parent
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    np.random.seed(42)
    n = 1000

    days_signup_age = np.random.randint(1, 900, n)
    recency_days = np.random.randint(0, 60, n)
    frequency_total = np.random.randint(1, 40, n)
    session_duration_avg = np.round(np.random.uniform(1.0, 25.0, n), 2)
    feature_count_used = np.random.randint(1, 12, n)

    # Simple rule to create a realistic target label for student project demo
    risk_score = (
        (recency_days * 0.05)
        + ((20 - np.minimum(frequency_total, 20)) * 0.03)
        + ((8 - np.minimum(feature_count_used, 8)) * 0.04)
        + ((10 - np.minimum(session_duration_avg, 10)) * 0.02)
    )

    probability = 1 / (1 + np.exp(-(risk_score - 1.5)))
    dropoff = (probability > 0.5).astype(int)

    df = pd.DataFrame(
        {
            "days_signup_age": days_signup_age,
            "recency_days": recency_days,
            "frequency_total": frequency_total,
            "session_duration_avg": session_duration_avg,
            "feature_count_used": feature_count_used,
            "dropoff": dropoff,
        }
    )

    output_path = data_dir / "user_data.csv"
    df.to_csv(output_path, index=False)
    print(f"Saved dataset: {output_path}")
    print(df.head())


if __name__ == "__main__":
    main()
