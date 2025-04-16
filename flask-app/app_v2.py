from flask import Flask, request, jsonify
from datetime import datetime
import json
import time
import threading
import os
import requests

app = Flask(__name__)

log_file = "logs/requests.log"
metrics_file = "logs/metrics.json"

# Load or initialize metrics
if os.path.exists(metrics_file):
    with open(metrics_file, "r") as f:
        metrics = json.load(f)
else:
    metrics = {
        "total_requests": 0,
        "requests_per_ip": {},
        "methods": {},
        "paths": {},
        "user_agents": {},
    }

lock = threading.Lock()

def save_metrics():
    with lock:
        with open(metrics_file, "w") as f:
            json.dump(metrics, f, indent=4)

def update_metrics(ip, method, path, user_agent):
    metrics["total_requests"] += 1

    # Per-IP count
    metrics["requests_per_ip"].setdefault(ip, 0)
    metrics["requests_per_ip"][ip] += 1

    # Method frequency
    metrics["methods"].setdefault(method, 0)
    metrics["methods"][method] += 1

    # Path frequency
    metrics["paths"].setdefault(path, 0)
    metrics["paths"][path] += 1

    # User-Agent frequency
    metrics["user_agents"].setdefault(user_agent, 0)
    metrics["user_agents"][user_agent] += 1

    save_metrics()

def get_geoip(ip):
    try:
        response = requests.get(f"https://ipapi.co/{ip}/json/", timeout=2)
        if response.status_code == 200:
            data = response.json()
            return {
                "country": data.get("country_name"),
                "city": data.get("city"),
                "org": data.get("org")
            }
    except:
        pass
    return {}

@app.route("/")
def home():
    return "Flask Security App is Running!"

@app.route("/monitor")
def monitor():
    start_time = time.time()

    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    method = request.method
    path = request.path
    user_agent = request.headers.get("User-Agent", "unknown")
    headers = dict(request.headers)
    geo_info = get_geoip(ip)

    latency = round(time.time() - start_time, 5)

    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "method": method,
        "remote_addr": ip,
        "user_agent": user_agent,
        "path": path,
        "latency": latency,
        "headers": headers,
        "geo_info": geo_info,
    }

    with lock:
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    update_metrics(ip, method, path, user_agent)

    return jsonify({"status": "logged", "metrics": log_entry})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
