import json
import logging
import os
import time
from datetime import datetime, timezone

import boto3
import psycopg2
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from kafka import KafkaConsumer, KafkaProducer, TopicPartition
from kafka.errors import KafkaError
from prometheus_client import Counter, Gauge, start_http_server
from pythonjsonlogger import jsonlogger

load_dotenv()

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "kafka:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "weather-data")
GROUP_ID = os.getenv("GROUP_ID", "weather-group")
CONSUMER_PORT = int(os.getenv("CONSUMER_PORT", "8001"))
DLQ_TOPIC = os.getenv("DLQ_TOPIC", "weather-data.dlq")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "weather-raw")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
TIMESCALE_HOST = os.getenv("TIMESCALE_HOST", "timescaledb")
TIMESCALE_PORT = int(os.getenv("TIMESCALE_PORT", "5432"))
TIMESCALE_USER = os.getenv("TIMESCALE_USER", "weatheruser")
TIMESCALE_PASSWORD = os.getenv("TIMESCALE_PASSWORD", "weatherpass")
TIMESCALE_DB = os.getenv("TIMESCALE_DB", "weather")

start_http_server(CONSUMER_PORT)

logger = logging.getLogger("consumer")
handler = logging.StreamHandler()
handler.setFormatter(
    jsonlogger.JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s")
)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

MESSAGES_CONSUMED = Counter("consumer_messages_consumed_total", "Total messages consumed")
CONSUMER_ERRORS = Counter("consumer_errors_total", "Total consumer errors")
CONSUMER_LAG = Gauge("consumer_lag", "Consumer lag per partition", ["topic", "partition"])
DLQ_MESSAGES = Counter("consumer_dlq_messages_total", "Total messages sent to DLQ")
MINIO_WRITES = Counter("consumer_minio_writes_total", "Total messages written to MinIO")
MINIO_ERRORS = Counter("consumer_minio_errors_total", "Failed MinIO write attempts")
TIMESCALE_WRITES = Counter("consumer_timescale_writes_total", "Total rows written to TimescaleDB")
TIMESCALE_ERRORS = Counter("consumer_timescale_errors_total", "Failed TimescaleDB write attempts")


def create_consumer():
    while True:
        try:
            consumer = KafkaConsumer(
                TOPIC,
                bootstrap_servers=KAFKA_BROKERS,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                group_id=GROUP_ID,
                value_deserializer=lambda x: json.loads(x.decode("utf-8")),
            )
            logger.info("Kafka consumer connected")
            return consumer
        except KafkaError as e:
            logger.warning("Kafka not ready, retrying in 5s", extra={"error": str(e)})
            time.sleep(5)


def create_dlq_producer():
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            logger.info("DLQ producer connected")
            return producer
        except KafkaError as e:
            logger.warning("DLQ producer not ready, retrying in 5s", extra={"error": str(e)})
            time.sleep(5)


def send_to_dlq(dlq_producer, message, error):
    dlq_payload = {
        "original_message": message.value,
        "error": str(error),
        "topic": message.topic,
        "partition": message.partition,
        "offset": message.offset,
        "timestamp": message.timestamp,
    }
    try:
        future = dlq_producer.send(DLQ_TOPIC, dlq_payload)
        future.get(timeout=10)
        DLQ_MESSAGES.inc()
        logger.info("Message sent to DLQ", extra={"offset": message.offset, "error": str(error)})
    except Exception as e:
        logger.error("Failed to send to DLQ", extra={"error": str(e)})


def update_lag(consumer):
    try:
        partitions = consumer.partitions_for_topic(TOPIC)
        if partitions is None:
            return
        for p in partitions:
            tp = TopicPartition(TOPIC, p)
            end_offsets = consumer.end_offsets([tp])
            current_offset = consumer.position(tp)
            lag = end_offsets[tp] - current_offset
            CONSUMER_LAG.labels(topic=TOPIC, partition=p).set(lag)
    except Exception as e:
        logger.error("Lag calculation error", extra={"error": str(e)})


def process_message(message):
    data = message.value
    logger.info(
        "Message received",
        extra={
            "start_time": data["startTime"],
            "temperature": data["temperature"],
            "unit": data["temperatureUnit"],
            "forecast": data["shortForecast"],
        },
    )


def create_minio_client():
    return boto3.client(
        "s3",
        endpoint_url=f"http://{MINIO_ENDPOINT}",
        aws_access_key_id=MINIO_ROOT_USER,
        aws_secret_access_key=MINIO_ROOT_PASSWORD,
    )


def ensure_bucket(client):
    try:
        client.head_bucket(Bucket=MINIO_BUCKET)
    except ClientError:
        client.create_bucket(Bucket=MINIO_BUCKET)
        logger.info("Bucket created", extra={"bucket": MINIO_BUCKET})


def write_to_minio(client, message):
    now = datetime.now(timezone.utc)
    key = f"raw/{now.strftime('%Y/%m/%d/%H')}/{message.partition}-{message.offset}.json"
    try:
        client.put_object(
            Bucket=MINIO_BUCKET,
            Key=key,
            Body=json.dumps(message.value).encode("utf-8"),
            ContentType="application/json",
        )
        MINIO_WRITES.inc()
        logger.info("Written to MinIO", extra={"key": key})
    except Exception as e:
        MINIO_ERRORS.inc()
        logger.error("MinIO write error", extra={"error": str(e)})


def create_timescale_conn():
    while True:
        try:
            conn = psycopg2.connect(
                host=TIMESCALE_HOST,
                port=TIMESCALE_PORT,
                user=TIMESCALE_USER,
                password=TIMESCALE_PASSWORD,
                dbname=TIMESCALE_DB,
            )
            logger.info("TimescaleDB connected")
            return conn
        except Exception as e:
            logger.warning("TimescaleDB not ready, retrying in 5s", extra={"error": str(e)})
            time.sleep(5)


def calculate_wind_power(wind_speed_mph):
    wind_speed_ms = wind_speed_mph * 0.44704
    return round(0.5 * 1.225 * 50 * wind_speed_ms**3 / 1000, 2)


def calculate_suitability(wind_speed_mph):
    if wind_speed_mph < 7:
        return 0
    elif wind_speed_mph > 55:
        return 0
    else:
        return min(100, int(wind_speed_mph * 4))


def write_to_timescale(conn, message):
    data = message.value
    wind_speed_mph = data.get("wind_speed_mph", 0.0)
    wind_power_index = calculate_wind_power(wind_speed_mph)
    suitability_score = calculate_suitability(wind_speed_mph)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO weather_forecasts
                    (time, name, temperature, temperature_unit,
                     wind_speed, wind_direction, short_forecast, is_daytime,
                     wind_speed_mph, wind_power_index, suitability_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    data.get("startTime"),
                    data.get("name"),
                    data.get("temperature"),
                    data.get("temperatureUnit"),
                    data.get("windSpeed"),
                    data.get("windDirection"),
                    data.get("shortForecast"),
                    data.get("isDaytime"),
                    wind_speed_mph,
                    wind_power_index,
                    suitability_score,
                ),
            )
        conn.commit()
        TIMESCALE_WRITES.inc()
        logger.info(
            "Written to TimescaleDB",
            extra={
                "forecast_name": data.get("name"),
                "wind_speed_mph": wind_speed_mph,
                "wind_power_index": wind_power_index,
                "suitability_score": suitability_score,
            },
        )
    except Exception as e:
        conn.rollback()
        TIMESCALE_ERRORS.inc()
        logger.error("TimescaleDB write error", extra={"error": str(e)})


def main():
    consumer = create_consumer()
    dlq_producer = create_dlq_producer()
    minio_client = create_minio_client()
    ensure_bucket(minio_client)
    timescale_conn = create_timescale_conn()
    logger.info("Waiting for messages")

    for message in consumer:
        try:
            process_message(message)
            MESSAGES_CONSUMED.inc()
            update_lag(consumer)
            write_to_minio(minio_client, message)
            write_to_timescale(timescale_conn, message)
        except Exception as e:
            CONSUMER_ERRORS.inc()
            logger.error("Error processing message", extra={"error": str(e)})
            send_to_dlq(dlq_producer, message, e)


if __name__ == "__main__":
    main()