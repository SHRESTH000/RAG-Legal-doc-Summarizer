#!/bin/bash
# Batch ingestion script for criminal cases
# Windows PowerShell version below

# Set password
export DB_PASSWORD="postgres"

echo "Starting criminal cases ingestion..."

# Ingest from each year folder (20 files at a time to avoid overload)
python scripts/ingest_judgments.py --folder criminal_2024 --limit 20
python scripts/ingest_judgments.py --folder criminal_2023 --limit 20
python scripts/ingest_judgments.py --folder criminal_2022 --limit 20
python scripts/ingest_judgments.py --folder criminal_2021 --limit 20
python scripts/ingest_judgments.py --folder criminal_2020 --limit 20
python scripts/ingest_judgments.py --folder criminal_2019 --limit 20
python scripts/ingest_judgments.py --folder criminal_2025 --limit 20

echo "Batch ingestion complete. Check status with: python scripts/check_status.py"
