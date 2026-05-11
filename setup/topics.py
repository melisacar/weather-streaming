import time

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
import os
from dotenv import load_dotenv

load_dotenv()

KAFKA_BROKER = os.getenv('KAFKA_BROKERS', 'kafka:9092')
TOPIC_NAME = os.getenv('KAFKA_TOPIC', 'weather-data')
DLQ_TOPIC_NAME = os.getenv('DLQ_TOPIC', 'weather-data.dlq')
NUM_PARTITIONS = int(os.getenv('NUM_PARTITIONS', '1'))
REPLICATION_FACTOR = int(os.getenv('REPLICATION_FACTOR', '1'))

def create_topics():
    while True:
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=KAFKA_BROKER,
                client_id="setup-script"
            )
            break
        except Exception as e:
            print(f"Failed to connect to Kafka: {e}", flush=True)
            time.sleep(5)

    topic_list = [
            NewTopic(
            name=TOPIC_NAME,
            num_partitions=NUM_PARTITIONS,
            replication_factor=REPLICATION_FACTOR
        ),  
            NewTopic(
                name=DLQ_TOPIC_NAME,
                num_partitions=NUM_PARTITIONS,
                replication_factor=REPLICATION_FACTOR
            ),
        ]

    for topic in topic_list:
        try:
            admin_client.create_topics(new_topics=[topic], validate_only=False)
            print(f"Topic '{topic.name}' created successfully.")
        except TopicAlreadyExistsError:
            print(f"Topic '{topic.name}' already exists, skipping.")
        except Exception as e:
            print(f"Topic creation failed for '{topic.name}': {e}")

    admin_client.close()


if __name__ == "__main__":
    create_topics()