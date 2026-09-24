"""AWS Glue ETL Job (Glue 4.0+ / PySpark).

Reutiliza las mismas transformaciones del pipeline local.
Parámetros del job:
    --RAW_PATH      s3://<bucket>/raw/transactions/
    --CLEAN_PATH    s3://<bucket>/clean/transactions/
    --CURATED_PATH  s3://<bucket>/curated/daily_kpis/
    --extra-py-files s3://<bucket>/code/src.zip   (zip de la carpeta src/)
"""

import json
import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext

from src.jobs.transform import clean_transactions, daily_kpis, quality_report

args = getResolvedOptions(sys.argv, ["JOB_NAME", "RAW_PATH", "CLEAN_PATH", "CURATED_PATH"])

sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session
job = Job(glue_context)
job.init(args["JOB_NAME"], args)

raw = spark.read.option("header", True).csv(args["RAW_PATH"])
clean = clean_transactions(raw).cache()

clean.write.mode("overwrite").partitionBy("event_date").parquet(args["CLEAN_PATH"])
daily_kpis(clean).write.mode("overwrite").parquet(args["CURATED_PATH"])

print(json.dumps(quality_report(raw, clean)))  # visible en CloudWatch Logs
job.commit()
