"""Genera un dataset SINTÉTICO de transacciones de una billetera digital.

Los datos son ficticios (no provienen de ninguna empresa real). Incluye
problemas de calidad a propósito (duplicados, nulos, montos negativos,
fechas en formatos mixtos) para que el pipeline tenga algo que limpiar.

Uso:
    python scripts/generate_data.py --rows 50000 --out data/raw/transactions.csv
"""

import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

CHANNELS = ["app", "qr", "pse", "cash_in", "p2p"]
CITIES = ["Medellín", "Bogotá", "Cali", "Barranquilla", "Bucaramanga", "Pereira"]
STATUSES = ["approved", "approved", "approved", "approved", "rejected", "pending"]


def generate(rows: int, out: Path, seed: int = 42) -> None:
    random.seed(seed)
    out.parent.mkdir(parents=True, exist_ok=True)
    start = datetime(2026, 1, 1)
    records = []
    for i in range(rows):
        ts = start + timedelta(seconds=random.randint(0, 180 * 24 * 3600))
        # Formatos de fecha mixtos (problema de calidad intencional)
        ts_str = ts.strftime("%Y-%m-%d %H:%M:%S") if random.random() > 0.05 else ts.strftime("%d/%m/%Y %H:%M")
        amount = round(random.lognormvariate(10.5, 1.0), 2)
        if random.random() < 0.01:
            amount = -amount  # montos inválidos
        records.append(
            {
                "transaction_id": f"TX{i:08d}",
                "user_id": f"U{random.randint(1, rows // 10):06d}",
                "timestamp": ts_str,
                "amount_cop": amount if random.random() > 0.01 else "",  # nulos
                "channel": random.choice(CHANNELS).upper() if random.random() < 0.1 else random.choice(CHANNELS),
                "city": random.choice(CITIES),
                "status": random.choice(STATUSES),
            }
        )
    # Duplicados exactos (~2 %)
    records += random.sample(records, k=max(1, rows // 50))
    random.shuffle(records)

    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
    print(f"{len(records)} filas escritas en {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument("--out", type=Path, default=Path("data/raw/transactions.csv"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    generate(args.rows, args.out, args.seed)
