import pandas as pd
import os
from dotenv import load_dotenv
from sklearn.ensemble import IsolationForest
import logging
from sqlalchemy import create_engine

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("anomaly_detection")

engine = create_engine(
    f"postgresql://{os.getenv('TIMESCALE_USER')}:{os.getenv('TIMESCALE_PASSWORD')}@localhost:{os.getenv('TIMESCALE_PORT')}/{os.getenv('TIMESCALE_DB')}"
)

df = pd.read_sql(
    """
    SELECT hour, avg_wind_speed_mph, max_wind_speed_mph, avg_temperature
    FROM weather_hourly_aggregates
    ORDER BY hour
    """,
    engine,
)

if df.empty:
    logger.warning("No data found in weather_hourly_aggregates.")
    exit(0)

features = df[["avg_wind_speed_mph", "max_wind_speed_mph", "avg_temperature"]]

model = IsolationForest(contamination=0.05, random_state=42)
df["anomaly"] = model.fit_predict(features)

# -1 = anomaly, 1 = normal
anomalies = df[df["anomaly"] == -1]

if anomalies.empty:
    logger.info("No anomalies detected.")
else:
    logger.warning(f"Detected {len(anomalies)} anomalies:")
    for _, row in anomalies.iterrows():
        logger.warning(
            "Anomaly detected",
            extra={
                "hour": str(row["hour"]),
                "avg_wind_speed_mph": row["avg_wind_speed_mph"],
                "avg_temperature": row["avg_temperature"],
            },
        )

logger.info(f"Total records: {len(df)}, Anomalies: {len(anomalies)}")