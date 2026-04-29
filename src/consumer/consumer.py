from kafka import KafkaConsumer
import json
import sys
import os
from prometheus_client import start_http_server, Counter
from dotenv import load_dotenv

load_dotenv()

KAFKA_BROKERS = os.getenv('KAFKA_BROKERS', 'kafka:9092')
TOPIC = os.getenv('KAFKA_TOPIC', 'weather-data')
GROUP_ID = os.getenv('GROUP_ID', 'weather-group')
CONSUMER_PORT = int(os.getenv('CONSUMER_PORT', '8001'))

messages_consumed = Counter('consumer_messages_consumed_total', 'Total messages consumed')
start_http_server(CONSUMER_PORT)

try:
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BROKERS,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id=GROUP_ID,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    print("Kafka consumer started. Waiting for messages...\n", flush=True)

    for message in consumer:
        messages_consumed.inc()
        data = message.value
        print(f"[{message.timestamp}] {data['startTime']} → {data['temperature']}°{data['temperatureUnit']}, {data['shortForecast']}", flush=True)
except Exception as e:
    print(f"Fatal error: {str(e)}", file=sys.stderr, flush=True)
    raise