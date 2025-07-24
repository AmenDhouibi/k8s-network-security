# app_v8.py

from flask import Flask, request, jsonify, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from datetime import datetime
import time, threading, os, json
import redis

app = Flask(__name__)

# ── Redis Setup (rate-limiting) ───────────────────────────────────────────────
REDIS_HOST = os.environ.get('REDIS_SERVICE_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_SERVICE_PORT', 6379))
RATE_LIMIT = 100
WINDOW_SIZE = 60  # seconds

try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
except redis.exceptions.ConnectionError:
    REDIS_AVAILABLE = False
    print("[WARNING] Redis unavailable — Rate limiting disabled.")

# ── File paths ────────────────────────────────────────────────────────────────
LOG_FILE     = "logs/requests.log"
METRICS_FILE = "logs/metrics.json"

os.makedirs("logs", exist_ok=True)
lock = threading.Lock()

# ── Custom JSON metrics ───────────────────────────────────────────────────────
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

# ── Prometheus metrics ────────────────────────────────────────────────────────
GAUGE_TOTAL      = Gauge('flask_total_requests',      'Total HTTP requests (from JSON)')
GAUGE_BY_IP      = Gauge('flask_requests_by_ip',      'Requests per IP',           ['ip'])
GAUGE_BY_METHOD  = Gauge('flask_requests_by_method',  'Requests per method',       ['method'])
GAUGE_BY_PATH    = Gauge('flask_requests_by_path',    'Requests per path',         ['path'])

HTTP_COUNTER     = Counter(
    'http_requests_total',
    'Count of HTTP requests',
    ['method','endpoint','http_status']
)
LATENCY_HIST     = Histogram(
    'http_request_duration_seconds',
    'Request latency in seconds',
    ['method','endpoint']
)
IN_PROGRESS      = Gauge(
    'inprogress_requests',
    'Number of requests in progress'
)

# ── Rate Limiting before request ──────────────────────────────────────────────
@app.before_request
def before_request():
    xff = request.headers.get("X-Forwarded-For", request.remote_addr)
    ip = xff.split(',')[0].strip()

    # Rate limiting via Redis
    if REDIS_AVAILABLE:
        key = f"ratelimit:{ip}"
        count = redis_client.get(key)
        if count is None:
            # Pas de clé -> set à 1 avec expiration
            redis_client.set(key, 1, ex=WINDOW_SIZE)
            count = 1
        else:
            # Clé existe -> incrémenter
            count = int(count) + 1
            redis_client.incr(key)

        # Après incrémentation, si on dépasse la limite, bloquer
        if count > RATE_LIMIT:
            return jsonify({"error": "Too many requests"}), 429

    request._start = time.time()
    IN_PROGRESS.inc()

# ── Logging + Prometheus after request ────────────────────────────────────────
@app.after_request
def after_request(response):
    rt = time.time() - request._start
    m  = request.method
    e  = request.path
    s  = response.status_code

    HTTP_COUNTER.labels(method=m, endpoint=e, http_status=s).inc()
    LATENCY_HIST.labels(method=m, endpoint=e).observe(rt)
    IN_PROGRESS.dec()

    xff = request.headers.get("X-Forwarded-For", request.remote_addr)
    ip = xff.split(',')[0].strip()

    update_custom(ip, m, e)

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
    return "Flask Security App v8 with Redis DDoS Mitigation is Running!"

@app.route("/monitor")
def monitor():
    return jsonify({"status":"logged", "custom_metrics": custom})

@app.route("/metrics")
def metrics():
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

@app.route("/ip")
def show_ip():
    xff = request.headers.get("X-Forwarded-For", request.remote_addr)
    ip = xff.split(',')[0].strip()
    return jsonify({"ip": ip})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
