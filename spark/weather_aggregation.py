from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import os

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "weather-raw")

TIMESCALE_HOST = os.getenv("TIMESCALE_HOST", "timescaledb")
TIMESCALE_PORT = os.getenv("TIMESCALE_PORT", "5432")
TIMESCALE_USER = os.getenv("TIMESCALE_USER", "weatheruser")
TIMESCALE_PASSWORD = os.getenv("TIMESCALE_PASSWORD", "weatherpass")
TIMESCALE_DB = os.getenv("TIMESCALE_DB", "weather")

JDBC_URL = f"jdbc:postgresql://{TIMESCALE_HOST}:{TIMESCALE_PORT}/{TIMESCALE_DB}"

spark = SparkSession.builder \
    .appName("WeatherAggregation") \
    .config("spark.hadoop.fs.s3a.endpoint", f"http://{MINIO_ENDPOINT}") \
    .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY) \
    .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY) \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# read raw JSON from MinIO
df = spark.read.json(f"s3a://{MINIO_BUCKET}/raw/*/*/*/*/*.json")

# parse and aggregate
df = df.withColumn("start_time", F.to_timestamp("startTime")) \
       .withColumn("hour", F.date_trunc("hour", F.col("start_time"))) \
       .withColumn("wind_speed_mph", F.col("wind_speed_mph").cast("double")) \
       .withColumn("temperature", F.col("temperature").cast("integer"))

aggregated = df.groupBy("hour").agg(
    F.avg("wind_speed_mph").alias("avg_wind_speed_mph"),
    F.max("wind_speed_mph").alias("max_wind_speed_mph"),
    F.avg("temperature").alias("avg_temperature"),
    F.count("*").alias("record_count"),
)

# write to TimescaleDB
aggregated.write \
    .format("jdbc") \
    .option("url", JDBC_URL) \
    .option("dbtable", "weather_hourly_aggregates") \
    .option("user", TIMESCALE_USER) \
    .option("password", TIMESCALE_PASSWORD) \
    .option("driver", "org.postgresql.Driver") \
    .mode("append") \
    .save()

print("Aggregation complete.")
spark.stop()