import great_expectations as gx
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host="localhost",
    port=os.getenv("TIMESCALE_PORT"),
    user=os.getenv("TIMESCALE_USER"),
    password=os.getenv("TIMESCALE_PASSWORD"),
    dbname=os.getenv("TIMESCALE_DB"),
)

df = pd.read_sql("SELECT * FROM weather_forecasts ORDER BY time DESC LIMIT 1000", conn)
conn.close()

context = gx.get_context()

data_source = context.data_sources.add_pandas("weather_data")
data_asset = data_source.add_dataframe_asset("forecasts")
batch_definition = data_asset.add_batch_definition_whole_dataframe("full_batch")
batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

suite = context.suites.add(gx.ExpectationSuite(name="weather_forecasts_suite"))

suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="time"))
suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="temperature", min_value=-50, max_value=130))
suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="wind_speed_mph"))
suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="wind_speed_mph", min_value=0, max_value=200))
suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="suitability_score", min_value=0, max_value=100))
suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="wind_power_index", min_value=0))
suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="short_forecast"))

results = batch.validate(suite)

if results["success"]:
    print("All data quality checks passed.")
else:
    print("Data quality checks FAILED:")
    for r in results["results"]:
        if not r["success"]:
            print(f"  - {r['expectation_config']['type']}: {r['result']}")