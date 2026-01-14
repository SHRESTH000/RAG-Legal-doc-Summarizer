# What is "Ingestion"? - Simple Answer

## Quick Answer

**"Ingest"** means: **Take PDF files and put their content into the database so the RAG system can search through them.**

## Analogy

Think of it like a library:
- **PDFs** = Books sitting on shelves (not searchable)
- **Ingestion** = Librarian reads books, creates index cards, organizes them
- **Database** = Card catalog (now you can search and find things)
- **RAG System** = Uses the catalog to find relevant books when you ask questions

## What Happens When You "Ingest" a Judgment

1. **Read PDF** → Extract text (like scanning the document)
2. **Find Information** → Extract case number, date, parties, etc.
3. **Break It Up** → Split into small searchable pieces (chunks)
4. **Create Search Index** → Convert chunks to numbers (embeddings) for AI search
5. **Extract Legal Terms** → Find all section numbers, case references, etc.
6. **Save Everything** → Store in database tables

## Result

**Before Ingestion:**
- PDF file exists, but system can't search it
- RAG has nothing to retrieve from

**After Ingestion:**
- Content is in database
- RAG can find and retrieve relevant parts
- You can query and get answers

## In Your System

- **Table**: `judgments` - stores judgment metadata
- **Table**: `judgment_chunks` - stores text pieces for search
- **Table**: `named_entities` - stores extracted legal terms

That's it! Ingestion = converting PDFs into searchable database content.
