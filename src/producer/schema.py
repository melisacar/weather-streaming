WEATHER_SCHEMA = {
    "type": "object",
    "required": ["startTime", "endTime", "temperature", "temperatureUnit", "shortForecast"],
    "properties": {
        "startTime": {"type": "string"},
        "endTime": {"type": "string"},
        "temperature": {"type": "integer"},
        "temperatureUnit": {"type": "string"},
        "shortForecast": {"type": "string"},
        "windSpeed": {"type": "string"},
        "windDirection": {"type": "string"},
        "isDaytime": {"type": "boolean"},
        "name": {"type": "string"},
    }
}