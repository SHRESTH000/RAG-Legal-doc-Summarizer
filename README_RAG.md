# Legal RAG System - Implementation Guide

## Overview

This is a comprehensive RAG (Retrieval-Augmented Generation) system for legal judgment summarization, specifically designed for Indian criminal judgments. The system uses hybrid retrieval (BM25 + Vector Search), NER, and LLM-based summarization.

## Quick Start

### 1. Prerequisites

- PostgreSQL 14+ with pgvector extension
- Python 3.9+
- 8GB+ RAM recommended

### 2. Installation

```bash
# Install dependencies
pip install -r requirements_rag.txt

# Install PostgreSQL extension (run in psql)
psql -d legal_rag -f database/schema.sql

# Download spaCy model (if using spaCy NER)
python -m spacy download en_core_web_sm
```

### 3. Configuration

1. Set environment variables:
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=legal_rag
export DB_USER=postgres
export DB_PASSWORD=your_password
```

2. Or edit `config/config.yaml` directly

### 4. Database Setup

```bash
# Create database
createdb legal_rag

# Run schema
psql -d legal_rag -f database/schema.sql

# Verify extensions
psql -d legal_rag -c "SELECT * FROM pg_extension WHERE extname IN ('vector', 'pg_trgm');"
```

### 5. Load Legal Datasets

```bash
# This will populate legal_sections table with IPC, CrPC, Evidence Act, Constitution
python scripts/load_legal_datasets.py
```

## Project Structure

```
legal_rag/
├── config/
│   └── config.yaml              # Configuration file
├── database/
│   ├── schema.sql               # Database schema
│   └── connection.py            # Database connection utilities
├── ner/
│   └── legal_ner.py             # NER module for legal entities
├── retrieval/
│   └── hybrid_retriever.py      # Hybrid BM25 + Vector retrieval
├── ingestion/                   # Data ingestion pipeline (to be implemented)
├── summarization/               # Summarization module (to be implemented)
├── evaluation/                  # Evaluation framework (to be implemented)
└── scripts/                     # Utility scripts
```

## Key Components

### 1. Database Schema
- `judgments`: Main judgment metadata
- `judgment_chunks`: Text chunks with embeddings
- `legal_sections`: IPC, CrPC, Evidence Act sections
- `named_entities`: Extracted entities
- `summaries`: Generated summaries

### 2. NER Module
Extracts:
- Legal sections (IPC, CrPC, Evidence Act)
- Case numbers
- Courts
- Statutes
- Legal terms
- Dates

### 3. Hybrid Retrieval
- **BM25**: Keyword-based retrieval
- **Vector Search**: Semantic similarity using pgvector
- **Fusion**: Weighted combination of both

## Usage Examples

### Using NER

```python
from ner.legal_ner import get_ner

ner = get_ner()
text = "The accused was convicted under Section 302 IPC..."
entities = ner.extract_entities(text)

for entity in entities:
    print(f"{entity.entity_type}: {entity.text}")
```

### Using Hybrid Retrieval

```python
from retrieval.hybrid_retriever import HybridRetriever

retriever = HybridRetriever(bm25_weight=0.4, vector_weight=0.6)

# Initialize BM25 (load documents first)
# retriever.initialize_bm25(documents, chunk_ids)

# Retrieve
results = retriever.retrieve("murder conviction", top_k=10)
for chunk_id, score in results:
    print(f"Chunk {chunk_id}: {score}")
```

## Next Steps

1. **Implement Data Ingestion Pipeline**
   - PDF extraction
   - Chunking
   - Embedding generation
   - Database storage

2. **Implement Summarization Module**
   - Context building
   - Prompt engineering
   - LLM integration
   - Output formatting

3. **Build Evaluation Framework**
   - Metrics calculation
   - Test suite
   - Benchmarking

## Documentation

See `RAG_IMPLEMENTATION_PLAN.md` for detailed implementation plan.

## Contributing

This is a work in progress. Follow the implementation phases outlined in the plan document.
