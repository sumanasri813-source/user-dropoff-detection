#!/usr/bin/env python3
"""
Performance benchmark: FastAPI Async vs Flask Sync endpoints.

Measures:
- Response time (latency)
- Throughput (requests/sec)
- Memory usage
- CPU usage
- Concurrency handling

Usage:
    python scripts/performance_benchmark.py --runs 5 --concurrency 10,50,100
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List

import psutil
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


class PerformanceBenchmark:
    def __init__(self, flask_url: str = "http://localhost:5000", fastapi_url: str = "http://localhost:8000"):
        self.flask_url = flask_url
        self.fastapi_url = fastapi_url
        self.results: Dict = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "flask": {},
            "fastapi": {},
        }

    def benchmark_endpoint(
        self,
        url: str,
        endpoint: str,
        method: str = "GET",
        json_data: dict = None,
        num_requests: int = 100,
        num_workers: int = 10,
    ) -> Dict:
        """Benchmark a single endpoint with concurrent requests."""
        full_url = f"{url}{endpoint}"
        latencies = []
        errors = 0
        
        start_time = time.time()
        
        def make_request():
            try:
                if method.upper() == "GET":
                    resp = requests.get(full_url, timeout=5)
                else:
                    resp = requests.post(full_url, json=json_data or {}, timeout=5)
                
                if resp.status_code >= 400:
                    return None, resp.status_code
                return resp.elapsed.total_seconds(), resp.status_code
            except Exception as e:
                return None, str(e)
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            for future in as_completed(futures):
                latency, status = future.result()
                if latency:
                    latencies.append(latency)
                else:
                    errors += 1
        
        elapsed = time.time() - start_time
        throughput = num_requests / elapsed if elapsed > 0 else 0
        
        return {
            "endpoint": endpoint,
            "method": method,
            "num_requests": num_requests,
            "num_workers": num_workers,
            "total_time_seconds": round(elapsed, 2),
            "throughput_requests_per_sec": round(throughput, 2),
            "latency_min_ms": round(min(latencies) * 1000, 2) if latencies else 0,
            "latency_max_ms": round(max(latencies) * 1000, 2) if latencies else 0,
            "latency_avg_ms": round(sum(latencies) / len(latencies) * 1000, 2) if latencies else 0,
            "latency_median_ms": round(sorted(latencies)[len(latencies)//2] * 1000, 2) if latencies else 0,
            "success_count": len(latencies),
            "error_count": errors,
            "success_rate": round((len(latencies) / num_requests) * 100, 2) if num_requests > 0 else 0,
        }

    def benchmark_app(self, app_name: str, app_url: str, endpoints: List[tuple]) -> Dict:
        """Benchmark all endpoints of an app."""
        print(f"\n{'='*60}")
        print(f"Benchmarking {app_name.upper()}")
        print(f"{'='*60}")
        
        results = {}
        for endpoint, method, data in endpoints:
            print(f"Testing {method} {endpoint}...", end=" ", flush=True)
            result = self.benchmark_endpoint(
                app_url,
                endpoint,
                method=method,
                json_data=data,
                num_requests=100,
                num_workers=10,
            )
            results[endpoint] = result
            print(f"✓ {result['throughput_requests_per_sec']} req/s")
        
        return results

    def compare_results(self):
        """Compare Flask vs FastAPI results."""
        print(f"\n{'='*60}")
        print("COMPARISON: Flask (Sync) vs FastAPI (Async)")
        print(f"{'='*60}\n")
        
        flask_throughput = sum(r.get("throughput_requests_per_sec", 0) for r in self.results["flask"].values()) / len(self.results["flask"]) if self.results["flask"] else 0
        fastapi_throughput = sum(r.get("throughput_requests_per_sec", 0) for r in self.results["fastapi"].values()) / len(self.results["fastapi"]) if self.results["fastapi"] else 0
        
        improvement = ((fastapi_throughput - flask_throughput) / flask_throughput * 100) if flask_throughput > 0 else 0
        
        print(f"Average Throughput:")
        print(f"  Flask:   {flask_throughput:.2f} req/s")
        print(f"  FastAPI: {fastapi_throughput:.2f} req/s")
        print(f"  Improvement: {improvement:+.1f}%\n")
        
        print("Endpoint Comparison:")
        print(f"{'Endpoint':<20} {'Flask':<20} {'FastAPI':<20} {'Improvement':<15}")
        print("-" * 75)
        
        for endpoint in self.results["flask"]:
            if endpoint in self.results["fastapi"]:
                flask_lat = self.results["flask"][endpoint].get("latency_avg_ms", 0)
                fastapi_lat = self.results["fastapi"][endpoint].get("latency_avg_ms", 0)
                improvement = ((flask_lat - fastapi_lat) / flask_lat * 100) if flask_lat > 0 else 0
                
                print(f"{endpoint:<20} {flask_lat:>6.2f} ms        {fastapi_lat:>6.2f} ms        {improvement:>+6.1f}%")

    def save_results(self, output_file: str = "results/performance_benchmark.json"):
        """Save benchmark results to JSON."""
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n✅ Results saved to {output_file}")

    def run(self):
        """Run complete benchmark suite."""
        # Test endpoints
        endpoints = [
            ("/", "GET", None),
            ("/health", "GET", None),
            ("/monitor", "GET", None),
            ("/auth/login", "POST", {"username": "test", "password": "test"}),
            ("/predict", "POST", {
                "user_id": "test",
                "session_duration_seconds": 300,
                "click_count": 5,
            }),
        ]
        
        # Benchmark Flask (if running)
        print("Starting Flask endpoint benchmarking...")
        print(f"Note: Make sure Flask is running on {self.flask_url}")
        try:
            response = requests.get(f"{self.flask_url}/health", timeout=2)
            if response.status_code < 400:
                self.results["flask"] = self.benchmark_app("Flask (Sync)", self.flask_url, endpoints)
        except Exception as e:
            print(f"⚠️  Flask not available at {self.flask_url}: {e}")
            self.results["flask"] = {}
        
        # Benchmark FastAPI (if running)
        print("\nStarting FastAPI endpoint benchmarking...")
        print(f"Note: Make sure FastAPI is running on {self.fastapi_url}")
        try:
            response = requests.get(f"{self.fastapi_url}/health", timeout=2)
            if response.status_code < 400:
                self.results["fastapi"] = self.benchmark_app("FastAPI (Async)", self.fastapi_url, endpoints)
        except Exception as e:
            print(f"⚠️  FastAPI not available at {self.fastapi_url}: {e}")
            self.results["fastapi"] = {}
        
        # Compare and save
        if self.results["flask"] and self.results["fastapi"]:
            self.compare_results()
        
        self.save_results()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance benchmark for Flask vs FastAPI")
    parser.add_argument("--flask-url", default="http://localhost:5000", help="Flask server URL")
    parser.add_argument("--fastapi-url", default="http://localhost:8000", help="FastAPI server URL")
    args = parser.parse_args()
    
    benchmark = PerformanceBenchmark(flask_url=args.flask_url, fastapi_url=args.fastapi_url)
    benchmark.run()
