# 🛡️ Kubernetes Security

This project simulates a microservices infrastructure using **Kubernetes** and **Istio** to test and observe **network-layer security attacks** (e.g. DDoS). The goal is to explore service mesh capabilities (Istio) in securing, monitoring, and handling malicious or anomalous traffic in a cloud-native environment.

---

## 🚀 Overview

This lab includes:

- ✅ A Flask-based web app for simulating a microservice and logging request metadata.
- ✅ A containerized deployment using Docker and Kubernetes (via k3d).
- ✅ Istio setup for advanced observability and security.
- ✅ Traffic monitoring through `/monitor` endpoint.
- ✅ Simulation of DDoS-style attacks for observability and mitigation testing.

---

## 🧪 Tech Stack

| Tool            | Purpose                              |
|-----------------|--------------------------------------|
| Docker          | Containerizing the Flask app         |
| k3d             | Lightweight Kubernetes (K3s in Docker) |
| Istio           | Service mesh for observability & security |
| Flask           | Microservice for monitoring requests |
| Prometheus/Grafana | Metrics and dashboards  |


