"""Ejecuta el pipeline completo en local con PySpark.

Uso:
    python -m src.jobs.run_local --input data/raw/transactions.csv --output data
"""

import argparse
import json

from pyspark.sql import SparkSession

from src.jobs.transform import clean_transactions, daily_kpis, quality_report


def main(input_path: str, output_dir: str) -> dict:
    spark = (
        SparkSession.builder.appName("transactions-pipeline").master("local[*]")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    raw = spark.read.option("header", True).csv(input_path)
    clean = clean_transactions(raw).cache()

    clean.write.mode("overwrite").partitionBy("event_date").parquet(f"{output_dir}/clean/transactions")
    daily_kpis(clean).write.mode("overwrite").parquet(f"{output_dir}/curated/daily_kpis")

    report = quality_report(raw, clean)
    print(json.dumps(report, indent=2))
    spark.stop()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/transactions.csv")
    parser.add_argument("--output", default="data")
    args = parser.parse_args()
    main(args.input, args.output)
