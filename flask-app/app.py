from flask import Flask, request, jsonify
import json
import os
import time

app = Flask(__name__)

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "requests.log")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

@app.route('/')
def index():
    return "Welcome to the Kubernetes Security Monitoring App!"

@app.route('/monitor', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def monitor():
    log = {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
        "method": request.method,
        "remote_addr": request.remote_addr,
        "user_agent": request.user_agent.string,
        "path": request.path,
        "headers": dict(request.headers),
    }

    # Print to console
    print(f"[{log['timestamp']}] {log['remote_addr']} -> {log['method']} {log['path']}")

    # Save log to file
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log) + "\n")

    return jsonify(log)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
