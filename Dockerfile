# Extend official Airflow image and install project dependencies from requirements.txt
FROM apache/airflow:2.11.1

COPY requirements.txt /requirements.txt
USER airflow
RUN pip install --no-cache-dir -r /requirements.txt
