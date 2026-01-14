# Using Ollama for Local Summarization

## Overview

Your summarization system now supports **Ollama** for running LLMs locally! This is perfect for using models like Mistral, GPT, OpenChat, etc. without API costs.

---

## Prerequisites

1. **Ollama Installed**
   - Download from: https://ollama.ai
   - Or install via package manager

2. **Ollama Running**
   ```bash
   ollama serve
   ```

3. **Models Pulled**
   ```bash
   ollama pull mistral
   ollama pull llama2
   # or any other model you have
   ```

4. **Python Package**
   ```bash
   pip install requests
   ```

---

## Quick Start

### 1. Check Available Models

```bash
python scripts/test_ollama_summarization.py
```

This will:
- Connect to Ollama
- List available models
- Test summarization with the first available model

### 2. Use Specific Model

```bash
python scripts/test_ollama_summarization.py --model mistral
```

Or in Python:

```python
from rag.integrated_rag_with_summarization import IntegratedRAGWithSummarization

system = IntegratedRAGWithSummarization(
    summarizer_model_type="ollama",
    summarizer_model_name="mistral"  # or "llama2", "openchat", etc.
)
```

### 3. Custom Ollama URL

If Ollama is running on a different port:

```bash
export OLLAMA_BASE_URL="http://localhost:11434"
python scripts/test_ollama_summarization.py
```

Or in Python:

```python
from summarization.legal_summarizer import LegalSummarizer

summarizer = LegalSummarizer(
    model_type="ollama",
    model_name="mistral",
    ollama_base_url="http://localhost:11434"
)
```

---

## Supported Models

Any model available in Ollama works! Common choices:

- **mistral** - Mistral 7B (good balance)
- **llama2** - LLaMA 2 (7B or 13B)
- **openchat** - OpenChat models
- **codellama** - Code-focused models
- **neural-chat** - Microsoft's Neural Chat
- **qwen** - Alibaba's Qwen models

To see all available:
```bash
ollama list
```

---

## Usage Example

```python
from rag.integrated_rag_with_summarization import IntegratedRAGWithSummarization
from database.connection import get_db_manager

# Initialize with Ollama
system = IntegratedRAGWithSummarization(
    rag_top_k=3,
    summarizer_model_type="ollama",
    summarizer_model_name="mistral",  # Your Ollama model
    compression_ratio=0.2
)

# Initialize BM25
db = get_db_manager()
chunks = db.execute_query("SELECT id, content FROM judgment_chunks LIMIT 10000")
documents = [row['content'] for row in chunks]
chunk_ids = [row['id'] for row in chunks]
system.initialize_bm25(documents, chunk_ids)

# Process query
query = "What are the legal provisions for murder conviction under IPC Section 302?"
result = system.process(query, generate_summary=True)

# Access summary
print(result['summary'])
print(result['summary_result'].case_summary)
print(result['summary_result'].key_issues)
```

---

## Configuration

### Environment Variables

```bash
# Ollama base URL (default: http://localhost:11434)
export OLLAMA_BASE_URL="http://localhost:11434"

# Database password
export DB_PASSWORD="postgres"
```

### Model Selection

The system will:
1. Connect to Ollama
2. List available models
3. Use specified model (or first available if not found)
4. Warn if model doesn't exist

---

## Performance Tips

### 1. Model Choice
- **Larger models** (13B+) = Better quality, slower
- **Smaller models** (7B) = Faster, good quality
- **Mistral 7B** = Recommended balance

### 2. Generation Parameters

Adjust in code:
```python
summarizer = LegalSummarizer(
    model_type="ollama",
    model_name="mistral",
    temperature=0.3,  # Lower = more focused
    max_length=512    # Max tokens
)
```

### 3. Hardware
- **CPU**: Works but slower
- **GPU**: Much faster (CUDA recommended)
- **RAM**: 8GB+ for 7B models, 16GB+ for 13B

---

## Troubleshooting

### Ollama Not Connecting

**Error**: "Could not connect to Ollama"

**Solutions**:
1. Check if Ollama is running: `ollama serve`
2. Verify URL: `curl http://localhost:11434/api/tags`
3. Check port: Default is 11434
4. Set custom URL: `export OLLAMA_BASE_URL="http://your-url:port"`

### Model Not Found

**Error**: "Model 'xyz' not found"

**Solutions**:
1. List models: `ollama list`
2. Pull model: `ollama pull model-name`
3. Use available model from list

### Slow Generation

**Solutions**:
1. Use smaller model (7B instead of 13B)
2. Reduce `max_length` parameter
3. Use GPU if available
4. Reduce `temperature` for faster generation

### Out of Memory

**Solutions**:
1. Use smaller model
2. Reduce `max_length`
3. Close other applications
4. Use quantized models (if available)

---

## Comparison: Ollama vs Other Backends

| Feature | Ollama | OpenAI | HuggingFace |
|---------|--------|--------|-------------|
| **Cost** | Free (local) | Paid API | Free (local) |
| **Privacy** | 100% local | Cloud | 100% local |
| **Setup** | Easy | Easy | Complex |
| **Speed** | Depends on hardware | Fast (cloud) | Depends on hardware |
| **Models** | Many available | GPT-3.5/4 | Any HuggingFace model |
| **Best For** | Privacy, cost | Quick testing | Custom models |

---

## Example Workflow

1. **Start Ollama**:
   ```bash
   ollama serve
   ```

2. **Pull Model** (if needed):
   ```bash
   ollama pull mistral
   ```

3. **Test**:
   ```bash
   python scripts/test_ollama_summarization.py --model mistral
   ```

4. **Use in Code**:
   ```python
   system = IntegratedRAGWithSummarization(
       summarizer_model_type="ollama",
       summarizer_model_name="mistral"
   )
   ```

---

## Benefits of Using Ollama

✅ **No API costs** - Run locally
✅ **Privacy** - Data stays on your machine
✅ **Multiple models** - Easy to switch between models
✅ **Offline capable** - Works without internet
✅ **Fast setup** - Simple installation

---

## Next Steps

1. **Test with your models**:
   ```bash
   python scripts/test_ollama_summarization.py
   ```

2. **Choose best model** for your use case

3. **Generate summaries** for evaluation

4. **Run BERTScore evaluation** with generated summaries

---

**You're all set! Ollama integration is ready to use with your local models!** 🚀
