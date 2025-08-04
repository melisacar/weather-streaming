from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'weather-data',
    bootstrap_servers='kafka:9092',
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='weather-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

print("Kafka consumer started. Waiting for messages...\n")

for message in consumer:
    data = message.value
    print(f"[{message.timestamp}] {data['startTime']} → {data['temperature']}°{data['temperatureUnit']}, {data['shortForecast']}")