# Legal RAG System - Quick Start Guide

## Overview

This guide will help you get started with the Legal RAG system for criminal judgment summarization.

## Prerequisites

1. **PostgreSQL 14+** with pgvector extension
2. **Python 3.9+**
3. Your existing PostgreSQL database connection details

## Step 1: Install Dependencies

```bash
pip install -r requirements_rag.txt
```

## Step 2: Set Up Database

### Option A: Using Environment Variables
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=legal_rag
export DB_USER=postgres
export DB_PASSWORD=your_password
```

### Option B: Edit config/config.yaml
Edit the database section in `config/config.yaml`

### Create Database and Schema
```bash
# Create database
createdb legal_rag

# Install pgvector extension (if not already installed)
# Download from: https://github.com/pgvector/pgvector

# Run schema
psql -d legal_rag -f database/schema.sql

# Verify setup
python scripts/setup_database.py
```

## Step 3: Load Legal Datasets

This will load IPC, CrPC, Evidence Act, and Constitution into your database:

```bash
python scripts/load_legal_datasets.py
```

**Note**: This script will only load sections that have actual content (skips placeholders).

## Step 4: Test Components

### Test NER Module
```python
from ner.legal_ner import get_ner

ner = get_ner()
text = """
The accused was convicted under Section 302 IPC for murder. 
The case Crl.A. No. 123/2020 was decided by the Supreme Court.
"""

entities = ner.extract_entities(text)
for entity in entities:
    print(f"{entity.entity_type.value}: {entity.text}")
```

### Test Database Connection
```python
from database.connection import get_db_manager

db = get_db_manager()
if db.check_connection():
    print("✅ Database connection successful")
    
    # Check legal sections count
    counts = db.execute_query("SELECT act_name, COUNT(*) FROM legal_sections GROUP BY act_name")
    for row in counts:
        print(f"{row['act_name']}: {row['count']} sections")
```

### Test Hybrid Retrieval (requires ingested data)
```python
from retrieval.hybrid_retriever import HybridRetriever

retriever = HybridRetriever(bm25_weight=0.4, vector_weight=0.6)

# Note: BM25 needs to be initialized with documents first
# For now, vector search will work if you have chunks in database

results = retriever.retrieve("murder conviction", top_k=10)
for chunk_id, score in results:
    print(f"Chunk {chunk_id}: Score {score:.4f}")
```

## Step 5: Next Steps

### Immediate Next Steps:

1. **Implement Data Ingestion Pipeline**
   - Extract text from PDF judgments
   - Create chunks
   - Generate embeddings
   - Store in database

2. **Build Summarization Module**
   - Create context builder
   - Design prompts
   - Integrate LLM

3. **Run End-to-End Test**
   - Ingest sample judgments
   - Test retrieval
   - Generate summaries
   - Evaluate results

## Project Structure

```
.
├── config/
│   └── config.yaml              # Configuration
├── database/
│   ├── schema.sql               # Database schema
│   └── connection.py            # DB utilities
├── ner/
│   └── legal_ner.py             # NER module
├── retrieval/
│   └── hybrid_retriever.py      # Hybrid retrieval
├── scripts/
│   ├── load_legal_datasets.py   # Load legal datasets
│   └── setup_database.py        # Setup verification
├── datasets/                    # Your existing datasets
├── RAG_IMPLEMENTATION_PLAN.md   # Detailed plan
├── IMPLEMENTATION_STATUS.md     # Progress tracking
└── requirements_rag.txt         # Dependencies
```

## Configuration

Key configuration options in `config/config.yaml`:

- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- **Retrieval Weights**: BM25=0.4, Vector=0.6
- **Chunk Size**: 512 tokens with 50 token overlap
- **Vector Similarity Threshold**: 0.7

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running
- Check credentials in config.yaml or environment variables
- Ensure database exists: `psql -l | grep legal_rag`

### pgvector Extension Missing
```sql
-- Install pgvector
CREATE EXTENSION vector;
```

### Import Errors
- Ensure you're in the project root directory
- Check that all dependencies are installed: `pip install -r requirements_rag.txt`

## Getting Help

1. Check `RAG_IMPLEMENTATION_PLAN.md` for detailed documentation
2. Review `IMPLEMENTATION_STATUS.md` for progress and next steps
3. Test individual components before integrating

## Example Workflow

```python
# 1. Initialize components
from database.connection import get_db_manager
from ner.legal_ner import get_ner
from retrieval.hybrid_retriever import HybridRetriever

db = get_db_manager()
ner = get_ner()
retriever = HybridRetriever()

# 2. Extract entities from query
query = "What are the legal provisions for murder conviction?"
entities = ner.extract_entities(query)
print(f"Found entities: {[e.text for e in entities]}")

# 3. Retrieve relevant chunks
results = retriever.retrieve(query, top_k=10)

# 4. Get chunk contents (when ingestion is implemented)
# chunks = db.execute_query(
#     "SELECT content FROM judgment_chunks WHERE id = ANY(%s)",
#     ([r[0] for r in results],)
# )

# 5. Build context and summarize (when summarization is implemented)
```

## Performance Tips

1. **Database Indexes**: Schema includes indexes, but monitor query performance
2. **Connection Pooling**: Already configured in DatabaseManager
3. **Batch Processing**: Use batching for embeddings and database inserts
4. **Caching**: Consider caching embeddings and frequent queries

## Next Implementation Tasks

See `IMPLEMENTATION_STATUS.md` for detailed task list. Priority order:

1. ✅ Foundation (COMPLETE)
2. ⏳ Data Ingestion Pipeline
3. ⏳ Summarization Module
4. ⏳ Evaluation Framework

---

**You're all set!** Start by setting up the database and loading legal datasets, then proceed with implementing the ingestion pipeline.
