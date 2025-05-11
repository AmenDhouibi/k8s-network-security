#!/bin/bash

# Namespace where Prometheus stack is deployed
NAMESPACE="monitoring"

echo "Starting port-forward for Prometheus on :9090..."
kubectl -n $NAMESPACE port-forward svc/cluster-metrics-kube-prome-prometheus 9090:9090 > /dev/null 2>&1 &

echo "Starting port-forward for Alertmanager on :9093..."
kubectl -n $NAMESPACE port-forward svc/cluster-metrics-kube-prome-alertmanager 9093:9093 > /dev/null 2>&1 &

echo "Starting port-forward for Grafana on :3000..."
kubectl -n $NAMESPACE port-forward svc/cluster-metrics-grafana 3000:80 > /dev/null 2>&1 &

echo "All services are being forwarded (Prometheus:9090, Alertmanager:9093, Grafana:3000)."
