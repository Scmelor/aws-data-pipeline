import datetime as dt

import pytest
from pyspark.sql import SparkSession

from src.jobs.transform import clean_transactions, daily_kpis


@pytest.fixture(scope="session")
def spark():
    s = SparkSession.builder.master("local[1]").appName("tests").getOrCreate()
    yield s
    s.stop()


COLS = ["transaction_id", "user_id", "timestamp", "amount_cop", "channel", "city", "status"]


def test_clean_removes_bad_rows_and_duplicates(spark):
    rows = [
        ("T1", "U1", "2026-03-01 10:00:00", "1000", "app", "Medellín", "approved"),
        ("T1", "U1", "2026-03-01 10:00:00", "1000", "app", "Medellín", "approved"),  # duplicado
        ("T2", "U2", "01/03/2026 11:30", "2500", " QR ", "Bogotá", "rejected"),  # fecha alterna + canal sucio
        ("T3", "U3", "2026-03-01 12:00:00", "-50", "app", "Cali", "approved"),  # monto negativo
        ("T4", "U4", "2026-03-01 12:00:00", "", "app", "Cali", "approved"),  # nulo
        ("T5", "U5", "fecha-mala", "900", "app", "Cali", "approved"),  # fecha inválida
        ("T6", "U6", "2026-03-01 13:00:00", "700", "fax", "Cali", "approved"),  # canal inválido
    ]
    out = clean_transactions(spark.createDataFrame(rows, COLS))
    ids = sorted(r.transaction_id for r in out.collect())
    assert ids == ["T1", "T2"]
    t2 = out.filter("transaction_id = 'T2'").first()
    assert t2.channel == "qr"
    assert t2.event_date == dt.date(2026, 3, 1)


def test_daily_kpis(spark):
    rows = [
        ("T1", "U1", "2026-03-01 10:00:00", "1000", "app", "Medellín", "approved"),
        ("T2", "U1", "2026-03-01 11:00:00", "3000", "app", "Medellín", "rejected"),
    ]
    kpi = daily_kpis(clean_transactions(spark.createDataFrame(rows, COLS))).first()
    assert kpi.n_transactions == 2
    assert kpi.approved_volume_cop == 1000
    assert kpi.avg_ticket_cop == 2000
    assert kpi.rejection_rate == 0.5
    assert kpi.active_users == 1
