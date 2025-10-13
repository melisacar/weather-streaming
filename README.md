# weather-streaming

weather.gov

## 1. Get Grid Coordinates (Using Postman)

**Request**:  

```json
GET https://api.weather.gov/points/{latitude},{longitude}
```

```json
{
    "@context": [
        "https://geojson.org/geojson-ld/geojson-context.jsonld",
        {
            "@version": "1.1",
            "wx": "https://api.weather.gov/ontology#",
            "s": "https://schema.org/",
            "geo": "http://www.opengis.net/ont/geosparql#",
            "unit": "http://codes.wmo.int/common/unit/",
            "@vocab": "https://api.weather.gov/ontology#",
            "geometry": {
                "@id": "s:GeoCoordinates",
                "@type": "geo:wktLiteral"
            },
            "city": "s:addressLocality",
            "state": "s:addressRegion",
            "distance": {
                "@id": "s:Distance",
                "@type": "s:QuantitativeValue"
            },
            "bearing": {
                "@type": "s:QuantitativeValue"
            },
            "value": {
                "@id": "s:value"
            },
            "unitCode": {
                "@id": "s:unitCode",
                "@type": "@id"
            },
            "forecastOffice": {
                "@type": "@id"
            },
            "forecastGridData": {
                "@type": "@id"
            },
            "publicZone": {
                "@type": "@id"
            },
            "county": {
                "@type": "@id"
            }
        }
    ],
    "id": "https://api.weather.gov/points/34.0947,-118.4017",
    "type": "Feature",
    "geometry": {
        "type": "Point",
        "coordinates": [
            -118.4017,
            34.0947
        ]
    },
    "properties": {
        "@id": "https://api.weather.gov/points/34.0947,-118.4017",
        "@type": "wx:Point",
        "cwa": "LOX",
        "forecastOffice": "https://api.weather.gov/offices/LOX",
        "gridId": "LOX",
        "gridX": 150,
        "gridY": 48,
        "forecast": "https://api.weather.gov/gridpoints/LOX/150,48/forecast",
        "forecastHourly": "https://api.weather.gov/gridpoints/LOX/150,48/forecast/hourly",
        "forecastGridData": "https://api.weather.gov/gridpoints/LOX/150,48",
        "observationStations": "https://api.weather.gov/gridpoints/LOX/150,48/stations",
        "relativeLocation": {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    -118.402437,
                    34.07923
                ]
            },
            "properties": {
                "city": "Beverly Hills",
                "state": "CA",
                "distance": {
                    "unitCode": "wmoUnit:m",
                    "value": 1721.5263548236
                },
                "bearing": {
                    "unitCode": "wmoUnit:degree_(angle)",
                    "value": 2
                }
            }
        },
        "forecastZone": "https://api.weather.gov/zones/forecast/CAZ368",
        "county": "https://api.weather.gov/zones/county/CAC037",
        "fireWeatherZone": "https://api.weather.gov/zones/fire/CAZ368",
        "timeZone": "America/Los_Angeles",
        "radarStation": "KSOX"
    }
}
```



## Generating Cluster_ID for Kafka Service

```py
python -c "import uuid, base64; print(base64.b64encode(uuid.uuid4().bytes).decode())"
```


## Generating Topic manually

Kafka'da "auto.create.topics.enable" özelliğinin kapalı olması olabilir. Bu ayar, KRaft (yani Zookeeper'sız Kafka) modunda default olarak false (kapalı) gelir. Yani:

Eğer topic mevcut değilse, Kafka otomatik olarak onu oluşturmaz.

---

## jmx_prometheus_javaagent.jar

jmx jar dosyası indirildi. montiroing klasoru icine kondu.

---

## 📊 Grafana Dashboard for Weather Kafka Pipeline

This project includes a sample **Grafana dashboard JSON** that visualizes the metrics collected from the Kafka-based weather data pipeline.  
The dashboard connects to **Prometheus**, which scrapes metrics from the following services:

- **Kafka Broker (via JMX Exporter)**
- **Weather Producer Service** (`/metrics` at port 8000)
- **Weather Consumer Service** (`/metrics` at port 8001)

### Dashboard Features

The dashboard provides the following panels:

1. **Producer Messages Sent Rate** – Monitors the rate of messages sent to Kafka.  
2. **Consumer Messages Consumed Rate** – Monitors the rate of messages consumed from Kafka.  
3. **Producer vs Consumer (Total)** – Compares cumulative messages sent and consumed.  
4. **Kafka Broker Health** – Displays the broker’s status (up/down) from Prometheus.  
5. **Weather API Requests Total** – Tracks the total number of API requests handled by the producer.  
6. **Producer CPU Usage** – Shows CPU utilization of the producer container.  
7. **Producer Memory Usage** – Shows memory utilization of the producer container.  
8. **Consumer CPU Usage** – Shows CPU utilization of the consumer container.  
9. **Consumer Memory Usage** – Shows memory utilization of the consumer container.  

### Importing the Dashboard

To import the dashboard into Grafana:

1. Open Grafana in your browser (`http://localhost:3000` by default).  
2. Go to **Dashboards → Import**.  
3. Copy-paste the JSON below or upload it as a `.json` file.  

### Dashboard JSON

```json
{
  "annotations": {
    "list": []
  },
  "panels": [
    {
      "type": "timeseries",
      "title": "Producer Messages Sent Rate",
      "targets": [
        {
          "expr": "rate(producer_messages_sent_total[1m])",
          "legendFormat": "Producer",
          "refId": "A"
        }
      ],
      "gridPos": { "x": 0, "y": 0, "w": 12, "h": 8 }
    },
    {
      "type": "timeseries",
      "title": "Consumer Messages Consumed Rate",
      "targets": [
        {
          "expr": "rate(consumer_messages_consumed_total[1m])",
          "legendFormat": "Consumer",
          "refId": "A"
        }
      ],
      "gridPos": { "x": 12, "y": 0, "w": 12, "h": 8 }
    },
    {
      "type": "timeseries",
      "title": "Producer vs Consumer (Total)",
      "targets": [
        {
          "expr": "producer_messages_sent_total",
          "legendFormat": "Producer Total",
          "refId": "A"
        },
        {
          "expr": "consumer_messages_consumed_total",
          "legendFormat": "Consumer Total",
          "refId": "B"
        }
      ],
      "gridPos": { "x": 0, "y": 8, "w": 24, "h": 8 }
    },
    {
      "type": "stat",
      "title": "Kafka Broker Health",
      "targets": [
        {
          "expr": "up{job=\"kafka\"}",
          "legendFormat": "Kafka Broker",
          "refId": "A"
        }
      ],
      "gridPos": { "x": 0, "y": 16, "w": 6, "h": 4 }
    },
    {
      "type": "timeseries",
      "title": "Weather API Requests Total",
      "targets": [
        {
          "expr": "weather_requests_total",
          "legendFormat": "API Requests",
          "refId": "A"
        }
      ],
      "gridPos": { "x": 6, "y": 16, "w": 18, "h": 6 }
    },
    {
      "type": "timeseries",
      "title": "Producer CPU Usage",
      "targets": [
        {
          "expr": "rate(process_cpu_seconds_total{instance=\"weather-production:8000\"}[1m])",
          "legendFormat": "Producer CPU",
          "refId": "A"
        }
      ],
      "gridPos": { "x": 0, "y": 22, "w": 12, "h": 6 }
    },
    {
      "type": "timeseries",
      "title": "Producer Memory Usage",
      "targets": [
        {
          "expr": "process_resident_memory_bytes{instance=\"weather-production:8000\"}",
          "legendFormat": "Producer Memory",
          "refId": "A"
        }
      ],
      "gridPos": { "x": 12, "y": 22, "w": 12, "h": 6 }
    },
    {
      "type": "timeseries",
      "title": "Consumer CPU Usage",
      "targets": [
        {
          "expr": "rate(process_cpu_seconds_total{instance=\"weather-consumer:8001\"}[1m])",
          "legendFormat": "Consumer CPU",
          "refId": "A"
        }
      ],
      "gridPos": { "x": 0, "y": 28, "w": 12, "h": 6 }
    },
    {
      "type": "timeseries",
      "title": "Consumer Memory Usage",
      "targets": [
        {
          "expr": "process_resident_memory_bytes{instance=\"weather-consumer:8001\"}",
          "legendFormat": "Consumer Memory",
          "refId": "A"
        }
      ],
      "gridPos": { "x": 12, "y": 28, "w": 12, "h": 6 }
    }
  ],
  "schemaVersion": 37,
  "title": "Weather Kafka Pipeline",
  "version": 2
}

---

#### Add container metrics
Cadvisor