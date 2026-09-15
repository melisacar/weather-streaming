CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS weather_forecasts (
    time             TIMESTAMPTZ NOT NULL,
    name             TEXT,
    temperature      INTEGER,
    temperature_unit VARCHAR(5),
    wind_speed       TEXT,
    wind_direction   VARCHAR(5),
    short_forecast   TEXT,
    is_daytime       BOOLEAN,
    wind_speed_mph   FLOAT,
    wind_power_index FLOAT,
    suitability_score INTEGER
);

SELECT create_hypertable('weather_forecasts', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_weather_forecasts_time
    ON weather_forecasts (time DESC);