#!/usr/bin/env bash
# Sube datos raw y código del Glue Job a S3.
# Requiere AWS CLI configurado (aws configure) — ⚠ nunca subas tus credenciales al repo.
set -euo pipefail

BUCKET="${1:?Uso: scripts/upload_to_s3.sh <nombre-del-bucket>}"

aws s3 cp data/raw/transactions.csv "s3://${BUCKET}/raw/transactions/transactions.csv"
zip -qr /tmp/src.zip src -x "*/__pycache__/*"
aws s3 cp /tmp/src.zip "s3://${BUCKET}/code/src.zip"
aws s3 cp glue/glue_job.py "s3://${BUCKET}/code/glue_job.py"
echo "Listo: s3://${BUCKET}/raw y s3://${BUCKET}/code"
