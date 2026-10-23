# Kubernetes manifests

Tested on Minikube. Everything runs in the `weather-streaming` namespace.

## Prerequisites

- Docker, Minikube, kubectl

## 1. Start the cluster and load images

The manifests use `imagePullPolicy: Never`, so all images must exist inside the cluster.

```
minikube start --driver=docker
minikube image build -t weather-producer:latest -f Dockerfile .
minikube image build -t weather-consumer:latest -f Dockerfile.consumer .
minikube image load confluentinc/cp-kafka:7.6.0
minikube image load confluentinc/cp-schema-registry:7.6.0
minikube image load minio/minio:latest
minikube image load timescale/timescaledb:latest-pg16
```

## 2. Create secrets

`secrets.yml` is gitignored. Copy the example and fill in real values.

```
cp k8s/secrets.example.yml k8s/secrets.yml
```

## 3. Deploy

```
kubectl apply -f k8s/namespace.yml -f k8s/configmap.yml -f k8s/secrets.yml
kubectl apply -f k8s/timescaledb/init-configmap.yml
kubectl apply -f k8s/kafka/ -f k8s/minio/ -f k8s/timescaledb/ -f k8s/schema-registry/
kubectl apply -f k8s/producer/ -f k8s/consumer/
kubectl get pods -n weather-streaming
```

## Known limitations

- TimescaleDB has no persistent volume, so data is lost when the pod is recreated.
- Prometheus, Grafana, Superset and the Spark job are not part of the manifests yet.