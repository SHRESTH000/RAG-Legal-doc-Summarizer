# Database Setup Guide

## Quick Setup

### Option 1: Using Environment Variables (Recommended)

1. **Create a `.env` file** in the project root:
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=legal_rag
DB_USER=postgres
DB_PASSWORD=your_password_here
```

2. **Or set environment variables directly:**
```bash
# Windows PowerShell
$env:DB_HOST="localhost"
$env:DB_PORT="5432"
$env:DB_NAME="legal_rag"
$env:DB_USER="postgres"
$env:DB_PASSWORD="your_password"

# Linux/Mac
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=legal_rag
export DB_USER=postgres
export DB_PASSWORD=your_password
```

3. **Install python-dotenv** (if using .env file):
```bash
pip install python-dotenv
```

### Option 2: Edit config/config.yaml

Edit `config/config.yaml` and set:
```yaml
database:
  host: "localhost"
  port: 5432
  name: "legal_rag"
  user: "postgres"
  password: "your_password_here"
```

### Option 3: Use Interactive Script

```bash
python scripts/configure_database.py
```

## Database Creation

1. **Create the database:**
```bash
createdb legal_rag
```

2. **Install pgvector extension** (if not already installed):
```sql
-- Connect to PostgreSQL
psql -d legal_rag

-- Install extension
CREATE EXTENSION vector;
CREATE EXTENSION pg_trgm;
```

3. **Run schema:**
```bash
psql -d legal_rag -f database/schema.sql
```

## Verify Setup

```bash
python scripts/setup_database.py
```

This will check:
- ✅ Database connection
- ✅ pgvector extension
- ✅ All required tables
- ✅ Indexes

## Troubleshooting

### "no password supplied"
- Set DB_PASSWORD environment variable
- Or edit config/config.yaml
- Or create .env file

### "database does not exist"
```bash
createdb legal_rag
```

### "extension vector does not exist"
- Install pgvector: https://github.com/pgvector/pgvector
- Or use: `CREATE EXTENSION vector;` in psql

### Connection refused
- Check PostgreSQL is running: `pg_isready`
- Verify host and port in config

## Quick Test

After setup, test with:
```python
from database.connection import get_db_manager

db = get_db_manager()
if db.check_connection():
    print("✅ Database connection successful!")
```
