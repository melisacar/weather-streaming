from kafka import KafkaProducer
import json
import requests
import time
import os

producer = KafkaProducer(
    bootstrap_servers=os.getenv('KAFKA_BROKERS', 'kafka:9092'), # Container DNS
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

topic = 'weather-data'

def fetch_weather_data():
    url = "https://api.weather.gov/gridpoints/LOX/150,48/forecast"
    headers = {"User-Agent": "myweatherapp.com"}
    response = requests.get(url, headers=headers)
    data = response.json()
    return data["properties"]["periods"]

while True:
    weather_periods = fetch_weather_data()
    for item in weather_periods:
        producer.send(topic, item)
        print(f"Sent: {item}")
        time.sleep(5)
    time.sleep(300)
