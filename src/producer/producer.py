import json as json_lib
import logging
import os
import re
import time

import requests
from confluent_kafka import Producer as ConfluentProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import MessageField, SerializationContext
from dotenv import load_dotenv
from jsonschema import ValidationError, validate
from prometheus_client import Counter, start_http_server
from pythonjsonlogger import jsonlogger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.producer.schema import WEATHER_SCHEMA
from src.producer.schema_avro import WEATHER_AVRO_SCHEMA

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
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://schema-registry:8081")

start_http_server(PRODUCER_PORT)

logger = logging.getLogger("producer")
handler = logging.StreamHandler()
handler.setFormatter(
    jsonlogger.JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s")
)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

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
            schema_registry_client = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})
            avro_serializer = AvroSerializer(
                schema_registry_client,
                json_lib.dumps(WEATHER_AVRO_SCHEMA),
            )
            producer = ConfluentProducer({"bootstrap.servers": KAFKA_BROKERS})
            logger.info("Kafka producer connected")
            return producer, avro_serializer
        except Exception as e:
            logger.warning("Kafka not ready, retrying in 5s", extra={"error": str(e)})
            time.sleep(5)


def parse_wind_speed(wind_speed_str):
    # "5 to 15 mph" → 10.0, "15 mph" → 15.0
    numbers = re.findall(r"\d+", wind_speed_str or "0")
    if len(numbers) == 2:
        return (int(numbers[0]) + int(numbers[1])) / 2
    elif len(numbers) == 1:
        return float(numbers[0])
    return 0.0


@retry(
    retry=retry_if_exception_type(
        (requests.exceptions.Timeout, requests.exceptions.ConnectionError)
    ),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(5),
)
def fetch_weather_data():
    WEATHER_REQUESTS.inc()
    headers = {"User-Agent": WEATHER_API_USER_AGENT}
    response = requests.get(WEATHER_API_URL, headers=headers, timeout=API_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    periods = data["properties"]["periods"]
    for period in periods:
        period["wind_speed_mph"] = parse_wind_speed(period.get("windSpeed", "0"))
    return periods


def send_message(producer, avro_serializer, message):
    try:
        validate(instance=message, schema=WEATHER_SCHEMA)
    except ValidationError as e:
        VALIDATION_ERRORS.inc()
        logger.warning("Message validation failed", extra={"error": e.message})
        return

    try:
        producer.produce(
            topic=TOPIC,
            value=avro_serializer(
                message,
                SerializationContext(TOPIC, MessageField.VALUE),
            ),
        )
        producer.flush()
        MESSAGES_SENT.inc()
        logger.info(
            "Message sent",
            extra={
                "forecast_name": message.get("name"),
                "temperature": message.get("temperature"),
                "unit": message.get("temperatureUnit"),
            },
        )
    except Exception as e:
        KAFKA_SEND_ERRORS.inc()
        logger.error("Kafka send error", extra={"error": str(e)})


def main():
    producer, avro_serializer = create_producer()

    while True:
        try:
            periods = fetch_weather_data()
            for item in periods:
                send_message(producer, avro_serializer, item)
                time.sleep(SEND_INTERVAL)
        except Exception as e:
            WEATHER_REQUEST_ERRORS.inc()
            logger.error(
                "Failed to fetch weather data after retries, waiting 60s",
                extra={"error": str(e)},
            )
            time.sleep(60)

        time.sleep(FETCH_INTERVAL)


if __name__ == "__main__":
    main()