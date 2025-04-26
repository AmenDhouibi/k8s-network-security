# app_v4.py

from flask import Flask, request, jsonify, Response
from datetime import datetime
import json, time, threading, os
from prometheus_client import Counter, Gauge, Histogram, Summary, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

log_file = "logs/requests.log"
metrics_file = "logs/metrics.json"

# ---- Custom Metrics
TOTAL_REQUESTS = Gauge('flask_total_requests', 'Total HTTP requests received')
REQUESTS_BY_IP = Gauge('flask_requests_by_ip', 'Number of requests per IP', ['ip'])
REQUESTS_BY_METHOD = Gauge('flask_requests_by_method', 'Number of requests per HTTP method', ['method'])
REQUESTS_BY_PATH = Gauge('flask_requests_by_path', 'Number of requests per URL path', ['path'])

# ---- Standard Prometheus_client metrics (for Grafana dashboards) ----
HTTP_REQUESTS_TOTAL = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'Histogram of request processing time', ['method', 'endpoint'])
IN_PROGRESS = Gauge('inprogress_requests', 'Number of in-progress requests')

# ---- Load or initialize JSON metrics ----
if os.path.exists(metrics_file):
    with open(metrics_file) as f:
        metrics = json.load(f)
else:
    metrics = {
        "total_requests": 0,
        "requests_per_ip": {},
        "methods": {},
        "paths": {},
    }

lock = threading.Lock()

def save_metrics():
    with lock:
        with open(metrics_file, "w") as f:
            json.dump(metrics, f, indent=4)

def update_custom_metrics(ip, method, path):
    metrics["total_requests"] += 1
    metrics["requests_per_ip"].setdefault(ip, 0)
    metrics["requests_per_ip"][ip] += 1
    metrics["methods"].setdefault(method, 0)
    metrics["methods"][method] += 1
    metrics["paths"].setdefault(path, 0)
    metrics["paths"][path] += 1
    save_metrics()

@app.before_request
def before_request():
    request.start_time = time.time()
    IN_PROGRESS.inc()

@app.after_request
def after_request(response):
    request_latency = time.time() - request.start_time
    method = request.method
    endpoint = request.path
    status = response.status_code
    # Update Standard metrics
    HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, http_status=status).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(request_latency)
    IN_PROGRESS.dec()
    return response

@app.route("/metrics")
def metrics_endpoint():
    # Update Custom Gauges from saved JSON
    with lock:
        with open(metrics_file) as f:
            data = json.load(f)

    TOTAL_REQUESTS.set(data.get("total_requests", 0))

    for ip, count in data.get("requests_per_ip", {}).items():
        REQUESTS_BY_IP.labels(ip=ip).set(count)

    for method, count in data.get("methods", {}).items():
        REQUESTS_BY_METHOD.labels(method=method).set(count)

    for path, count in data.get("paths", {}).items():
        REQUESTS_BY_PATH.labels(path=path).set(count)

    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route("/")
def home():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    method = request.method
    path = request.path
    update_custom_metrics(ip, method, path)
    return "Flask Security App v4 is Running!"

@app.route("/monitor")
def monitor():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    method = request.method
    path = request.path
    update_custom_metrics(ip, method, path)
    return jsonify({"status": "logged", "metrics": metrics})

if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    app.run(host="0.0.0.0", port=5000)
