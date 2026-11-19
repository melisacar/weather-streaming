# Helm chart

Chart for the weather-streaming pipeline (Kafka, Schema Registry, MinIO, TimescaleDB, producer, consumer). Tested on Minikube.

## Prerequisites

- Minikube, kubectl, Helm
- Images loaded into the cluster (see [`k8s/README.md`](../k8s/README.md))
- `weather-secrets` created before install. It is not part of the chart so no credentials end up in git:

```
cp k8s/secrets.example.yml k8s/secrets.yml   # fill in real values
kubectl create namespace weather-streaming
kubectl apply -f k8s/secrets.yml
```

## Install

```
helm install weather-streaming helm/weather-streaming --namespace weather-streaming
```

Image tags and replica counts are set in `helm/weather-streaming/values.yaml` and can be overridden with `--set`, for example `--set replicas.producer=2`.

## Uninstall

```
helm uninstall weather-streaming --namespace weather-streaming
```