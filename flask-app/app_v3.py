# app_v3.py

from flask import Flask, request, jsonify, Response
from datetime import datetime
import json, time, threading, os, requests
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

log_file = "logs/requests.log"
metrics_file = "logs/metrics.json"

# — Prometheus gauges —
TOTAL_REQUESTS = Gauge('flask_total_requests', 'Total HTTP requests')
REQUESTS_BY_IP   = Gauge('flask_requests_by_ip',   'Requests per IP',           ['ip'])
REQUESTS_BY_METHOD = Gauge('flask_requests_by_method', 'Requests per HTTP method', ['method'])
REQUESTS_BY_PATH = Gauge('flask_requests_by_path', 'Requests per path',         ['path'])

# load or initialize metrics dict
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

def update_metrics(ip, method, path):
    metrics["total_requests"] += 1
    metrics["requests_per_ip"].setdefault(ip, 0)
    metrics["requests_per_ip"][ip] += 1
    metrics["methods"].setdefault(method, 0)
    metrics["methods"][method] += 1
    metrics["paths"].setdefault(path, 0)
    metrics["paths"][path] += 1
    save_metrics()

@app.route("/metrics")
def metrics_endpoint():
    # Refresh gauges from JSON file
    with lock:
        with open(metrics_file) as f:
            data = json.load(f)
    TOTAL_REQUESTS.set(data.get("total_requests", 0))
    # Clear old label values (optional; gauges overwrite same label)
    for ip, v in data.get("requests_per_ip", {}).items():
        REQUESTS_BY_IP.labels(ip=ip).set(v)
    for m, v in data.get("methods", {}).items():
        REQUESTS_BY_METHOD.labels(method=m).set(v)
    for p, v in data.get("paths", {}).items():
        REQUESTS_BY_PATH.labels(path=p).set(v)
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route("/")
def home():
    start = time.time()
    ip    = request.headers.get("X-Forwarded-For", request.remote_addr)
    method= request.method
    path  = request.path
    update_metrics(ip, method, path)
    return "Flask Security App is Running!"

@app.route("/monitor")
def monitor():
    start = time.time()
    ip    = request.headers.get("X-Forwarded-For", request.remote_addr)
    method= request.method
    path  = request.path
    update_metrics(ip, method, path)
    return jsonify({"status": "logged", "metrics": metrics})

if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    app.run(host="0.0.0.0", port=5000)
