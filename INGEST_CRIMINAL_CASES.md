# Ingest Criminal Cases - Guide

## Available Criminal Cases

You have **1,705 criminal cases** already filtered in folders:

- `criminal_2019/` - 296 cases
- `criminal_2020/` - 139 cases  
- `criminal_2021/` - 203 cases
- `criminal_2022/` - 279 cases
- `criminal_2023/` - 276 cases
- `criminal_2024/` - 296 cases
- `criminal_2025/` - 216 cases

## Quick Start - Ingest Criminal Cases

### Option 1: Ingest specific year (recommended)
```powershell
$env:DB_PASSWORD="postgres"
python scripts/ingest_judgments.py --folder criminal_2024 --limit 50
```

### Option 2: Use batch script
```powershell
# Edit scripts/ingest_criminal_batch.ps1 and run:
. .\scripts\ingest_criminal_batch.ps1
```

### Option 3: Ingest all (one year at a time)
```powershell
$env:DB_PASSWORD="postgres"

# Start with recent years (most relevant)
python scripts/ingest_judgments.py --folder criminal_2024 --limit 100
python scripts/ingest_judgments.py --folder criminal_2023 --limit 100
python scripts/ingest_judgments.py --folder criminal_2022 --limit 100
```

## Check Progress

```powershell
python scripts/check_status.py
```

## Time Estimates

- **Per judgment**: ~1-2 minutes (depends on PDF size)
- **20 judgments**: ~20-40 minutes
- **100 judgments**: ~2-3 hours
- **All 1,705**: ~30-60 hours (process in batches!)

## Recommended Approach

1. **Start small**: Ingest 20-50 from each recent year
2. **Test RAG**: Make sure system works well
3. **Scale up**: Ingest more as needed
4. **Monitor**: Check status regularly

## Current Status

Run this to see current status:
```powershell
python scripts/check_status.py
```

The system will:
- ✅ Only ingest files not already in database
- ✅ Skip duplicates automatically
- ✅ Show progress as it processes
- ✅ Continue even if some files fail
