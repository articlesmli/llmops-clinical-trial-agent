import time
import requests

# FastAPI local endpoint
URL = "http://127.0.0.1:8000/"
METRICS_URL = "http://127.0.0.1:8000/metrics"

print("Starting traffic generator for Prometheus metrics... (Press Ctrl+C to stop)")

for i in range(1, 51):
    try:
        # Hit the root/docs endpoint
        response = requests.get(URL)
        print(f"Request {i}: Status {response.status_code}")
        
        # Periodically check metrics endpoint
        if i % 10 == 0:
            metrics_res = requests.get(METRICS_URL)
            print(f"--- Fetched /metrics (Status {metrics_res.status_code}) ---")
            
    except requests.exceptions.ConnectionError:
        print(f"Request {i}: Failed to connect. Is FastAPI running on port 8000?")
        
    time.sleep(1) # Wait 1 second between requests

print("Traffic generation complete!")
