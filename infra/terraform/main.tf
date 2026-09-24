# Infraestructura del data lake: S3 (raw/clean/curated), Glue Catalog + Crawler, Athena.
# ⚠ Genera costos mínimos si se deja encendido. Ejecuta `terraform destroy` al terminar.

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "project" {
  type    = string
  default = "scmelor-data-pipeline"
}

resource "aws_s3_bucket" "lake" {
  bucket        = "${var.project}-lake"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "lake" {
  bucket                  = aws_s3_bucket.lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lake" {
  bucket = aws_s3_bucket.lake.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_glue_catalog_database" "db" {
  name = "transactions_db"
}

data "aws_iam_policy_document" "glue_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["glue.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "glue" {
  name               = "${var.project}-glue-role"
  assume_role_policy = data.aws_iam_policy_document.glue_assume.json
}

resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy" "glue_s3" {
  name = "lake-access"
  role = aws_iam_role.glue.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
      Resource = [aws_s3_bucket.lake.arn, "${aws_s3_bucket.lake.arn}/*"]
    }]
  })
}

resource "aws_glue_crawler" "clean" {
  name          = "${var.project}-clean-crawler"
  role          = aws_iam_role.glue.arn
  database_name = aws_glue_catalog_database.db.name

  s3_target {
    path = "s3://${aws_s3_bucket.lake.bucket}/clean/"
  }
  s3_target {
    path = "s3://${aws_s3_bucket.lake.bucket}/curated/"
  }
}

resource "aws_glue_job" "etl" {
  name              = "${var.project}-etl"
  role_arn          = aws_iam_role.glue.arn
  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 15

  command {
    script_location = "s3://${aws_s3_bucket.lake.bucket}/code/glue_job.py"
    python_version  = "3"
  }

  default_arguments = {
    "--extra-py-files" = "s3://${aws_s3_bucket.lake.bucket}/code/src.zip"
    "--RAW_PATH"       = "s3://${aws_s3_bucket.lake.bucket}/raw/transactions/"
    "--CLEAN_PATH"     = "s3://${aws_s3_bucket.lake.bucket}/clean/transactions/"
    "--CURATED_PATH"   = "s3://${aws_s3_bucket.lake.bucket}/curated/daily_kpis/"
  }
}

resource "aws_athena_workgroup" "wg" {
  name          = "${var.project}-wg"
  force_destroy = true
  configuration {
    result_configuration {
      output_location = "s3://${aws_s3_bucket.lake.bucket}/athena-results/"
    }
  }
}

output "lake_bucket" {
  value = aws_s3_bucket.lake.bucket
}
