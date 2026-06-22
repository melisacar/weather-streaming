import pytest
from unittest.mock import MagicMock
from src.consumer.consumer import process_message, send_to_dlq, update_lag, DLQ_TOPIC


FAKE_MESSAGE = MagicMock()
FAKE_MESSAGE.value = {
    "startTime": "2026-05-11T06:00:00-07:00",
    "temperature": 72,
    "temperatureUnit": "F",
    "shortForecast": "Sunny"
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