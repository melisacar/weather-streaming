from kafka import KafkaConsumer, TopicPartition
from kafka.errors import KafkaError
import json
import sys
import os
import time
from prometheus_client import start_http_server, Counter, Gauge
from dotenv import load_dotenv

load_dotenv()

KAFKA_BROKERS = os.getenv('KAFKA_BROKERS', 'kafka:9092')
TOPIC = os.getenv('KAFKA_TOPIC', 'weather-data')
GROUP_ID = os.getenv('GROUP_ID', 'weather-group')
CONSUMER_PORT = int(os.getenv('CONSUMER_PORT', '8001'))

start_http_server(CONSUMER_PORT)

MESSAGES_CONSUMED = Counter('consumer_messages_consumed_total', 'Total messages consumed')
CONSUMER_ERRORS = Counter('consumer_errors_total', 'Total consumer errors')
CONSUMER_LAG = Gauge('consumer_lag', 'Consumer lag per partition', ['topic', 'partition'])


def create_consumer():
    # retry connecting to Kafka broker on startup
    while True:
        try:
            consumer = KafkaConsumer(
                TOPIC,
                bootstrap_servers=KAFKA_BROKERS,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id=GROUP_ID,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            )
            print("Kafka consumer connected.", flush=True)
            return consumer
        except KafkaError as e:
            print(f"Kafka not ready, retrying in 5s: {e}", flush=True)
            time.sleep(5)


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
        print(f"Lag calculation error: {e}", flush=True)


def process_message(message):
    data = message.value
    print(
        f"[{message.timestamp}] {data['startTime']} → "
        f"{data['temperature']}°{data['temperatureUnit']}, "
        f"{data['shortForecast']}",
        flush=True
    )


def main():
    consumer = create_consumer()
    print("Waiting for messages...\n", flush=True)

    for message in consumer:
        try:
            process_message(message)
            MESSAGES_CONSUMED.inc()
            update_lag(consumer)
        except Exception as e:
            CONSUMER_ERRORS.inc()
            print(f"Error processing message: {e}", flush=True)


if __name__ == "__main__":
    main()