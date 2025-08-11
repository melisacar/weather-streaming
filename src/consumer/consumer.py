from kafka import KafkaConsumer
import json
import sys
from prometheus_client import start_http_server, Counter

messages_consumed = Counter('consumer_messages_consumed_total', 'Total messages consumed')
start_http_server(8001)

try:
    consumer = KafkaConsumer(
        'weather-data',
        bootstrap_servers='kafka:9092',
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='weather-group',
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
