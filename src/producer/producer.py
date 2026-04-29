from kafka import KafkaProducer
import json
import requests
import time
import os
from prometheus_client import start_http_server, Counter
from dotenv import load_dotenv

load_dotenv()

KAFKA_BROKERS = os.getenv('KAFKA_BROKERS', 'kafka:9092')
TOPIC = os.getenv('KAFKA_TOPIC', 'weather-data')
PRODUCER_PORT = int(os.getenv('PRODUCER_PORT', '8000'))
WEATHER_API_URL = os.getenv('WEATHER_API_URL', 'https://api.weather.gov/gridpoints/LOX/150,48/forecast')
WEATHER_API_USER_AGENT = os.getenv('WEATHER_API_USER_AGENT', 'myweatherapp.com')

start_http_server(PRODUCER_PORT)
WEATHER_REQUESTS = Counter('weather_requests', 'API request count')
MESSAGES_SENT = Counter('producer_messages_sent_total', 'Total messages sent to Kafka')

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def fetch_weather_data():
    WEATHER_REQUESTS.inc()
    headers = {"User-Agent": WEATHER_API_USER_AGENT}
    response = requests.get(WEATHER_API_URL, headers=headers)
    data = response.json()
    return data["properties"]["periods"]

while True:
    weather_periods = fetch_weather_data()
    for item in weather_periods:
        producer.send(TOPIC, item)
        MESSAGES_SENT.inc()
        print(f"Sent: {item}")
        time.sleep(5)
    time.sleep(300)