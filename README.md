# weather-streaming

A production-grade real-time data streaming pipeline that ingests weather forecast data from the [National Weather Service API](weather.gov), publishes it to Apache Kafka, and exposes full observability through Prometheus and Grafana. Built to demonstrate professional data engineering patterns including event-driven architecture, containerized microservices, and metrics-driven monitoring.

---

## Architecture

```bash
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Weather.gov API │────▶│   Producer   │────▶│  Apache Kafka   │
│  (NWS Forecast) │     │  (Python)    │     │  (KRaft mode)   │
└─────────────────┘     └──────────────┘     └────────┬────────┘
                                                       │
                                              ┌────────▼────────┐
                                              │    Consumer      │
                                              │    (Python)      │
                                              └─────────────────┘

Observability layer:
┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│ JMX Exporter │────▶│             │     │             │
│ Node Exporter│────▶│ Prometheus  │────▶│   Grafana   │
│ cAdvisor     │────▶│             │     │             │
│ Producer     │────▶│             │     │             │
│ Consumer     │────▶│             │     │             │
└──────────────┘     └─────────────┘     └─────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Message Broker | Apache Kafka 7.6 (KRaft) | Event streaming without Zookeeper |
| Producer | Python + kafka-python | Fetches API data, publishes to Kafka |
| Consumer | Python + kafka-python | Reads messages from Kafka topic |
| Metrics | Prometheus | Scrapes and stores metrics from all services |
| Dashboards | Grafana 9.5 | Visualizes pipeline health and performance |
| Broker Metrics | JMX Exporter | Exposes Kafka internal JMX metrics to Prometheus |
| Host Metrics | Node Exporter | CPU, memory, disk of the host machine |
| Container Metrics | cAdvisor | Per-container resource usage |
| Broker UI | Kafka UI | Inspect topics, partitions, consumer groups |
| Config | python-dotenv | Environment-based configuration |
| Orchestration | Docker Compose | Local multi-container setup |

---

## Project Structure

```bash
weather-streaming/
  src/
    producer/
      producer.py          # fetches weather forecasts, publishes to Kafka topic
    consumer/
      consumer.py          # consumes messages from Kafka, prints to stdout
  setup/
    topics.py              # creates Kafka topics programmatically via admin client
  monitoring/
    dashboards/
      kafka_grafana.json   # full Grafana dashboard definition (17 panels)
    provisioning/
      datasources/
        prometheus.yml     # auto-configures Prometheus as Grafana datasource
      dashboards/
        dashboard.yml      # tells Grafana where to load dashboard JSONs from
    jmx_config.yml         # JMX exporter configuration for Kafka broker metrics
    prometheus.yml         # Prometheus scrape targets configuration
  Dockerfile               # producer container image
  Dockerfile.consumer      # consumer container image
  docker-compose.yml       # full stack orchestration
  requirements.txt         # Python dependencies
  .env.example             # all required environment variables with descriptions
```

---

## What Each Component Does

### Producer (`src/producer/producer.py`)

Fetches 7-day weather forecast data from the National Weather Service API every 5 minutes. Each forecast period (day/night slot) is serialized as JSON and published as a separate Kafka message. Exposes a Prometheus `/metrics` endpoint on port 8000 tracking request counts and messages sent.

### Consumer (`src/consumer/consumer.py`)

Reads messages from the `weather-data` Kafka topic as part of the `weather-group` consumer group. Deserializes JSON payloads and prints forecast data to stdout. Exposes a Prometheus `/metrics` endpoint on port 8001 tracking messages consumed.

### Kafka (KRaft mode)

Runs without Zookeeper using KRaft consensus. Single broker setup with 1 partition and replication factor 1. Topic is created programmatically via `setup/topics.py` using the Kafka admin client — auto topic creation is disabled by default in KRaft mode.

### Observability Stack

- **JMX Exporter** — runs as a Java agent inside the Kafka container, exposes broker internals (bytes in/out per topic, partition counts, ISR) to Prometheus
- **Node Exporter** — exposes host machine CPU, memory, and disk metrics
- **cAdvisor** — exposes per-container CPU, memory, and network I/O metrics
- **Prometheus** — scrapes all five targets every 15 seconds
- **Grafana** — auto-provisioned on startup with Prometheus datasource and full dashboard, no manual import needed

### Grafana Dashboard (17 panels)

| Panel | What it shows |
|---|---|
| Producer Rate | Messages/sec being published to Kafka |
| Consumer Rate | Messages/sec being consumed |
| Producer vs Consumer Total | Cumulative comparison — reveals consumer lag |
| Kafka Broker Health | Broker up/down status (1 or 0) |
| Weather API Requests | Rate of outbound API calls |
| Producer CPU / Memory | Process-level resource usage of producer |
| Consumer CPU / Memory | Process-level resource usage of consumer |
| Host CPU / Memory / Disk | Underlying machine resource usage |
| Kafka Bytes In / Out | Per-topic throughput from JMX |
| Container CPU / Memory / Network | Container-level metrics from cAdvisor |

---

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Setup

1. Clone the repo

```
git clone https://github.com/melisacar/weather-streaming.git
cd weather-streaming
```

2. Create your env file

```
cp .env.example .env
```

3. Start the stack

```
docker compose up --build
```

4. Verify everything is running

```
docker compose ps
```

All 8 services should be up: kafka, weather-production, weather-consumer, kafka-ui, prometheus, grafana, node-exporter, cadvisor.

---

## Services

| Service | URL | Credentials |
|---|---|---|
| Kafka UI | http://localhost:8080 | — |
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | — |
| Producer metrics | http://localhost:8000/metrics | — |
| Consumer metrics | http://localhost:8001/metrics | — |
| cAdvisor | http://localhost:8085 | — |
| Node Exporter | http://localhost:9100/metrics | — |

---

## Data Source

The producer fetches from the [National Weather Service API](https://www.weather.gov) — a free, no-auth-required API maintained by NOAA. It returns 7-day forecasts broken into day/night periods for a given grid point.

Example Kafka message:

```json
{
  "name": "Today",
  "startTime": "2026-04-29T06:00:00-07:00",
  "endTime": "2026-04-29T18:00:00-07:00",
  "isDaytime": true,
  "temperature": 72,
  "temperatureUnit": "F",
  "windSpeed": "5 to 10 mph",
  "windDirection": "W",
  "shortForecast": "Sunny",
  "detailedForecast": "Sunny. High near 72."
}
```

## How to Use Your Own Location

The API uses a grid system. Follow these steps to get your coordinates.

### Step 1 — Look up your grid point

```bash
curl https://api.weather.gov/points/{latitude},{longitude}
```

Example for Beverly Hills, CA:

```bash
curl https://api.weather.gov/points/34.0947,-118.4017
```

From the response grab:

```json
"gridId": "LOX",
"gridX": 150,
"gridY": 48
```

### Step 2 — Build your forecast URL

```bash
https://api.weather.gov/gridpoints/{gridId}/{gridX},{gridY}/forecast
```

### Step 3 — Set it in your .env

```bash
WEATHER_API_URL=https://api.weather.gov/gridpoints/LOX/150,48/forecast
```

Note: This API only covers the United States.

---

## Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Description | Default |
|---|---|---|
| KAFKA_BROKERS | Kafka broker address | kafka:9092 |
| KAFKA_TOPIC | Topic name | weather-data |
| GROUP_ID | Consumer group ID | weather-group |
| PRODUCER_PORT | Producer metrics port | 8000 |
| CONSUMER_PORT | Consumer metrics port | 8001 |
| CLUSTER_ID | Kafka KRaft cluster ID | — |
| WEATHER_API_URL | NWS forecast endpoint | LOX/150,48 |
| GF_SECURITY_ADMIN_USER | Grafana admin username | admin |
| GF_SECURITY_ADMIN_PASSWORD | Grafana admin password | admin |

---

## Roadmap

### Done

- [x] Kafka producer fetching from Weather.gov API
- [x] Kafka consumer reading and printing messages
- [x] Apache Kafka in KRaft mode (no Zookeeper)
- [x] Programmatic topic creation via admin client
- [x] Prometheus metrics exposed from producer and consumer
- [x] JMX exporter for Kafka broker internals
- [x] Node Exporter for host-level metrics
- [x] cAdvisor for container-level metrics
- [x] Grafana dashboard with 17 panels auto-provisioned on startup
- [x] Environment-based configuration with .env and python-dotenv

### In Progress

- [ ] Error handling — API timeout, Kafka broker unavailable scenarios
- [ ] Retry mechanism with exponential backoff (tenacity)
- [ ] Dead Letter Queue (DLQ) for failed messages
- [ ] Idempotent producer and consumer to prevent duplicate processing
- [ ] JSON Schema validation for message format
- [ ] Consumer lag panel in Grafana
- [ ] API error rate panel in Grafana

### Planned

- [ ] pytest unit and integration tests with testcontainers
- [ ] GitHub Actions CI/CD pipeline (lint + test + build)
- [ ] MinIO as S3-compatible data lake (raw message storage)
- [ ] TimescaleDB for time-series weather data storage
- [ ] PySpark Structured Streaming for windowed aggregations
- [ ] Avro schema + Confluent Schema Registry
- [ ] Structured JSON logging with python-json-logger

---

## Notes

- Kafka runs in KRaft mode — no Zookeeper container needed
- Topic is not auto-created; run `setup/topics.py` before starting producer or it will fail
- Grafana dashboard and datasource are provisioned automatically — `docker compose down -v` won't lose them
- Weather.gov API is free, has no rate limits documented, and requires no API key
- To generate a fresh Kafka Cluster ID:

```
python -c "import uuid, base64; print(base64.b64encode(uuid.uuid4().bytes).decode())"
```

## Contributing

1. Fork the repo
2. Create your branch

```
git checkout -b feat/your-feature
```

3. Commit using conventional commits

```
feat:     new feature
fix:      bug fix
refactor: code change that is not a fix or feature
chore:    build, config, dependencies
docs:     documentation only
```

4. Push and open a pull request