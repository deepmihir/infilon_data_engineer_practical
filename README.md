# ETL Events Pipeline (Airflow)

An Apache Airflow ETL pipeline that **extracts** event logs from Google Drive, **transforms** them into a flat, typed structure, and **loads** them into MongoDB. Suitable for event analytics (e.g. daily active users, purchases).

---

## What This Pipeline Does

The DAG **`etl_events_dag`** runs three tasks in sequence:

| Step   | Task       | Description |
|--------|------------|-------------|
| **1**  | **Extract** | Downloads `logs.json` from a shared Google Drive link and saves it to `source/logs.json`. |
| **2**  | **Transform** | Reads the JSON, flattens the `metadata` object into columns (`device`, `amount`), converts `timestamp` to UTC `event_timestamp`, drops the original `timestamp`, and ensures `amount` is numeric. Writes the result to `source/transformed.parquet`. |
| **3**  | **Load** | Reads the parquet file, converts datetimes for MongoDB, and inserts all records into the `etl_db.events` collection. |

**Data flow:** Google Drive → `source/logs.json` → transform → `source/transformed.parquet` → MongoDB `etl_db.events`.

The DAG is **manually triggered** (no schedule). Each run overwrites/extends the data in the target collection depending on your use case.

---

## Project Structure

```
infilon/
├── README.md                 # This file
├── requirements.txt          # Python deps (used by venv and Docker image)
├── .env.example              # Example env vars (copy to .env)
├── .env                      # Secrets (mongodb_conn_string) — not committed
├── Dockerfile                # Airflow image + requirements.txt
├── docker-compose.yaml       # Airflow stack (Postgres, Redis, scheduler, worker, webserver)
├── dags/
│   ├── etl_events_dag.py     # ETL DAG (extract → transform → load)
│   └── README.md             # DAG folder notes
├── source/                   # ETL inputs/outputs (mounted in Docker)
│   ├── logs.json             # Downloaded from Google Drive (extract output)
│   └── transformed.parquet   # Transformed data (transform output)
├── script.ipynb              # Original ETL logic (notebook)
├── config/                   # Airflow config (optional)
└── plugins/                  # Airflow plugins (optional)
```

---

## Prerequisites

- **Docker** and **Docker Compose** (for running Airflow).
- **MongoDB** connection string (e.g. MongoDB Atlas) for the load task.
- (Optional) **Python 3.10+** and a **virtualenv** if you want to run the notebook or scripts locally.

---

## Setup and Run

### 1. Clone and enter the project

```bash
cd infilon
```

### 2. Configure MongoDB connection

Create a `.env` file in the project root (same folder as `docker-compose.yaml`). You can copy `.env.example` and fill in your values:

```bash
cp .env.example .env
# Edit .env and set mongodb_conn_string=...
```

Example content:

```env
mongodb_conn_string=mongodb+srv://USER:PASSWORD@CLUSTER.mongodb.net/?appName=...
```

No quotes, no spaces around `=`. This is loaded by Docker Compose and used by the **load** task.

(Alternatively, you can set the Airflow Variable `mongodb_conn_string` in the Airflow UI: **Admin → Variables**.)

### 3. Build the Airflow image (installs from `requirements.txt`)

Build the custom image once so all Airflow containers use the same dependencies:

```bash
docker compose build airflow-image
```

### 4. Start Airflow

```bash
docker compose up -d
```

Wait 1–2 minutes for the scheduler and webserver to be healthy.

### 5. Open the Airflow UI

- URL: **http://localhost:8080**
- Default login: **airflow** / **airflow**

### 6. Run the ETL DAG

1. In the DAGs list, find **etl_events_dag**.
2. Turn the toggle to **Unpaused** if it is paused.
3. Click **Trigger DAG** (play button) to run the pipeline.

Monitor progress in the Graph or Grid view. When all three tasks (extract → transform → load) are green, the run is complete and data is in MongoDB.

---

## Running Locally (optional)

If you prefer to run the ETL logic outside Airflow (e.g. in the notebook):

```bash
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Ensure `.env` exists with `mongodb_conn_string`. You can run the cells in `script.ipynb` or call the same logic from a script.

---

## Environment Variables

| Variable               | Used by        | Description |
|------------------------|----------------|-------------|
| `mongodb_conn_string`  | Load task / .env | MongoDB URI (required for load). |
| `AIRFLOW_IMAGE_NAME`   | Docker Compose | Override Airflow image name (default: `infilon-airflow:latest`). |
| `AIRFLOW_PROJ_DIR`     | Docker Compose | Project path for volumes (default: `.`). |
| `AIRFLOW_UID`          | Docker Compose | User ID for Airflow containers (see Airflow Docker docs). |

---

## DAG Details

- **DAG id:** `etl_events_dag`
- **Schedule:** None (trigger manually).
- **Tasks:** `extract` → `transform` → `load` (linear).
- **Data passing:** Extract returns the path to `logs.json`; Transform reads it and writes `transformed.parquet`, then returns that path; Load reads the parquet and inserts into MongoDB. Paths are passed via Airflow XCom.
- **Retries:** 1 retry with 2-minute delay on failure.

---

## Troubleshooting

- **DAG not appearing or import errors**  
  Check: `docker compose exec airflow-scheduler airflow dags list-import-errors`

- **Load task: "mongodb_conn_string not set"**  
  Add `mongodb_conn_string` to `.env` in the project root and restart: `docker compose down && docker compose up -d`

- **Rebuild after changing `requirements.txt`**  
  `docker compose build --no-cache airflow-image` then `docker compose up -d`

---

## Summary

This project provides a production-style ETL pipeline on Airflow: **extract** from Google Drive, **transform** with pandas, and **load** into MongoDB, with dependencies defined in `requirements.txt` and the connection string in `.env` (or an Airflow Variable).
