from kafka import KafkaProducer
import json
import requests
import time
import os
from prometheus_client import start_http_server, Counter

start_http_server(8000)
WEATHER_REQUESTS = Counter('weather_requests', 'API request count')
MESSAGES_SENT = Counter('producer_messages_sent_total', 'Total messages sent to Kafka')

producer = KafkaProducer(
    bootstrap_servers=os.getenv('KAFKA_BROKERS', 'kafka:9092'), # Container DNS
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

topic = 'weather-data'

def fetch_weather_data():
    WEATHER_REQUESTS.inc()
    url = "https://api.weather.gov/gridpoints/LOX/150,48/forecast"
    headers = {"User-Agent": "myweatherapp.com"}
    response = requests.get(url, headers=headers)
    data = response.json()
    return data["properties"]["periods"]

while True:
    weather_periods = fetch_weather_data()
    for item in weather_periods:
        producer.send(topic, item)
        MESSAGES_SENT.inc()
        print(f"Sent: {item}")
        time.sleep(5)
    time.sleep(300)
