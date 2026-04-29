from kafka.admin import KafkaAdminClient, NewTopic
import os
from dotenv import load_dotenv

load_dotenv()

KAFKA_BROKER = os.getenv('KAFKA_BROKERS', 'kafka:9092')
TOPIC_NAME = os.getenv('KAFKA_TOPIC', 'weather-data')
NUM_PARTITIONS = int(os.getenv('NUM_PARTITIONS', '1'))
REPLICATION_FACTOR = int(os.getenv('REPLICATION_FACTOR', '1'))

def create_topic():
    admin_client = KafkaAdminClient(
        bootstrap_servers=KAFKA_BROKER,
        client_id="setup-script"
    )

    topic_list = [NewTopic(
        name=TOPIC_NAME,
        num_partitions=NUM_PARTITIONS,
        replication_factor=REPLICATION_FACTOR
    )]

    try:
        admin_client.create_topics(new_topics=topic_list, validate_only=False)
        print(f"Topic '{TOPIC_NAME}' created successfully.")
    except Exception as e:
        print(f"Topic creation failed or already exists: {e}")
    finally:
        admin_client.close()

if __name__ == "__main__":
    create_topic()