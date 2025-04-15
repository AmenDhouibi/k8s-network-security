from flask import Flask, request, jsonify
import time

app = Flask(__name__)

@app.route('/')
def index():
    return "Welcome to the Kubernetes Security Monitoring App!"

@app.route('/monitor', methods=['GET', 'POST'])
def monitor():
    log = {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
        "method": request.method,
        "remote_addr": request.remote_addr,
        "user_agent": request.user_agent.string,
        "headers": dict(request.headers)
    }
    print(f"Request Log: {log}")
    return jsonify(log)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
