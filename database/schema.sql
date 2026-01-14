-- Legal Judgment RAG System - Database Schema
-- PostgreSQL with pgvector extension

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Judgments table
CREATE TABLE IF NOT EXISTS judgments (
    id SERIAL PRIMARY KEY,
    case_number VARCHAR(255) UNIQUE NOT NULL,
    title TEXT,
    parties TEXT,
    judgment_date DATE,
    court VARCHAR(100),
    judges TEXT[],
    year INTEGER,
    file_path TEXT,
    file_hash VARCHAR(64),
    total_chunks INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Judgment chunks (for retrieval)
CREATE TABLE IF NOT EXISTS judgment_chunks (
    id SERIAL PRIMARY KEY,
    judgment_id INTEGER REFERENCES judgments(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    page_number INTEGER,
    section_type VARCHAR(50),  -- 'facts', 'analysis', 'conclusion', 'headnote', etc.
    token_count INTEGER,
    embedding vector(384),  -- Using all-MiniLM-L6-v2 default dimension
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(judgment_id, chunk_index)
);

-- Legal sections reference (IPC, CrPC, Evidence Act, Constitution)
CREATE TABLE IF NOT EXISTS legal_sections (
    id SERIAL PRIMARY KEY,
    act_name VARCHAR(100) NOT NULL,
    section_number VARCHAR(50) NOT NULL,
    title TEXT,
    content TEXT,
    chapter VARCHAR(50),
    part VARCHAR(50),
    classification TEXT,
    punishment TEXT,
    triable_by TEXT,
    compoundable TEXT,
    metadata JSONB,
    embedding vector(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(act_name, section_number)
);

-- Named entities extracted from judgments
CREATE TABLE IF NOT EXISTS named_entities (
    id SERIAL PRIMARY KEY,
    judgment_id INTEGER REFERENCES judgments(id) ON DELETE CASCADE,
    chunk_id INTEGER REFERENCES judgment_chunks(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    entity_text TEXT NOT NULL,
    start_position INTEGER,
    end_position INTEGER,
    confidence FLOAT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Legal section references in judgments
CREATE TABLE IF NOT EXISTS judgment_section_refs (
    id SERIAL PRIMARY KEY,
    judgment_id INTEGER REFERENCES judgments(id) ON DELETE CASCADE,
    chunk_id INTEGER REFERENCES judgment_chunks(id) ON DELETE CASCADE,
    legal_section_id INTEGER REFERENCES legal_sections(id),
    mention_context TEXT,
    page_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Summaries (generated summaries)
CREATE TABLE IF NOT EXISTS summaries (
    id SERIAL PRIMARY KEY,
    judgment_id INTEGER REFERENCES judgments(id) ON DELETE CASCADE,
    summary_type VARCHAR(50),
    summary_text TEXT NOT NULL,
    key_points TEXT[],
    relevant_sections TEXT[],
    entities_extracted JSONB,
    retrieval_chunk_ids INTEGER[],
    model_used VARCHAR(100),
    prompt_template TEXT,
    metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(judgment_id, summary_type)
);

-- BM25 token index for judgments (for BM25 retrieval)
CREATE TABLE IF NOT EXISTS judgment_tokens (
    chunk_id INTEGER REFERENCES judgment_chunks(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    position INTEGER,
    PRIMARY KEY (chunk_id, token, position)
);

-- Indexes for judgments
CREATE INDEX IF NOT EXISTS idx_judgments_date ON judgments(judgment_date);
CREATE INDEX IF NOT EXISTS idx_judgments_case_number ON judgments(case_number);
CREATE INDEX IF NOT EXISTS idx_judgments_year ON judgments(year);
CREATE INDEX IF NOT EXISTS idx_judgments_court ON judgments(court);

-- Indexes for judgment_chunks
CREATE INDEX IF NOT EXISTS idx_judgment_chunks_judgment_id ON judgment_chunks(judgment_id);
CREATE INDEX IF NOT EXISTS idx_judgment_chunks_section_type ON judgment_chunks(section_type);
CREATE INDEX IF NOT EXISTS idx_judgment_chunks_embedding ON judgment_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_judgment_chunks_content_search ON judgment_chunks USING gin(content gin_trgm_ops);

-- Indexes for legal_sections
CREATE INDEX IF NOT EXISTS idx_legal_sections_act ON legal_sections(act_name);
CREATE INDEX IF NOT EXISTS idx_legal_sections_section_number ON legal_sections(section_number);
CREATE INDEX IF NOT EXISTS idx_legal_sections_embedding ON legal_sections USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Indexes for named_entities
CREATE INDEX IF NOT EXISTS idx_named_entities_judgment ON named_entities(judgment_id);
CREATE INDEX IF NOT EXISTS idx_named_entities_chunk ON named_entities(chunk_id);
CREATE INDEX IF NOT EXISTS idx_named_entities_type ON named_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_named_entities_text ON named_entities USING gin(entity_text gin_trgm_ops);

-- Indexes for judgment_section_refs
CREATE INDEX IF NOT EXISTS idx_judgment_section_refs_judgment ON judgment_section_refs(judgment_id);
CREATE INDEX IF NOT EXISTS idx_judgment_section_refs_chunk ON judgment_section_refs(chunk_id);
CREATE INDEX IF NOT EXISTS idx_judgment_section_refs_section ON judgment_section_refs(legal_section_id);

-- Indexes for summaries
CREATE INDEX IF NOT EXISTS idx_summaries_judgment ON summaries(judgment_id);
CREATE INDEX IF NOT EXISTS idx_summaries_type ON summaries(summary_type);

-- Indexes for BM25 tokens
CREATE INDEX IF NOT EXISTS idx_judgment_tokens_chunk ON judgment_tokens(chunk_id);
CREATE INDEX IF NOT EXISTS idx_judgment_tokens_token ON judgment_tokens(token);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for judgments
CREATE TRIGGER update_judgments_updated_at BEFORE UPDATE ON judgments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for easier querying
CREATE OR REPLACE VIEW judgment_with_metadata AS
SELECT 
    j.id,
    j.case_number,
    j.title,
    j.parties,
    j.judgment_date,
    j.court,
    j.judges,
    j.year,
    j.total_chunks,
    COUNT(DISTINCT jsr.legal_section_id) as referenced_sections_count,
    COUNT(DISTINCT ne.id) as entities_count
FROM judgments j
LEFT JOIN judgment_section_refs jsr ON j.id = jsr.judgment_id
LEFT JOIN named_entities ne ON j.id = ne.judgment_id
GROUP BY j.id, j.case_number, j.title, j.parties, j.judgment_date, j.court, j.judges, j.year, j.total_chunks;
