from unittest.mock import MagicMock

import pytest

from src.consumer.consumer import DLQ_TOPIC, process_message, send_to_dlq, update_lag

FAKE_MESSAGE = MagicMock()
FAKE_MESSAGE.value = {
    "startTime": "2026-05-11T06:00:00-07:00",
    "temperature": 72,
    "temperatureUnit": "F",
    "shortForecast": "Sunny",
}
FAKE_MESSAGE.timestamp = 1234567890
FAKE_MESSAGE.topic = "weather-data"
FAKE_MESSAGE.partition = 0
FAKE_MESSAGE.offset = 42


def test_process_message_prints_correctly(capsys):
    # process_message should print temperature and forecast
    process_message(FAKE_MESSAGE)
    captured = capsys.readouterr()
    assert "72" in captured.out
    assert "Sunny" in captured.out


def test_process_message_missing_field_raises():
    # message missing required fields should raise KeyError
    bad_message = MagicMock()
    bad_message.value = {"startTime": "2026-05-11T06:00:00-07:00"}
    with pytest.raises(KeyError):
        process_message(bad_message)


def test_send_to_dlq_sends_correct_payload():
    # failed message should be sent to DLQ topic with error info
    mock_producer = MagicMock()
    mock_future = MagicMock()
    mock_producer.send.return_value = mock_future
    error = ValueError("something went wrong")

    send_to_dlq(mock_producer, FAKE_MESSAGE, error)

    mock_producer.send.assert_called_once()
    call_args = mock_producer.send.call_args
    assert call_args[0][0] == DLQ_TOPIC
    payload = call_args[0][1]
    assert payload["error"] == "something went wrong"
    assert payload["offset"] == 42
    assert payload["partition"] == 0


def test_send_to_dlq_increments_counter():
    # DLQ counter should increment on successful send
    mock_producer = MagicMock()
    mock_future = MagicMock()
    mock_producer.send.return_value = mock_future

    from src.consumer.consumer import DLQ_MESSAGES

    before = DLQ_MESSAGES._value.get()

    send_to_dlq(mock_producer, FAKE_MESSAGE, ValueError("test error"))

    after = DLQ_MESSAGES._value.get()
    assert after == before + 1


def test_send_to_dlq_handles_kafka_error():
    # if DLQ send fails, function should not raise
    from kafka.errors import KafkaError

    mock_producer = MagicMock()
    mock_producer.send.side_effect = KafkaError("dlq unavailable")

    send_to_dlq(mock_producer, FAKE_MESSAGE, ValueError("original error"))
    # should not raise


def test_update_lag_sets_gauge():
    # update_lag should calculate lag and set gauge metric
    mock_consumer = MagicMock()
    mock_consumer.partitions_for_topic.return_value = {0}

    from kafka import TopicPartition

    tp = TopicPartition("weather-data", 0)
    mock_consumer.end_offsets.return_value = {tp: 100}
    mock_consumer.position.return_value = 90

    from src.consumer.consumer import CONSUMER_LAG

    update_lag(mock_consumer)

    assert CONSUMER_LAG.labels(topic="weather-data", partition=0)._value.get() == 10


def test_update_lag_handles_none_partitions():
    # if topic has no partitions yet, should return without error
    mock_consumer = MagicMock()
    mock_consumer.partitions_for_topic.return_value = None

    update_lag(mock_consumer)
    # should not raise


def test_write_to_minio_success():
    # successful write should increment MINIO_WRITES counter
    mock_client = MagicMock()
    mock_client.put_object.return_value = {}

    from src.consumer.consumer import MINIO_WRITES, write_to_minio

    before = MINIO_WRITES._value.get()

    write_to_minio(mock_client, FAKE_MESSAGE)

    after = MINIO_WRITES._value.get()
    assert after == before + 1
    mock_client.put_object.assert_called_once()


def test_write_to_minio_correct_bucket():
    # should write to correct bucket
    mock_client = MagicMock()

    from src.consumer.consumer import MINIO_BUCKET, write_to_minio

    write_to_minio(mock_client, FAKE_MESSAGE)

    call_args = mock_client.put_object.call_args
    assert call_args[1]["Bucket"] == MINIO_BUCKET


def test_write_to_minio_correct_content_type():
    # should write with application/json content type
    mock_client = MagicMock()

    from src.consumer.consumer import write_to_minio

    write_to_minio(mock_client, FAKE_MESSAGE)

    call_args = mock_client.put_object.call_args
    assert call_args[1]["ContentType"] == "application/json"


def test_write_to_minio_key_format():
    # key should follow raw/YYYY/MM/DD/HH/partition-offset.json format
    mock_client = MagicMock()

    from src.consumer.consumer import write_to_minio

    write_to_minio(mock_client, FAKE_MESSAGE)

    call_args = mock_client.put_object.call_args
    key = call_args[1]["Key"]
    assert key.startswith("raw/")
    assert key.endswith(f"{FAKE_MESSAGE.partition}-{FAKE_MESSAGE.offset}.json")


def test_write_to_minio_error_increments_counter():
    # failed write should increment MINIO_ERRORS counter
    mock_client = MagicMock()
    mock_client.put_object.side_effect = Exception("connection refused")

    from src.consumer.consumer import MINIO_ERRORS, write_to_minio

    before = MINIO_ERRORS._value.get()

    write_to_minio(mock_client, FAKE_MESSAGE)

    after = MINIO_ERRORS._value.get()
    assert after == before + 1


def test_write_to_minio_error_does_not_raise():
    # failed write should not crash the consumer
    mock_client = MagicMock()
    mock_client.put_object.side_effect = Exception("connection refused")

    from src.consumer.consumer import write_to_minio

    write_to_minio(mock_client, FAKE_MESSAGE)
    # should not raise


def test_ensure_bucket_creates_if_not_exists():
    # if bucket does not exist, should create it
    from botocore.exceptions import ClientError

    from src.consumer.consumer import ensure_bucket

    mock_client = MagicMock()
    mock_client.head_bucket.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadBucket"
    )

    ensure_bucket(mock_client)

    mock_client.create_bucket.assert_called_once()


def test_ensure_bucket_skips_if_exists():
    # if bucket exists, should not create it
    from src.consumer.consumer import ensure_bucket

    mock_client = MagicMock()
    mock_client.head_bucket.return_value = {}

    ensure_bucket(mock_client)

    mock_client.create_bucket.assert_not_called()

def test_calculate_wind_power_zero_wind():
    # zero wind speed should return zero power
    from src.consumer.consumer import calculate_wind_power

    result = calculate_wind_power(0)
    assert result == 0.0


def test_calculate_wind_power_positive():
    # positive wind speed should return positive power
    from src.consumer.consumer import calculate_wind_power

    result = calculate_wind_power(10)
    assert result > 0


def test_calculate_wind_power_increases_with_speed():
    # higher wind speed should produce more power (cubic relationship)
    from src.consumer.consumer import calculate_wind_power

    assert calculate_wind_power(20) > calculate_wind_power(10)


def test_calculate_suitability_too_low():
    # wind speed below 7 mph should return 0
    from src.consumer.consumer import calculate_suitability

    assert calculate_suitability(5) == 0
    assert calculate_suitability(0) == 0


def test_calculate_suitability_too_high():
    # wind speed above 55 mph should return 0 — dangerous for turbines
    from src.consumer.consumer import calculate_suitability

    assert calculate_suitability(60) == 0
    assert calculate_suitability(100) == 0


def test_calculate_suitability_optimal():
    # wind speed in 7-55 mph range should return positive score
    from src.consumer.consumer import calculate_suitability

    assert calculate_suitability(15) > 0
    assert calculate_suitability(25) > 0


def test_calculate_suitability_max_100():
    # score should never exceed 100
    from src.consumer.consumer import calculate_suitability

    assert calculate_suitability(30) <= 100
    assert calculate_suitability(50) <= 100


def test_write_to_timescale_success():
    # successful write should increment TIMESCALE_WRITES counter
    from src.consumer.consumer import write_to_timescale, TIMESCALE_WRITES

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    before = TIMESCALE_WRITES._value.get()
    write_to_timescale(mock_conn, FAKE_MESSAGE)
    after = TIMESCALE_WRITES._value.get()

    assert after == before + 1
    mock_conn.commit.assert_called_once()


def test_write_to_timescale_error_rolls_back():
    # failed write should rollback and increment error counter
    from src.consumer.consumer import write_to_timescale, TIMESCALE_ERRORS

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("DB error")
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    before = TIMESCALE_ERRORS._value.get()
    write_to_timescale(mock_conn, FAKE_MESSAGE)
    after = TIMESCALE_ERRORS._value.get()

    assert after == before + 1
    mock_conn.rollback.assert_called_once()


def test_write_to_timescale_does_not_raise():
    # DB error should not crash the consumer
    from src.consumer.consumer import write_to_timescale

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("DB error")
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    write_to_timescale(mock_conn, FAKE_MESSAGE)
    # should not raise