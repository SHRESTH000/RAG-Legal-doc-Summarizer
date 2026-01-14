# Comprehensive RAG Implementation Plan for Legal Judgment Summarization

## Executive Summary

This document outlines a comprehensive RAG (Retrieval-Augmented Generation) system for criminal judgment summarization, incorporating:
- Hybrid retrieval (BM25 + Vector Search)
- Named Entity Recognition (NER) for legal entities
- PostgreSQL for metadata and structured data
- Integration with legal datasets (IPC, CrPC, Evidence Act, Constitution)
- Advanced summarization with legal context awareness

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User Query                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Query Processing & Enhancement                  │
│  - Query expansion (legal terms)                            │
│  - NER on query (extract sections, entities)                │
│  - Query classification (criminal case type)                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Hybrid Retrieval System                         │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │   BM25       │         │   Vector     │                  │
│  │  (Rank-BM25) │────────▶│   Search     │                  │
│  │              │  Merge  │  (pgvector/  │                  │
│  │              │         │   FAISS)     │                  │
│  └──────────────┘         └──────────────┘                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         Context Assembly & Enrichment                        │
│  - Merge retrieved chunks                                   │
│  - Add relevant legal sections (IPC, CrPC, etc.)            │
│  - Include NER extracted entities                           │
│  - Metadata filtering (date, court, judge, etc.)            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         LLM-Based Summarization                             │
│  - Context-aware prompt engineering                         │
│  - Legal domain fine-tuning (optional)                      │
│  - Multi-stage summarization (extract → abstract)           │
│  - Citation and reference generation                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Output & Post-Processing                        │
│  - Summary validation                                       │
│  - Entity linking                                           │
│  - Formatting (structured output)                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack

### Core Components
- **Python 3.9+**
- **PostgreSQL 14+** (with pgvector extension for vector search)
- **LangChain** - LLM orchestration and chains
- **FAISS/ChromaDB** - Vector database (alternative to pgvector)
- **Rank-BM25** - BM25 implementation
- **spaCy/Transformers** - NER models
- **Sentence Transformers** - Embeddings
- **LLM**: OpenAI GPT-4/Claude/LLama2 (legal domain)

### Additional Libraries
- **psycopg2** - PostgreSQL adapter
- **pgvector** - Vector similarity search in PostgreSQL
- **pdfplumber/pypdf** - PDF extraction
- **tiktoken** - Token counting
- **pydantic** - Data validation
- **fastapi** - API framework (optional)

---

## 3. Database Schema Design (PostgreSQL)

### 3.1 Core Tables

```sql
-- Judgments table
CREATE TABLE judgments (
    id SERIAL PRIMARY KEY,
    case_number VARCHAR(255) UNIQUE NOT NULL,
    title TEXT,
    parties TEXT,
    judgment_date DATE,
    court VARCHAR(100),
    judges TEXT[],  -- Array of judge names
    year INTEGER,
    file_path TEXT,
    file_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Judgment chunks (for retrieval)
CREATE TABLE judgment_chunks (
    id SERIAL PRIMARY KEY,
    judgment_id INTEGER REFERENCES judgments(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    page_number INTEGER,
    section_type VARCHAR(50),  -- 'facts', 'analysis', 'conclusion', etc.
    token_count INTEGER,
    embedding vector(384),  -- or 768/1536 depending on model
    metadata JSONB,  -- Additional metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(judgment_id, chunk_index)
);

-- Indexes
CREATE INDEX idx_judgment_chunks_judgment_id ON judgment_chunks(judgment_id);
CREATE INDEX idx_judgment_chunks_embedding ON judgment_chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_judgments_date ON judgments(judgment_date);
CREATE INDEX idx_judgments_case_number ON judgments(case_number);
CREATE INDEX idx_judgments_year ON judgments(year);

-- Legal sections reference (IPC, CrPC, etc.)
CREATE TABLE legal_sections (
    id SERIAL PRIMARY KEY,
    act_name VARCHAR(100) NOT NULL,  -- 'IPC', 'CrPC', 'Evidence Act', 'Constitution'
    section_number VARCHAR(50) NOT NULL,
    title TEXT,
    content TEXT,
    chapter VARCHAR(50),
    part VARCHAR(50),
    metadata JSONB,
    embedding vector(384),
    UNIQUE(act_name, section_number)
);

CREATE INDEX idx_legal_sections_act ON legal_sections(act_name);
CREATE INDEX idx_legal_sections_embedding ON legal_sections USING ivfflat (embedding vector_cosine_ops);

-- Named entities extracted from judgments
CREATE TABLE named_entities (
    id SERIAL PRIMARY KEY,
    judgment_id INTEGER REFERENCES judgments(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,  -- 'PERSON', 'SECTION', 'CASE_NUMBER', 'COURT', etc.
    entity_text TEXT NOT NULL,
    start_position INTEGER,
    end_position INTEGER,
    confidence FLOAT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_named_entities_judgment ON named_entities(judgment_id);
CREATE INDEX idx_named_entities_type ON named_entities(entity_type);
CREATE INDEX idx_named_entities_text ON named_entities USING gin(entity_text gin_trgm_ops);

-- Legal section references in judgments
CREATE TABLE judgment_section_refs (
    id SERIAL PRIMARY KEY,
    judgment_id INTEGER REFERENCES judgments(id) ON DELETE CASCADE,
    legal_section_id INTEGER REFERENCES legal_sections(id),
    mention_context TEXT,
    page_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_judgment_section_refs_judgment ON judgment_section_refs(judgment_id);
CREATE INDEX idx_judgment_section_refs_section ON judgment_section_refs(legal_section_id);

-- Summaries (generated summaries)
CREATE TABLE summaries (
    id SERIAL PRIMARY KEY,
    judgment_id INTEGER REFERENCES judgments(id) ON DELETE CASCADE,
    summary_type VARCHAR(50),  -- 'extractive', 'abstractive', 'hybrid'
    summary_text TEXT NOT NULL,
    key_points TEXT[],
    relevant_sections TEXT[],
    entities_extracted JSONB,
    retrieval_chunks INTEGER[],  -- IDs of chunks used
    model_used VARCHAR(100),
    prompt_template TEXT,
    metrics JSONB,  -- ROUGE, BLEU, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(judgment_id, summary_type)
);

CREATE INDEX idx_summaries_judgment ON summaries(judgment_id);

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For text similarity
```

---

## 4. Named Entity Recognition (NER) Module

### 4.1 Legal Entity Types

```python
LEGAL_ENTITY_TYPES = {
    'PERSON': ['Judge names', 'Lawyer names', 'Party names'],
    'CASE_NUMBER': ['Crl.A. No.', 'W.P. No.', 'SLP No.'],
    'LEGAL_SECTION': ['IPC Section', 'CrPC Section', 'Evidence Act Section'],
    'COURT': ['Supreme Court', 'High Court', 'District Court'],
    'DATE': ['Judgment dates', 'Case dates'],
    'PENALTY': ['Punishment', 'Fine amounts', 'Imprisonment'],
    'LEGAL_TERM': ['Acquittal', 'Conviction', 'Bail', 'Appeal'],
    'STATUTE': ['Indian Penal Code', 'Criminal Procedure Code'],
    'ORGANIZATION': ['Police stations', 'Government bodies']
}
```

### 4.2 NER Implementation

```python
# ner_module.py structure
class LegalNER:
    def __init__(self):
        # Use spaCy model + custom rules
        # OR fine-tuned transformer model (BERT, RoBERTa)
        pass
    
    def extract_entities(self, text: str) -> List[Entity]:
        # Extract all legal entities
        pass
    
    def extract_sections(self, text: str) -> List[SectionReference]:
        # Extract IPC/CrPC section references
        pass
    
    def link_entities(self, entities: List[Entity]) -> List[LinkedEntity]:
        # Link entities to knowledge base
        pass
```

---

## 5. Data Ingestion Pipeline

### 5.1 Pipeline Stages

1. **PDF Extraction**
   - Extract full text from PDFs
   - Preserve structure (headings, sections)
   - Extract metadata (case number, date, parties)

2. **Preprocessing**
   - Clean text (remove headers/footers)
   - Sentence segmentation
   - Paragraph identification
   - Section detection (facts, analysis, conclusion)

3. **Chunking Strategy**
   - Semantic chunking (preserve context)
   - Overlapping chunks (sliding window)
   - Chunk size: 500-1000 tokens
   - Metadata preservation

4. **NER & Entity Extraction**
   - Extract all legal entities
   - Identify section references
   - Store in database

5. **Embedding Generation**
   - Generate embeddings for chunks
   - Use legal domain embeddings if available
   - Store in PostgreSQL (pgvector)

6. **Indexing**
   - Create BM25 index
   - Vector index (IVFFlat/HNSW)
   - Metadata indexes

---

## 6. Hybrid Retrieval System

### 6.1 BM25 Component

```python
from rank_bm25 import BM25Okapi

class BM25Retriever:
    def __init__(self):
        self.bm25 = None
        self.corpus = []
    
    def build_index(self, documents: List[str]):
        # Tokenize documents
        tokenized_corpus = [self.tokenize(doc) for doc in documents]
        self.bm25 = BM25Okapi(tokenized_corpus)
        self.corpus = documents
    
    def retrieve(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        tokenized_query = self.tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(idx, scores[idx]) for idx in top_indices]
```

### 6.2 Vector Search Component

```python
from sentence_transformers import SentenceTransformer
import pgvector

class VectorRetriever:
    def __init__(self, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
    
    def retrieve(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        query_embedding = self.model.encode(query)
        # PostgreSQL vector search query
        # SELECT id, 1 - (embedding <=> %s) as similarity
        # FROM judgment_chunks
        # ORDER BY embedding <=> %s
        # LIMIT %s
        pass
```

### 6.3 Hybrid Fusion

```python
class HybridRetriever:
    def __init__(self, bm25_weight: float = 0.4, vector_weight: float = 0.6):
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.bm25_retriever = BM25Retriever()
        self.vector_retriever = VectorRetriever()
    
    def retrieve(self, query: str, top_k: int = 20) -> List[Tuple[int, float]]:
        # Get results from both retrievers
        bm25_results = self.bm25_retriever.retrieve(query, top_k * 2)
        vector_results = self.vector_retriever.retrieve(query, top_k * 2)
        
        # Normalize scores
        bm25_scores = self._normalize_scores(bm25_results)
        vector_scores = self._normalize_scores(vector_results)
        
        # Combine results
        combined_scores = {}
        for idx, score in bm25_scores.items():
            combined_scores[idx] = self.bm25_weight * score
        for idx, score in vector_scores.items():
            combined_scores[idx] = combined_scores.get(idx, 0) + self.vector_weight * score
        
        # Sort and return top_k
        sorted_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]
```

---

## 7. Context Assembly & Enrichment

### 7.1 Context Builder

```python
class ContextBuilder:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def build_context(
        self, 
        retrieved_chunks: List[Dict],
        query: str,
        max_context_length: int = 4000
    ) -> str:
        context_parts = []
        
        # 1. Add retrieved judgment chunks
        for chunk in retrieved_chunks:
            context_parts.append(f"[Judgment Excerpt]\n{chunk['content']}")
        
        # 2. Add relevant legal sections
        entities = self.extract_entities_from_query(query)
        legal_sections = self.get_relevant_sections(entities)
        for section in legal_sections:
            context_parts.append(f"[Legal Section: {section['act_name']} Section {section['section_number']}]\n{section['content']}")
        
        # 3. Add metadata
        metadata = self.get_judgment_metadata(retrieved_chunks[0]['judgment_id'])
        context_parts.append(f"[Metadata]\nCase: {metadata['case_number']}\nDate: {metadata['judgment_date']}\nCourt: {metadata['court']}")
        
        # Combine and truncate if needed
        full_context = "\n\n".join(context_parts)
        return self._truncate_context(full_context, max_context_length)
```

---

## 8. Summarization Module

### 8.1 Prompt Engineering

```python
LEGAL_SUMMARY_PROMPT = """
You are an expert legal analyst specializing in Indian criminal law. 
Your task is to summarize the following criminal judgment.

Context Information:
{context}

Instructions:
1. Provide a concise summary of the case facts
2. Identify key legal issues and arguments
3. Summarize the court's reasoning and decision
4. List relevant legal sections cited (IPC, CrPC, Evidence Act)
5. Extract key entities (parties, judges, dates, case numbers)
6. Highlight the final judgment/order

Format your summary as:
- Case Summary: [2-3 sentences]
- Key Issues: [Bullet points]
- Legal Analysis: [2-3 paragraphs]
- Relevant Sections: [List of sections]
- Judgment: [Final decision]
- Key Entities: [Structured list]

Ensure accuracy and legal correctness. Cite specific sections and precedents mentioned.
"""

class LegalSummarizer:
    def __init__(self, llm_model):
        self.llm = llm_model
        self.prompt_template = LEGAL_SUMMARY_PROMPT
    
    def summarize(self, context: str, judgment_metadata: Dict) -> Dict:
        prompt = self.prompt_template.format(context=context)
        
        # Call LLM
        response = self.llm.generate(prompt)
        
        # Parse structured output
        summary = self._parse_summary(response)
        
        # Extract entities
        summary['entities'] = self._extract_entities_from_summary(response)
        
        return summary
```

### 8.2 Multi-Stage Summarization

```python
class MultiStageSummarizer:
    def __init__(self):
        self.extractive_stage = ExtractiveSummarizer()
        self.abstractive_stage = AbstractiveSummarizer()
    
    def summarize(self, text: str) -> Dict:
        # Stage 1: Extractive (identify important sentences)
        important_sentences = self.extractive_stage.extract(text)
        
        # Stage 2: Abstractive (generate coherent summary)
        summary = self.abstractive_stage.generate(important_sentences)
        
        return summary
```

---

## 9. Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- [ ] Set up PostgreSQL database with schema
- [ ] Install and configure pgvector extension
- [ ] Create data models (Pydantic)
- [ ] Implement basic PDF extraction
- [ ] Set up database connection utilities

### Phase 2: Data Ingestion (Weeks 3-4)
- [ ] Build PDF extraction pipeline
- [ ] Implement chunking strategy
- [ ] Create embedding generation pipeline
- [ ] Build data ingestion scripts
- [ ] Ingest sample judgments (100-500)

### Phase 3: NER Implementation (Week 5)
- [ ] Fine-tune or configure NER model
- [ ] Implement entity extraction
- [ ] Build entity linking system
- [ ] Create entity storage pipeline
- [ ] Test and validate NER accuracy

### Phase 4: Retrieval System (Weeks 6-7)
- [ ] Implement BM25 retriever
- [ ] Implement vector retriever (pgvector)
- [ ] Build hybrid fusion mechanism
- [ ] Create query enhancement module
- [ ] Test retrieval performance

### Phase 5: Summarization (Weeks 8-9)
- [ ] Design prompt templates
- [ ] Implement context builder
- [ ] Build summarization pipeline
- [ ] Add multi-stage summarization
- [ ] Implement output formatting

### Phase 6: Integration & Testing (Weeks 10-11)
- [ ] Integrate all components
- [ ] Create API endpoints (FastAPI)
- [ ] Build evaluation framework
- [ ] Test end-to-end pipeline
- [ ] Performance optimization

### Phase 7: Deployment & Monitoring (Week 12)
- [ ] Deploy system
- [ ] Set up monitoring
- [ ] Create user interface (optional)
- [ ] Documentation
- [ ] Production optimization

---

## 10. Evaluation Metrics

### 10.1 Retrieval Metrics
- **Precision@K**: Relevance of top-K retrieved documents
- **Recall@K**: Coverage of relevant documents
- **NDCG**: Normalized Discounted Cumulative Gain
- **MRR**: Mean Reciprocal Rank

### 10.2 Summarization Metrics
- **ROUGE-L**: Longest common subsequence
- **ROUGE-1/2**: N-gram overlap
- **BLEU**: N-gram precision
- **BERTScore**: Semantic similarity
- **Legal Accuracy**: Manual evaluation of legal correctness

### 10.3 NER Metrics
- **Precision/Recall/F1**: Per entity type
- **Entity Linking Accuracy**: Correctness of entity resolution

---

## 11. Additional Datasets & Resources Needed

### 11.1 Recommended Additions

1. **Legal Precedents Database**
   - Landmark criminal cases
   - Frequently cited judgments
   - Case law relationships

2. **Legal Vocabulary/Glossary**
   - Standard legal terms
   - Synonym mapping
   - Term hierarchies

3. **Judge & Lawyer Database**
   - Historical judge information
   - Specialization areas

4. **Case Citation Network**
   - Which cases cite which
   - Citation frequency

5. **Legal Domain Embeddings**
   - Fine-tuned embeddings on legal corpus
   - Better semantic understanding

### 11.2 External APIs/Resources
- **India Code API** (if available) - For legal section text
- **Supreme Court Database** - Official case data
- **Legal Lexicons** - Domain-specific word lists

---

## 12. Code Structure

```
legal_rag/
├── config/
│   ├── database.yaml
│   ├── models.yaml
│   └── prompts.yaml
├── database/
│   ├── schema.sql
│   ├── migrations/
│   └── connection.py
├── ingestion/
│   ├── pdf_extractor.py
│   ├── preprocessor.py
│   ├── chunker.py
│   ├── embedder.py
│   └── pipeline.py
├── ner/
│   ├── models/
│   ├── extractor.py
│   ├── entity_linker.py
│   └── utils.py
├── retrieval/
│   ├── bm25_retriever.py
│   ├── vector_retriever.py
│   ├── hybrid_retriever.py
│   └── query_enhancer.py
├── summarization/
│   ├── context_builder.py
│   ├── prompt_templates.py
│   ├── summarizer.py
│   └── post_processor.py
├── evaluation/
│   ├── metrics.py
│   ├── test_suite.py
│   └── benchmarks.py
├── api/
│   ├── main.py
│   ├── routes.py
│   └── models.py
└── utils/
    ├── logger.py
    └── helpers.py
```

---

## 13. Next Steps

1. **Review and approve this plan**
2. **Set up development environment**
3. **Create database schema**
4. **Start with Phase 1 implementation**
5. **Iterative development and testing**

---

## 14. Risk Mitigation

- **Data Quality**: Implement validation at each pipeline stage
- **Scalability**: Design for batch processing, consider async operations
- **Cost**: Monitor LLM API costs, implement caching
- **Accuracy**: Continuous evaluation and model improvement
- **Legal Compliance**: Ensure proper handling of legal data

---

This plan provides a comprehensive roadmap for building a production-ready RAG system for legal judgment summarization. Each phase builds upon the previous one, ensuring systematic development and testing.
