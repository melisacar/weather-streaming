WEATHER_AVRO_SCHEMA = {
    "type": "record",
    "name": "WeatherForecast",
    "namespace": "com.weather.streaming",
    "fields": [
        {"name": "name", "type": ["null", "string"], "default": None},
        {"name": "startTime", "type": "string"},
        {"name": "endTime", "type": "string"},
        {"name": "isDaytime", "type": ["null", "boolean"], "default": None},
        {"name": "temperature", "type": "int"},
        {"name": "temperatureUnit", "type": "string"},
        {"name": "windSpeed", "type": ["null", "string"], "default": None},
        {"name": "windDirection", "type": ["null", "string"], "default": None},
        {"name": "shortForecast", "type": "string"},
        {"name": "wind_speed_mph", "type": ["null", "double"], "default": None},
    ],
}