# What is "Ingestion"?

## Definition

**Ingestion** = The process of taking raw PDF judgment files and converting them into structured, searchable data in your database.

## Ingestion Process (Step-by-Step)

### 1. **PDF Extraction**
   - Reads PDF files from your folders (e.g., `judgments_2024/`, `criminal_2024/`)
   - Extracts text content from PDFs
   - Handles different PDF formats and quality

### 2. **Metadata Extraction**
   - Extracts case number (e.g., "Crl.A. No. 123/2024")
   - Extracts parties (Plaintiff vs Defendant)
   - Extracts judgment date
   - Extracts court name
   - Extracts judge names

### 3. **Text Processing**
   - Cleans and preprocesses the text
   - Identifies document sections (facts, analysis, conclusion)
   - Handles formatting issues

### 4. **Chunking**
   - Splits long judgment text into smaller chunks (512 tokens each)
   - Maintains context with overlapping chunks
   - Preserves sentence boundaries
   - Marks section types (facts, analysis, etc.)

### 5. **Embedding Generation**
   - Converts each chunk into a vector embedding (384 dimensions)
   - Uses sentence-transformers model
   - Enables semantic similarity search

### 6. **Entity Extraction (NER)**
   - Extracts legal entities from text:
     - Legal sections (IPC 302, CrPC 154, etc.)
     - Case numbers
     - Court names
     - Legal terms
     - Dates, etc.

### 7. **Database Storage**
   - Stores judgment metadata in `judgments` table
   - Stores chunks in `judgment_chunks` table
   - Stores embeddings for vector search
   - Stores extracted entities in `named_entities` table
   - Links entities to chunks and judgments

## Why Ingestion is Important

Without ingestion:
- ❌ PDFs are just files - not searchable
- ❌ No way to retrieve specific content
- ❌ Can't use RAG system
- ❌ No semantic search possible

After ingestion:
- ✅ All judgments in searchable database
- ✅ Can retrieve relevant chunks for queries
- ✅ BM25 keyword search works
- ✅ Vector semantic search works
- ✅ Entities are extracted and linked
- ✅ RAG system can find relevant context

## What Gets Stored

### `judgments` table:
- Case number, title, parties, date, court, judges
- File path, file hash

### `judgment_chunks` table:
- Text content of each chunk
- Embeddings (for vector search)
- Section type, page number
- Metadata

### `named_entities` table:
- All extracted entities
- Entity types and positions
- Confidence scores

## Ingestion Statistics

Currently ingested:
- **Judgments**: 2
- **Chunks**: 711
- **Entities**: 83

With more ingestion:
- More judgments = Better retrieval coverage
- More diverse legal cases
- Better context for RAG queries
- More complete knowledge base
