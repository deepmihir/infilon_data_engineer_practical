"""
ETL DAG: Extract events from Google Drive → Transform → Load to MongoDB.
"""
from datetime import datetime, timedelta
import os

import pandas as pd
import requests
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable

# Paths relative to project root (parent of dags/)
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIR = os.path.join(BASE_PATH, "source")
EXTRACT_PATH = os.path.join(SOURCE_DIR, "logs.json")
TRANSFORMED_PATH = os.path.join(SOURCE_DIR, "transformed.parquet")

# Shared Google Drive file URL (logs.json)
DRIVE_FILE_URL = (
    "https://drive.google.com/file/d/1_4xzvaJW-HGj0mp0yp6pZFwQ7cpI-wb_"
)
# Extract file ID for direct download
GOOGLE_DRIVE_FILE_ID = DRIVE_FILE_URL.rstrip("/").split("/d/")[-1].split("/")[0]

DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


def extract(**context):
    """Task 1: Download logs from shared Google Drive file to source/logs.json."""
    os.makedirs(SOURCE_DIR, exist_ok=True)
    # Use direct download URL (shared link format is for browser, not download)
    url = f"https://drive.google.com/uc?export=download&id={GOOGLE_DRIVE_FILE_ID}"
    response = requests.get(url)
    response.raise_for_status()
    with open(EXTRACT_PATH, "wb") as f:
        f.write(response.content)
    return EXTRACT_PATH


def transform(**context):
    """Task 2: Read JSON, flatten metadata, convert timestamp, ensure numeric."""
    path = context["ti"].xcom_pull(task_ids="extract") or EXTRACT_PATH
    df = pd.read_json(path)

    # Flatten metadata
    metadata_df = pd.json_normalize(df["metadata"])
    df = df.drop(columns=["metadata"]).join(metadata_df)

    # Convert timestamp
    df["event_timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.drop(columns=["timestamp"])

    # Ensure numeric type
    df["amount"] = df["amount"].astype("float")

    os.makedirs(SOURCE_DIR, exist_ok=True)
    df.to_parquet(TRANSFORMED_PATH, index=False)
    return TRANSFORMED_PATH


def load(**context):
    """Task 3: Load transformed data into MongoDB."""
    path = context["ti"].xcom_pull(task_ids="transform") or TRANSFORMED_PATH
    uri = Variable.get(
        "mongodb_conn_string",
        default_var=os.getenv("mongodb_conn_string"),
    )
    if not uri:
        raise ValueError("mongodb_conn_string not set. Set Airflow Variable or env var.")

    client = MongoClient(uri, server_api=ServerApi("1"))
    client.admin.command("ping")

    db = client["etl_db"]
    collection = db["events"]

    df = pd.read_parquet(path)
    df["event_timestamp"] = df["event_timestamp"].dt.to_pydatetime()
    records = df.to_dict(orient="records")
    collection.insert_many(records)

    print("ETL Load Completed Successfully 🚀")


with DAG(
    dag_id="etl_events_dag",
    default_args=DEFAULT_ARGS,
    description="ETL: Google Drive → Transform → MongoDB",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["etl", "events", "mongodb"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract",
        python_callable=extract,
    )

    transform_task = PythonOperator(
        task_id="transform",
        python_callable=transform,
    )

    load_task = PythonOperator(
        task_id="load",
        python_callable=load,
    )

    extract_task >> transform_task >> load_task
