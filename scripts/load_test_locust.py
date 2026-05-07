"""
Locust load testing script for FastAPI async endpoints.

Run with:
    locust -f scripts/load_test_locust.py --host=http://localhost:8000 -u 50 -r 5 -t 5m --headless
"""

import random
from locust import HttpUser, task, between


class APIUser(HttpUser):
    """Simulates typical API user behavior."""
    
    wait_time = between(1, 3)
    
    sample_user_ids = [f"user_{i}" for i in range(1, 101)]
    
    @task(50)
    def root(self):
        """Root endpoint - 50% of requests."""
        self.client.get("/", name="GET /")
    
    @task(30)
    def health_check(self):
        """Health check endpoint - 30% of requests."""
        self.client.get("/health", name="GET /health")
    
    @task(10)
    def predict_single(self):
        """Single prediction - 10% of requests."""
        user_id = random.choice(self.sample_user_ids)
        payload = {
            "user_id": user_id,
            "session_duration_seconds": random.randint(60, 600),
            "click_count": random.randint(1, 50),
        }
        self.client.post("/predict", json=payload, name="POST /predict")
    
    @task(5)
    def batch_predict(self):
        """Batch prediction - 5% of requests."""
        samples = [
            {
                "user_id": random.choice(self.sample_user_ids),
                "session_duration_seconds": random.randint(60, 600),
                "click_count": random.randint(1, 50),
            }
            for _ in range(random.randint(1, 5))
        ]
        payload = {"samples": samples}
        self.client.post("/predict/batch", json=payload, name="POST /predict/batch")
    
    @task(5)
    def monitor(self):
        """Monitor endpoint - 5% of requests."""
        self.client.get("/monitor", name="GET /monitor")
