import json
import os
import time

import requests
from dotenv import load_dotenv
from jsonschema import ValidationError, validate
from kafka import KafkaProducer
from kafka.errors import KafkaError
from prometheus_client import Counter, start_http_server
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.producer.schema import WEATHER_SCHEMA

load_dotenv()

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "kafka:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "weather-data")
PRODUCER_PORT = int(os.getenv("PRODUCER_PORT", "8000"))
WEATHER_API_URL = os.getenv(
    "WEATHER_API_URL", "https://api.weather.gov/gridpoints/LOX/150,48/forecast"
)
WEATHER_API_USER_AGENT = os.getenv("WEATHER_API_USER_AGENT", "myweatherapp.com")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "10"))
FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", "300"))
SEND_INTERVAL = int(os.getenv("SEND_INTERVAL", "5"))

start_http_server(PRODUCER_PORT)

WEATHER_REQUESTS = Counter("weather_requests_total", "Total API requests")
MESSAGES_SENT = Counter("producer_messages_sent_total", "Total messages sent to Kafka")
WEATHER_REQUEST_ERRORS = Counter("weather_request_errors_total", "Failed API requests")
KAFKA_SEND_ERRORS = Counter("kafka_send_errors_total", "Failed Kafka send attempts")
VALIDATION_ERRORS = Counter(
    "producer_validation_errors_total", "Messages failed schema validation"
)


def create_producer():
    # retry connecting to Kafka broker on startup — broker may not be ready yet
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",  # wait for all replicas to acknowledge
                retries=5,  # retry failed sends up to 5 times
                retry_backoff_ms=500,  # wait 500ms between retries
                # enable_idempotence=True,    # not supported in kafka-python-ng on Python 3.9
            )
            print("Kafka producer connected.", flush=True)
            return producer
        except KafkaError as e:
            print(f"Kafka not ready, retrying in 5s: {e}", flush=True)
            time.sleep(5)


@retry(
    retry=retry_if_exception_type(
        (requests.exceptions.Timeout, requests.exceptions.ConnectionError)
    ),
    wait=wait_exponential(multiplier=1, min=2, max=30),  # 2s, 4s, 8s... up to 30s
    stop=stop_after_attempt(5),
)

def parse_wind_speed(wind_speed_str):
    # "5 to 15 mph" → 10.0
    # "15 mph" → 15.0
    import re
    numbers = re.findall(r'\d+', wind_speed_str or "0")
    if len(numbers) == 2:
        return (int(numbers[0]) + int(numbers[1])) / 2
    elif len(numbers) == 1:
        return float(numbers[0])
    return 0.0

def fetch_weather_data():
    WEATHER_REQUESTS.inc()
    headers = {"User-Agent": WEATHER_API_USER_AGENT}
    response = requests.get(WEATHER_API_URL, headers=headers, timeout=API_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    periods = data["properties"]["periods"]
    # add numeric wind speed to each period
    for period in periods:
        period["wind_speed_mph"] = parse_wind_speed(period.get("windSpeed", "0"))
    return periods


def send_message(producer, message):
    try:
        validate(instance=message, schema=WEATHER_SCHEMA)
    except ValidationError as e:
        VALIDATION_ERRORS.inc()
        print(f"Message validation error: {e.message}", flush=True)
        return  # skip invalid message, don't send to Kafka

    try:
        future = producer.send(TOPIC, message)
        future.get(timeout=10)  # block until send confirmed or timeout
        MESSAGES_SENT.inc()
        print(
            f"Sent: {message.get('name')} — {message.get('temperature')}°{message.get('temperatureUnit')}",
            flush=True,
        )
    except KafkaError as e:
        KAFKA_SEND_ERRORS.inc()
        print(f"Kafka send error: {e}", flush=True)

def main():
    producer = create_producer()

    while True:
        try:
            periods = fetch_weather_data()
            for item in periods:
                send_message(producer, item)
                time.sleep(SEND_INTERVAL)
        except Exception as e:
            WEATHER_REQUEST_ERRORS.inc()
            print(f"Failed to fetch weather data after retries: {e}", flush=True)
            print("Waiting 60s before next attempt...", flush=True)
            time.sleep(60)

        time.sleep(FETCH_INTERVAL)


if __name__ == "__main__":
    main()
