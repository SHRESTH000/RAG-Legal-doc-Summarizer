# Legal RAG Implementation - Base Paper Aligned with Enhancements

## Overview

This implementation closely follows the methodology from the base paper **"Optimizing Legal Text Summarization Through Dynamic Retrieval-Augmented Generation and Domain-Specific Adaptation"** while adding enhancements:
- **Hybrid Retrieval**: BM25 + Vector Search (instead of BM25 only)
- **Enhanced NER**: More comprehensive legal entity extraction
- **Dynamic RAG**: Entity-aware real-time augmentation

## Base Paper Methodology (Summary)

### Key Components:
1. **Dynamic Legal RAG System**
   - BM25 retriever with top-3 chunk selection
   - Legal NER module for entity extraction
   - Real-time entity-aware augmentation
   - Identifies "dark zones" (unexplained statute-provision pairs)

2. **Legal-Aware Text Summarization**
   - Fine-tuned LLaMA 3.1-8B
   - Compression ratio: 0.05 to 0.5
   - Contextual enrichment from RAG

3. **Knowledge Sources**
   - Constitution of India
   - Civil Procedure Code (CPC)
   - Supreme Court judgments

4. **Performance**
   - BM25 found most effective (vs other retrievers)
   - BERTScore: 0.89 with LLaMA 3.1-8B + NER + Dynamic RAG

---

## Our Enhanced Implementation

### Enhancements Over Base Paper:

1. **Hybrid Retrieval (BM25 + Vector)**
   - Combines BM25's keyword precision with vector semantic understanding
   - Configurable weights (default: BM25=0.4, Vector=0.6)
   - Better handling of synonymy and semantic similarity

2. **Expanded Legal Datasets**
   - IPC (Indian Penal Code) - 302 sections
   - CrPC (Criminal Procedure Code) - 484 sections
   - Evidence Act - 167 sections
   - Constitution - 395 articles + 12 schedules
   - Supreme Court judgments

3. **Enhanced NER**
   - Multiple entity types
   - Section reference linking
   - Dark zone detection

4. **PostgreSQL Integration**
   - Efficient storage and retrieval
   - Metadata filtering
   - Scalable architecture

---

## Implementation Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Input: Legal Judgment                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Legal NER Module                                │
│  - Extract legal entities (sections, statutes, cases)        │
│  - Identify dark zones (unexplained references)              │
│  - Entity linking to knowledge base                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         Dynamic Query Enhancement                            │
│  - Expand query with extracted entities                      │
│  - Add section references                                    │
│  - Include legal terminology                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         Hybrid Retrieval System                              │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │   BM25       │         │   Vector     │                  │
│  │  (Base Paper)│────────▶│   (Enhanced) │                  │
│  │  Top-3/K     │  Merge  │   Semantic   │                  │
│  └──────────────┘         └──────────────┘                  │
│         │                          │                         │
│         └──────────┬───────────────┘                         │
│                    ▼                                         │
│         ┌────────────────────┐                               │
│         │  Score Fusion      │                               │
│         │  (Weighted)        │                               │
│         └────────────────────┘                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         Knowledge Base Retrieval                             │
│  - Constitution articles                                     │
│  - IPC/CrPC/Evidence Act sections                           │
│  - Related judgments                                         │
│  - Dark zone resolution                                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         Context Assembly                                     │
│  - Top-K chunks (default: 3, configurable)                   │
│  - Legal section references                                  │
│  - Entity annotations                                        │
│  - Metadata (case number, date, court, etc.)                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         Summarization Model                                  │
│  - Base: LLaMA 3.1-8B (or available LLM)                    │
│  - Compression ratio: 0.05-0.5                              │
│  - Legal-aware prompt                                        │
│  - Entity-enriched context                                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Final Summary                                   │
│  - Factually grounded                                        │
│  - Entity-linked                                            │
│  - Citation included                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Details

### 1. Dynamic Legal RAG System

```python
class DynamicLegalRAG:
    """
    Dynamic RAG system following base paper methodology
    Enhanced with hybrid retrieval (BM25 + Vector)
    """
    
    def __init__(self, 
                 top_k: int = 3,  # Base paper uses top-3
                 bm25_weight: float = 0.4,
                 vector_weight: float = 0.6,
                 compression_ratio: float = 0.1):
        self.ner = LegalNER()
        self.hybrid_retriever = HybridRetriever(
            bm25_weight=bm25_weight,
            vector_weight=vector_weight
        )
        self.top_k = top_k
        self.compression_ratio = compression_ratio
    
    def process_judgment(self, judgment_text: str):
        # 1. Extract entities (NER)
        entities = self.ner.extract_entities(judgment_text)
        
        # 2. Identify dark zones (unexplained references)
        dark_zones = self.identify_dark_zones(judgment_text, entities)
        
        # 3. Enhanced query construction
        query = self.build_enhanced_query(judgment_text, entities, dark_zones)
        
        # 4. Hybrid retrieval
        retrieved_chunks = self.hybrid_retriever.retrieve(query, top_k=self.top_k * 2)
        
        # 5. Select top-K (as per base paper)
        top_chunks = retrieved_chunks[:self.top_k]
        
        # 6. Resolve dark zones
        resolved_context = self.resolve_dark_zones(
            top_chunks, dark_zones, entities
        )
        
        return {
            'entities': entities,
            'dark_zones': dark_zones,
            'retrieved_chunks': top_chunks,
            'context': resolved_context
        }
```

### 2. Dark Zone Detection

```python
def identify_dark_zones(self, text: str, entities: List[Entity]) -> List[DarkZone]:
    """
    Identify dark zones: unexplained statute-provision pairs
    Following base paper methodology
    """
    dark_zones = []
    
    # Find section references
    sections = [e for e in entities if e.entity_type == EntityType.LEGAL_SECTION]
    
    for section in sections:
        # Check if section is explained in context
        context_window = self.get_context_window(text, section)
        
        if not self.is_explained(context_window, section):
            # Find related sections mentioned nearby
            related = self.find_related_sections(context_window, sections)
            
            dark_zones.append(DarkZone(
                section=section,
                context=context_window,
                related_sections=related,
                needs_retrieval=True
            ))
    
    return dark_zones
```

### 3. Enhanced Query Construction

```python
def build_enhanced_query(self, 
                        judgment_text: str,
                        entities: List[Entity],
                        dark_zones: List[DarkZone]) -> str:
    """
    Build enhanced query following base paper approach
    """
    query_parts = []
    
    # 1. Original judgment context (key sentences)
    key_sentences = self.extract_key_sentences(judgment_text)
    query_parts.extend(key_sentences)
    
    # 2. Extracted entities
    entity_texts = [e.text for e in entities if e.confidence > 0.8]
    query_parts.extend(entity_texts)
    
    # 3. Dark zone queries
    for dz in dark_zones:
        query_parts.append(f"{dz.section.text} {dz.context}")
    
    # 4. Legal terminology from judgment
    legal_terms = self.extract_legal_terms(judgment_text)
    query_parts.extend(legal_terms)
    
    return " ".join(query_parts)
```

### 4. Compression Ratio Constraint

```python
def apply_compression_ratio(self, 
                           original_length: int,
                           summary_length: int,
                           min_ratio: float = 0.05,
                           max_ratio: float = 0.5) -> bool:
    """
    Ensure compression ratio is within 0.05 to 0.5
    Following base paper constraint
    """
    ratio = summary_length / original_length
    
    if ratio < min_ratio:
        # Summary too short, need more content
        return False, "expand"
    elif ratio > max_ratio:
        # Summary too long, need compression
        return False, "compress"
    else:
        return True, "valid"
```

---

## Configuration (Base Paper Aligned)

```yaml
# Base paper configuration + enhancements
rag:
  # Base paper: top-3 chunk selection
  top_k_chunks: 3
  
  # Base paper: BM25 only, we use hybrid
  retrieval:
    type: "hybrid"  # "bm25", "vector", or "hybrid"
    bm25_weight: 0.4
    vector_weight: 0.6
    # Base paper uses BM25 only (weight=1.0)
  
  # Base paper: compression ratio 0.05-0.5
  summarization:
    compression_ratio:
      min: 0.05
      max: 0.5
      target: 0.1  # Typical target
  
  # Base paper: LLaMA 3.1-8B
  model:
    name: "llama-3.1-8b"  # or available alternative
    fine_tuned: true
  
  # Base paper: Legal NER
  ner:
    enabled: true
    detect_dark_zones: true
    entity_linking: true
  
  # Knowledge sources (base paper + our additions)
  knowledge_base:
    - "Constitution"
    - "IPC"  # Our addition
    - "CrPC"  # Our addition  
    - "Evidence_Act"  # Our addition
    - "CPC"  # Base paper mentions
    - "Supreme_Court_Judgments"
```

---

## Implementation Steps (Following Base Paper Flow)

### Phase 1: NER & Entity Extraction ✅ (Partially Complete)
- [x] Legal NER module
- [x] Entity extraction patterns
- [ ] Dark zone detection
- [ ] Entity linking to knowledge base

### Phase 2: Hybrid Retrieval System ✅ (Complete)
- [x] BM25 retriever
- [x] Vector retriever
- [x] Hybrid fusion
- [ ] Top-K selection (base paper: top-3)

### Phase 3: Knowledge Base Integration
- [x] Legal sections database (IPC, CrPC, Evidence Act, Constitution)
- [ ] Judgment chunks database
- [ ] Dark zone resolution system
- [ ] Entity-to-section linking

### Phase 4: Dynamic RAG Implementation
- [ ] Query enhancement with entities
- [ ] Dark zone identification
- [ ] Real-time context augmentation
- [ ] Top-K chunk selection

### Phase 5: Summarization Model
- [ ] LLaMA 3.1-8B integration (or alternative)
- [ ] Compression ratio enforcement
- [ ] Legal-aware prompting
- [ ] Entity-enriched context assembly

### Phase 6: Evaluation
- [ ] BERTScore calculation
- [ ] ROUGE metrics
- [ ] Legal accuracy evaluation
- [ ] Comparison with base paper results

---

## Key Differences from Base Paper

| Aspect | Base Paper | Our Implementation |
|--------|-----------|-------------------|
| Retrieval | BM25 only | **BM25 + Vector Hybrid** |
| Chunk Selection | Top-3 | Top-3 (configurable) |
| Knowledge Base | Constitution, CPC, Judgments | **+ IPC, CrPC, Evidence Act** |
| NER | Legal NER module | **Enhanced with dark zone detection** |
| Database | Not specified | **PostgreSQL with pgvector** |
| Model | LLaMA 3.1-8B | LLaMA 3.1-8B (or available LLM) |

---

## Expected Improvements

1. **Better Retrieval**: Hybrid approach should improve recall for semantically similar but lexically different queries
2. **More Complete Knowledge**: IPC, CrPC, Evidence Act provide comprehensive legal coverage
3. **Scalability**: PostgreSQL enables handling larger datasets efficiently
4. **Flexibility**: Configurable weights allow tuning for different use cases

---

## Next Steps

1. **Implement Dark Zone Detection**
   ```python
   # scripts/implement_dark_zones.py
   ```

2. **Enhance Query Construction**
   ```python
   # retrieval/query_enhancer.py
   ```

3. **Top-K Selection Module**
   ```python
   # retrieval/topk_selector.py
   ```

4. **Compression Ratio Validator**
   ```python
   # summarization/compression_validator.py
   ```

5. **LLM Integration**
   ```python
   # summarization/llm_summarizer.py
   ```

---

This implementation closely follows the base paper methodology while adding the requested hybrid retrieval enhancement and additional improvements.
