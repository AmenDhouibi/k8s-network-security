# app_v5.py

from flask import Flask, request, jsonify, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from datetime import datetime
import time, threading, os, json

app = Flask(__name__)

# ── File paths ────────────────────────────────────────────────────────────────
LOG_FILE     = "logs/requests.log"
METRICS_FILE = "logs/metrics.json"

os.makedirs("logs", exist_ok=True)
lock = threading.Lock()

# ── Custom JSON metrics (for your JSON/dashboard) ─────────────────────────────
if os.path.exists(METRICS_FILE):
    with open(METRICS_FILE) as f:
        custom = json.load(f)
else:
    custom = {
        "total_requests": 0,
        "requests_per_ip": {},
        "methods": {},
        "paths": {},
    }

def save_custom():
    with lock:
        with open(METRICS_FILE, "w") as f:
            json.dump(custom, f, indent=2)

def update_custom(ip, method, path):
    custom["total_requests"] += 1
    custom["requests_per_ip"].setdefault(ip, 0)
    custom["requests_per_ip"][ip] += 1
    custom["methods"].setdefault(method, 0)
    custom["methods"][method] += 1
    custom["paths"].setdefault(path, 0)
    custom["paths"][path] += 1
    save_custom()

# ── Prometheus client metrics ─────────────────────────────────────────────────
# Custom JSON gauges :
GAUGE_TOTAL      = Gauge('flask_total_requests',      'Total HTTP requests (from JSON)')
GAUGE_BY_IP      = Gauge('flask_requests_by_ip',      'Requests per IP',           ['ip'])
GAUGE_BY_METHOD  = Gauge('flask_requests_by_method',  'Requests per method',       ['method'])
GAUGE_BY_PATH    = Gauge('flask_requests_by_path',    'Requests per path',         ['path'])

# Standard counters & histograms for Grafana dashboards:
HTTP_COUNTER    = Counter(
    'http_requests_total',
    'Count of HTTP requests',
    ['method','endpoint','http_status']
)
LATENCY_HIST    = Histogram(
    'http_request_duration_seconds',
    'Request latency in seconds',
    ['method','endpoint']
)
IN_PROGRESS     = Gauge(
    'inprogress_requests',
    'Number of requests in progress'
)

# ── Request instrumentation ───────────────────────────────────────────────────
@app.before_request
def before_request():
    request._start = time.time()
    IN_PROGRESS.inc()

@app.after_request
def after_request(response):
    rt = time.time() - request._start
    m  = request.method
    e  = request.path
    s  = response.status_code

    # Prometheus metrics
    HTTP_COUNTER.labels(method=m, endpoint=e, http_status=s).inc()
    LATENCY_HIST.labels(method=m, endpoint=e).observe(rt)
    IN_PROGRESS.dec()

    # JSON store
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    update_custom(ip, m, e)

    # Optional: append to log file
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "method": m, "endpoint": e,
        "status": s, "latency": round(rt,5),
        "ip": ip
    }
    with lock:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")

    return response

# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return "Flask Security App v5 is Running!"

@app.route("/monitor")
def monitor():
    return jsonify({"status":"logged", "custom_metrics": custom})

@app.route("/metrics")
def metrics():
    # Refresh custom gauges
    with lock:
        with open(METRICS_FILE) as f:
            data = json.load(f)

    GAUGE_TOTAL.set(data.get("total_requests", 0))
    for ip,count in data.get("requests_per_ip", {}).items():
        GAUGE_BY_IP.labels(ip=ip).set(count)
    for m,count in data.get("methods", {}).items():
        GAUGE_BY_METHOD.labels(method=m).set(count)
    for p,count in data.get("paths", {}).items():
        GAUGE_BY_PATH.labels(path=p).set(count)

    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
