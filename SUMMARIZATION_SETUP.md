# Summarization Module Setup Guide

## Overview

The summarization module is now integrated with the RAG system. You can generate summaries of legal judgments using various LLM backends.

## Supported LLM Backends

### 1. OpenAI (Recommended for Testing)

**Setup:**
```bash
pip install openai
export OPENAI_API_KEY="your-api-key"
```

**Usage:**
```python
from rag.integrated_rag_with_summarization import IntegratedRAGWithSummarization

system = IntegratedRAGWithSummarization(
    summarizer_model_type="openai",
    summarizer_model_name="gpt-4"  # or "gpt-3.5-turbo"
)
```

### 2. HuggingFace Transformers (Open Source)

**Setup:**
```bash
pip install transformers torch
```

**Usage:**
```python
system = IntegratedRAGWithSummarization(
    summarizer_model_type="huggingface",
    summarizer_model_name="meta-llama/Llama-2-7b-chat-hf"  # or other models
)
```

**Recommended Models:**
- `meta-llama/Llama-2-7b-chat-hf` - LLaMA 2 (requires access)
- `mistralai/Mistral-7B-Instruct-v0.1` - Mistral (open)
- `microsoft/DialoGPT-large` - For dialogue

### 3. LLaMA (via llama.cpp)

**Setup:**
```bash
pip install llama-cpp-python
# Download LLaMA model (GGUF format)
```

**Usage:**
```python
system = IntegratedRAGWithSummarization(
    summarizer_model_type="llama",
    summarizer_model_name="/path/to/llama-model.gguf"
)
```

## Quick Start

### Basic Usage

```python
from rag.integrated_rag_with_summarization import IntegratedRAGWithSummarization
from database.connection import get_db_manager

# Initialize system
system = IntegratedRAGWithSummarization(
    rag_top_k=3,
    summarizer_model_type="openai",  # or "huggingface", "llama"
    summarizer_model_name="gpt-4"
)

# Initialize BM25
db = get_db_manager()
chunks = db.execute_query("SELECT id, content FROM judgment_chunks LIMIT 10000")
documents = [row['content'] for row in chunks]
chunk_ids = [row['id'] for row in chunks]
system.initialize_bm25(documents, chunk_ids)

# Process query/text
query = "What are the legal provisions for murder conviction under IPC Section 302?"
result = system.process(query, generate_summary=True)

# Access results
print("Summary:", result['summary'])
print("Case Summary:", result['summary_result'].case_summary)
print("Key Issues:", result['summary_result'].key_issues)
```

## Testing Without LLM

You can test the RAG part without LLM:

```python
result = system.process(query, generate_summary=False)
# Only RAG retrieval, no summarization
```

## Configuration Options

### Compression Ratio (0.05 to 0.5)

Following base paper's compression ratio constraint:

```python
system = IntegratedRAGWithSummarization(
    compression_ratio=0.2  # 20% of original length
)
```

### Temperature (for generation)

Lower temperature = more deterministic:
```python
from summarization.legal_summarizer import LegalSummarizer

summarizer = LegalSummarizer(
    model_type="openai",
    temperature=0.3  # Lower = more focused
)
```

## Integration with RAG

The summarization automatically uses:
- ✅ Retrieved judgment chunks
- ✅ Legal sections (IPC, CrPC, Evidence Act)
- ✅ Dark zone resolutions
- ✅ Extracted entities

All assembled context is passed to the LLM for summarization.

## Next Steps

1. **Configure LLM**: Set up your preferred LLM backend
2. **Test Summarization**: Run `python scripts/test_summarization.py`
3. **Generate Summaries**: Use integrated system for full pipeline
4. **Evaluate**: Set up BERTScore evaluation (next step)

## Files Created

- `summarization/legal_summarizer.py` - Core summarization module
- `rag/integrated_rag_with_summarization.py` - Integrated RAG + Summarization
- `scripts/test_summarization.py` - Test script
