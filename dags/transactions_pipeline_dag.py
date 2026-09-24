"""DAG de Airflow: generar/extraer -> transformar (PySpark) -> control de calidad.

Semana 8 del roadmap: ejecutar con Airflow en Docker
(https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html).
En la versión cloud, la tarea `transform` se reemplaza por GlueJobOperator
(apache-airflow-providers-amazon).
"""

from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

REPO = "/opt/airflow/repo"


def check_quality(**_):
    import pandas as pd

    kpis = pd.read_parquet(f"{REPO}/data/curated/daily_kpis")
    assert len(kpis) > 0, "daily_kpis vacío"
    assert kpis["rejection_rate"].between(0, 1).all(), "rejection_rate fuera de rango"
    assert (kpis["n_transactions"] > 0).all(), "días sin transacciones"


with DAG(
    dag_id="transactions_pipeline",
    start_date=datetime(2026, 10, 1),
    schedule="@daily",
    catchup=False,
    tags=["portfolio", "pyspark"],
) as dag:
    extract = BashOperator(
        task_id="extract",
        bash_command=f"cd {REPO} && python scripts/generate_data.py --rows 50000",
    )
    transform = BashOperator(
        task_id="transform",
        bash_command=f"cd {REPO} && python -m src.jobs.run_local",
    )
    quality = PythonOperator(task_id="quality_check", python_callable=check_quality)

    extract >> transform >> quality
