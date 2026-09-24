"""Transformaciones PySpark reutilizables (local y AWS Glue).

Flujo: raw (CSV) -> clean (Parquet particionado) -> curated (agregados).
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

VALID_CHANNELS = ["app", "qr", "pse", "cash_in", "p2p"]


def clean_transactions(df: DataFrame) -> DataFrame:
    """Limpia la capa raw: tipos, fechas mixtas, duplicados, nulos y montos inválidos."""
    ts = F.coalesce(
        F.to_timestamp("timestamp", "yyyy-MM-dd HH:mm:ss"),
        F.to_timestamp("timestamp", "dd/MM/yyyy HH:mm"),
    )
    return (
        df.dropDuplicates(["transaction_id"])
        .withColumn("event_ts", ts)
        .withColumn("amount_cop", F.col("amount_cop").cast("double"))
        .withColumn("channel", F.lower(F.trim("channel")))
        .filter(F.col("event_ts").isNotNull())
        .filter(F.col("amount_cop").isNotNull() & (F.col("amount_cop") > 0))
        .filter(F.col("channel").isin(VALID_CHANNELS))
        .withColumn("event_date", F.to_date("event_ts"))
        .drop("timestamp")
    )


def daily_kpis(df: DataFrame) -> DataFrame:
    """Capa curated: KPIs diarios por canal."""
    return (
        df.groupBy("event_date", "channel")
        .agg(
            F.count("*").alias("n_transactions"),
            F.round(F.sum(F.when(F.col("status") == "approved", F.col("amount_cop"))), 2).alias("approved_volume_cop"),
            F.round(F.avg("amount_cop"), 2).alias("avg_ticket_cop"),
            F.round(F.avg(F.when(F.col("status") == "rejected", 1).otherwise(0)), 4).alias("rejection_rate"),
            F.countDistinct("user_id").alias("active_users"),
        )
        .orderBy("event_date", "channel")
    )


def quality_report(raw: DataFrame, clean: DataFrame) -> dict:
    """Métricas simples de calidad para auditar cada ejecución."""
    raw_n, clean_n = raw.count(), clean.count()
    return {
        "raw_rows": raw_n,
        "clean_rows": clean_n,
        "dropped_rows": raw_n - clean_n,
        "dropped_pct": round(100 * (raw_n - clean_n) / raw_n, 2) if raw_n else 0.0,
    }
