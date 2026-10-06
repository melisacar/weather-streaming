from unittest.mock import MagicMock, patch

import pytest

from src.producer.producer import TOPIC, fetch_weather_data, send_message

FAKE_PERIODS = [
    {
        "number": 1,
        "name": "Today",
        "startTime": "2026-05-11T06:00:00-07:00",
        "endTime": "2026-05-11T18:00:00-07:00",
        "isDaytime": True,
        "temperature": 72,
        "temperatureUnit": "F",
        "windSpeed": "5 to 10 mph",
        "windDirection": "W",
        "shortForecast": "Sunny",
        "detailedForecast": "Sunny. High near 72.",
    }
]


def test_fetch_weather_data_returns_periods():
    # mock requests.get to return fake API response
    fake_response = MagicMock()
    fake_response.json.return_value = {"properties": {"periods": FAKE_PERIODS}}
    fake_response.raise_for_status = MagicMock()

    with patch("src.producer.producer.requests.get", return_value=fake_response):
        result = fetch_weather_data()

    assert result == FAKE_PERIODS
    assert len(result) == 1
    assert result[0]["temperature"] == 72


def test_fetch_weather_data_calls_raise_for_status():
    # raise_for_status should be called to catch 4xx/5xx errors
    fake_response = MagicMock()
    fake_response.json.return_value = {"properties": {"periods": FAKE_PERIODS}}

    with patch("src.producer.producer.requests.get", return_value=fake_response):
        fetch_weather_data()

    fake_response.raise_for_status.assert_called_once()


def test_fetch_weather_data_timeout_raises():
    # when requests times out, exception should propagate
    import requests

    with patch(
        "src.producer.producer.requests.get", side_effect=requests.exceptions.Timeout
    ):
        with pytest.raises(Exception):
            fetch_weather_data()


def test_send_message_success():
    mock_producer = MagicMock()
    mock_avro_serializer = MagicMock(return_value=b"avro_bytes")

    message = FAKE_PERIODS[0]
    send_message(mock_producer, mock_avro_serializer, message)

    mock_producer.produce.assert_called_once()
    mock_producer.flush.assert_called_once()


def test_send_message_kafka_error_does_not_raise():
    mock_producer = MagicMock()
    mock_avro_serializer = MagicMock(return_value=b"avro_bytes")
    mock_producer.produce.side_effect = Exception("broker unavailable")

    message = FAKE_PERIODS[0]
    send_message(mock_producer, mock_avro_serializer, message)


def test_send_message_invalid_schema_skips_kafka():
    mock_producer = MagicMock()
    mock_avro_serializer = MagicMock()
    invalid_message = {"name": "Today"}

    send_message(mock_producer, mock_avro_serializer, invalid_message)

    mock_producer.produce.assert_not_called()
