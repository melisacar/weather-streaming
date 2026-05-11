import pytest
from jsonschema import validate, ValidationError
from src.producer.schema import WEATHER_SCHEMA

VALID_MESSAGE = {
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
    "detailedForecast": "Sunny. High near 72."
}

def test_valid_message_passes():
    # valid message should not raise
    validate(instance=VALID_MESSAGE, schema=WEATHER_SCHEMA)

def test_missing_required_field_fails():
    # temperature is required, removing it should fail
    msg = VALID_MESSAGE.copy()
    del msg['temperature']
    with pytest.raises(ValidationError):
        validate(instance=msg, schema=WEATHER_SCHEMA)

def test_wrong_temperature_type_fails():
    # temperature must be integer, string should fail
    msg = VALID_MESSAGE.copy()
    msg["temperature"] = "seventy-two"
    with pytest.raises(ValidationError):
        validate(instance=msg, schema=WEATHER_SCHEMA)

def test_wrong_is_daytime_type_fails():
    # isDaytime must be boolean, string should fail
    msg = VALID_MESSAGE.copy()
    msg["isDaytime"] = "true"
    with pytest.raises(ValidationError):
        validate(instance=msg, schema=WEATHER_SCHEMA)


def test_extra_fields_allowed():
    # extra fields not in schema should still pass
    msg = VALID_MESSAGE.copy()
    msg["unexpectedField"] = "some value"
    validate(instance=msg, schema=WEATHER_SCHEMA)


def test_missing_start_time_fails():
    msg = VALID_MESSAGE.copy()
    del msg["startTime"]
    with pytest.raises(ValidationError):
        validate(instance=msg, schema=WEATHER_SCHEMA)


def test_missing_short_forecast_fails():
    msg = VALID_MESSAGE.copy()
    del msg["shortForecast"]
    with pytest.raises(ValidationError):
        validate(instance=msg, schema=WEATHER_SCHEMA)