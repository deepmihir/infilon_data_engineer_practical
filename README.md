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

After a successful run, the **`etl_db.events`** collection in MongoDB contains the loaded documents (e.g. `user_id`, `event_type`, `event_timestamp`, `device`, `amount`):

![Events collection in MongoDB](Image/events_collection_output.png)

For **analytics queries** (Daily Active Users, Daily Purchases) and their MongoDB aggregation equivalents, see [ANALYTICS_README.md](ANALYTICS_README.md).

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
├── source/                   # ETL inputs/outputs (mounted in Docker)
│   ├── logs.json             # Downloaded from Google Drive (extract output)
│   └── transformed.parquet   # Transformed data (transform output)
├── SQL_QUERIES/
│   └── analytics_sql_query.sql   # SQL reference for analytics
├── ANALYTICS_README.md       # MongoDB equivalents, screenshots, output CSVs
├── output/                   # Analytics query results (CSV)
│   ├── DAU.csv               # Daily Active Users
│   └── DAILY_TOTAL_PURCHASE.csv
└── Image/                    # Screenshots (DAG graph, query outputs)
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

## Analytics queries and output

After the ETL loads data into MongoDB (`etl_db.events`), you can run analytics on it:

- **[ANALYTICS_README.md](ANALYTICS_README.md)** — MongoDB aggregation pipelines for:
  - **Daily Active Users (DAU)** — distinct users per day
  - **Daily Purchases** — purchase count and revenue per day  
  Includes SQL reference, MongoDB equivalents, and screenshots of query results.

- **Output (CSV)** — Query results are also available as CSV files in **`output/`**:
  - `output/DAU.csv` — Daily Active Users
  - `output/DAILY_TOTAL_PURCHASE.csv` — Daily Purchases  

Open these in Excel, Google Sheets, or any text editor to view the results.

---

## Pipeline overview

![ETL Events DAG](Image/DAG_graph.png)
