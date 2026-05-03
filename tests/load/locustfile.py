from locust import HttpUser, task, between
import json
import random

class DropoffAPIUser(HttpUser):
    """Load test user that simulates API usage patterns"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a simulated user starts"""
        self.sample_payload = {
            "user_id": random.randint(1000, 9999),
            "session_duration_minutes": random.randint(1, 120),
            "pages_visited": random.randint(1, 50),
            "items_added": random.randint(0, 20),
            "items_removed": random.randint(0, 5),
            "price_sensitivity_percentile": random.randint(10, 90)
        }
    
    @task(3)
    def health_check(self):
        """Health endpoint (higher frequency)"""
        self.client.get(
            "/health",
            name="health_check"
        )
    
    @task(7)
    def verify_prediction(self):
        """Make a prediction request (most common task)"""
        self.client.post(
            "/predict",
            json=self.sample_payload,
            headers={"Content-Type": "application/json"},
            name="predict"
        )
    
    @task(2)
    def batch_predict(self):
        """Batch prediction (less frequent)"""
        batch_payload = {
            "predictions": [
                {
                    "user_id": random.randint(1000, 9999),
                    "session_duration_minutes": random.randint(1, 120),
                    "pages_visited": random.randint(1, 50),
                    "items_added": random.randint(0, 20),
                    "items_removed": random.randint(0, 5),
                    "price_sensitivity_percentile": random.randint(10, 90)
                }
                for _ in range(5)
            ]
        }
        self.client.post(
            "/predict-batch",
            json=batch_payload,
            headers={"Content-Type": "application/json"},
            name="predict_batch"
        )
    
    @task(1)
    def invalid_request(self):
        """Simulate invalid requests (error handling test)"""
        self.client.post(
            "/predict",
            json={"invalid": "data"},
            headers={"Content-Type": "application/json"},
            name="invalid_request"
        )
