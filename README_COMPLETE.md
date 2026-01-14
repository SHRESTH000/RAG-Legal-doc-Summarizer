# Legal RAG System - Complete Implementation Guide

## Quick Start

### 1. Setup Database
```bash
# Create database
createdb legal_rag

# Install schema
psql -d legal_rag -f database/schema.sql

# Verify setup
python scripts/setup_database.py
```

### 2. Load Legal Datasets
```bash
python scripts/load_legal_datasets.py
```

### 3. Ingest Judgments
```bash
# Ingest from a year folder
python scripts/ingest_judgments.py --year 2024 --limit 10

# Or ingest criminal cases only
python scripts/ingest_judgments.py --year 2024 --criminal-only --limit 10

# Or ingest from specific folder
python scripts/ingest_judgments.py --folder criminal_2024 --limit 10
```

### 4. Run RAG Example
```bash
python scripts/run_rag_example.py
```

## Architecture

Following base paper methodology with enhancements:

```
Query/Text
    ↓
[Legal NER] → Extract entities
    ↓
[Dark Zone Detection] → Find unexplained references
    ↓
[Query Enhancement] → Build enriched query
    ↓
[Hybrid Retrieval] → BM25 + Vector Search
    ↓
[Top-K Selection] → Select top-3 chunks (base paper)
    ↓
[Legal Sections] → Retrieve relevant IPC/CrPC/Evidence Act sections
    ↓
[Dark Zone Resolution] → Resolve missing context
    ↓
[Context Assembly] → Combine all retrieved information
    ↓
[Summarization] → Generate summary (to be implemented)
```

## Key Features

### ✅ Implemented
- **Database Schema**: Complete PostgreSQL schema with pgvector
- **Legal NER**: Entity extraction from legal text
- **Dark Zone Detection**: Identifies unexplained legal references
- **Query Enhancement**: Builds enriched queries with entities and context
- **Hybrid Retrieval**: BM25 + Vector search (enhanced over base paper)
- **Legal Datasets**: IPC, CrPC, Evidence Act, Constitution
- **Judgment Ingestion**: Complete pipeline for PDF processing
- **Dynamic RAG**: Main RAG pipeline following base paper

### 🚧 To Implement
- **Summarization Module**: LLM integration with compression ratio
- **Evaluation Framework**: Metrics (BERTScore, ROUGE, etc.)
- **BM25 Index Initialization**: Build index from ingested chunks

## Usage Examples

### Using Dynamic RAG
```python
from rag.dynamic_legal_rag import DynamicLegalRAG

# Initialize (top-3 as per base paper)
rag = DynamicLegalRAG(top_k=3, bm25_weight=0.4, vector_weight=0.6)

# Process query
result = rag.process(
    query="What are the legal provisions for murder?",
    retrieve_legal_sections=True
)

# Access results
print(result.context)  # Assembled context
print(result.entities)  # Extracted entities
print(result.dark_zones)  # Detected dark zones
```

### Ingesting Judgments
```python
from ingestion.judgment_ingestor import JudgmentIngestor

ingestor = JudgmentIngestor()

# Single file
judgment_id = ingestor.ingest_pdf("path/to/judgment.pdf")

# Batch
results = ingestor.ingest_batch(["file1.pdf", "file2.pdf"])
```

## Configuration

Edit `config/config.yaml` to customize:
- Database connection
- Retrieval weights (BM25 vs Vector)
- Chunk size and overlap
- Embedding model
- Top-K value (base paper uses 3)

## Performance

Following base paper:
- **Top-K**: 3 chunks (configurable)
- **Compression Ratio**: 0.05-0.5 (to be enforced in summarization)
- **Retrieval**: Hybrid (BM25 + Vector) instead of BM25 only

## Next Steps

1. **Initialize BM25 Index**: After ingesting judgments, build BM25 index
2. **Implement Summarization**: Add LLM integration with compression ratio
3. **Evaluation**: Implement metrics (BERTScore target: 0.89 as per base paper)

## Files Structure

```
├── rag/
│   └── dynamic_legal_rag.py      # Main RAG pipeline
├── retrieval/
│   ├── hybrid_retriever.py       # BM25 + Vector retrieval
│   ├── dark_zone_detector.py     # Dark zone detection
│   ├── query_enhancer.py         # Query enhancement
│   └── chunking.py               # Text chunking
├── ingestion/
│   └── judgment_ingestor.py      # PDF ingestion pipeline
├── ner/
│   └── legal_ner.py              # Legal entity extraction
├── database/
│   ├── schema.sql                # Database schema
│   └── connection.py             # DB utilities
└── scripts/
    ├── ingest_judgments.py       # Ingestion script
    ├── load_legal_datasets.py    # Load legal sections
    └── run_rag_example.py        # Example usage
```

## Troubleshooting

### Database Connection
- Check PostgreSQL is running
- Verify credentials in config.yaml or environment variables
- Ensure pgvector extension is installed

### No Chunks Retrieved
- Ensure judgments are ingested first
- Check if chunks have embeddings
- Verify vector index is created

### Import Errors
- Run from project root directory
- Check all dependencies: `pip install -r requirements_rag.txt`

---

**Ready to use!** Start by ingesting judgments, then test the RAG system.
