"""
Judgment Ingestion Pipeline
Extracts, chunks, embeds, and stores judgments in database
"""

import os
import sys
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

# Fix import conflict
project_root = Path(__file__).parent.parent
if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from database.connection import get_db_manager
from sentence_transformers import SentenceTransformer
from ner.legal_ner import get_ner
import json
from retrieval.chunking import LegalChunker

logger = logging.getLogger(__name__)


class JudgmentIngestor:
    """
    Ingests legal judgments into the database
    
    Pipeline:
    1. Extract text from PDF
    2. Extract metadata (case number, parties, date, etc.)
    3. Chunk text
    4. Generate embeddings
    5. Store in database
    """
    
    def __init__(self,
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
                 chunk_size: int = 512,
                 chunk_overlap: int = 50):
        """
        Initialize ingestor
        
        Args:
            embedding_model: Sentence transformer model
            chunk_size: Size of chunks in tokens
            chunk_overlap: Overlap between chunks in tokens
        """
        self.db = get_db_manager()
        self.embedder = SentenceTransformer(embedding_model)
        self.ner = get_ner()
        self.chunker = LegalChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.embedding_dim = self.embedder.get_sentence_embedding_dimension()
        
        logger.info(f"JudgmentIngestor initialized with model: {embedding_model}")
    
    def ingest_pdf(self, pdf_path: str) -> Optional[int]:
        """
        Ingest a single PDF judgment
        
        Returns:
            Judgment ID if successful, None otherwise
        """
        try:
            # Extract text
            text = self._extract_pdf_text(pdf_path)
            if not text or len(text) < 100:
                logger.warning(f"Insufficient text extracted from {pdf_path}")
                return None
            
            # Extract metadata
            metadata = self._extract_metadata(text, pdf_path)
            
            # Check if already exists
            file_hash = self._compute_file_hash(pdf_path)
            existing = self._check_existing(metadata.get('case_number'), file_hash)
            if existing:
                logger.info(f"Judgment already exists: {existing}")
                return existing
            
            # Store judgment metadata
            judgment_id = self._store_judgment(metadata, file_path=pdf_path, file_hash=file_hash)
            
            # Chunk text
            chunks = self.chunker.chunk(text)
            logger.info(f"Created {len(chunks)} chunks from judgment {judgment_id}")
            
            # Process chunks
            chunk_ids = self._store_chunks(judgment_id, chunks, text)
            
            # Extract and store entities
            self._store_entities(judgment_id, text, chunk_ids)
            
            # Update chunk count
            self.db.execute_update(
                "UPDATE judgments SET total_chunks = %s WHERE id = %s",
                (len(chunk_ids), judgment_id)
            )
            
            logger.info(f"Successfully ingested judgment {judgment_id}: {metadata.get('case_number')}")
            return judgment_id
            
        except Exception as e:
            logger.error(f"Error ingesting {pdf_path}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF"""
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                return text
        except ImportError:
            try:
                import pypdf
                with open(pdf_path, 'rb') as f:
                    pdf = pypdf.PdfReader(f)
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() or ""
                    return text
            except ImportError:
                raise ImportError("No PDF library available. Install pdfplumber or pypdf")
    
    def _extract_metadata(self, text: str, file_path: str) -> Dict:
        """Extract metadata from judgment text"""
        metadata = {
            'case_number': '',
            'title': '',
            'parties': '',
            'judgment_date': None,
            'court': 'Supreme Court of India',
            'judges': [],
            'year': None
        }
        
        # Extract case number
        case_patterns = [
            r'(Crl\.?A\.?\s*No\.?\s*\d+/\d+)',
            r'(Criminal\s+Appeal\s+No\.?\s*\d+/\d+)',
            r'(W\.?P\.?\s*\(?C\)?\s*No\.?\s*\d+/\d+)',
            r'(SLP\s*\(?C\)?\s*No\.?\s*\d+/\d+)',
        ]
        
        for pattern in case_patterns:
            match = re.search(pattern, text[:2000], re.IGNORECASE)
            if match:
                metadata['case_number'] = match.group(1)
                break
        
        # Extract parties
        party_match = re.search(
            r'([A-Z][^.]{10,100}?)\s+v[eo]rs?\.?\s+([A-Z][^.]{10,100}?)',
            text[:2000],
            re.IGNORECASE
        )
        if party_match:
            metadata['parties'] = f"{party_match.group(1).strip()} vs {party_match.group(2).strip()}"
        
        # Extract date
        date_match = re.search(r'(\d{1,2}[./-]\d{1,2}[./-]\d{4})', text[:2000])
        if date_match:
            date_str = date_match.group(1)
            # Try to parse date
            try:
                from datetime import datetime
                for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y']:
                    try:
                        metadata['judgment_date'] = datetime.strptime(date_str, fmt).date()
                        break
                    except ValueError:
                        continue
                if metadata['judgment_date']:
                    metadata['year'] = metadata['judgment_date'].year
            except:
                pass
        
        # Extract judges
        judge_patterns = [
            r"HON'?BLE\s+MR\.?\s+JUSTICE\s+([A-Z][A-Z\s.]+)",
            r"JUSTICE\s+([A-Z][A-Z\s.]+)",
        ]
        judges = set()
        for pattern in judge_patterns:
            matches = re.findall(pattern, text[:3000])
            for match in matches:
                judge_name = match.strip()
                if 3 < len(judge_name) < 50:
                    judges.add(judge_name)
        metadata['judges'] = list(judges)[:5]
        
        # Extract title from first few lines
        first_lines = text[:500].split('\n')[:3]
        if first_lines:
            metadata['title'] = ' '.join(first_lines).strip()[:200]
        
        return metadata
    
    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _check_existing(self, case_number: str, file_hash: str) -> Optional[int]:
        """Check if judgment already exists"""
        if case_number:
            result = self.db.execute_one(
                "SELECT id FROM judgments WHERE case_number = %s",
                (case_number,)
            )
            if result:
                return result['id']
        
        result = self.db.execute_one(
            "SELECT id FROM judgments WHERE file_hash = %s",
            (file_hash,)
        )
        if result:
            return result['id']
        
        return None
    
    def _store_judgment(self, metadata: Dict, file_path: str, file_hash: str) -> int:
        """Store judgment metadata"""
        # Ensure case_number is not empty (use file hash if no case number)
        case_number = metadata.get('case_number', '').strip()
        if not case_number:
            # Use filename as fallback
            case_number = Path(file_path).stem[:200]  # Limit length
        
        sql = """
            INSERT INTO judgments 
            (case_number, title, parties, judgment_date, court, judges, year, file_path, file_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        result = self.db.execute_one(
            sql,
            (
                case_number,
                metadata.get('title'),
                metadata.get('parties'),
                metadata.get('judgment_date'),
                metadata.get('court'),
                metadata.get('judges', []),
                metadata.get('year'),
                file_path,
                file_hash
            )
        )
        
        return result['id']
    
    def _store_chunks(self, judgment_id: int, chunks: List[Dict], full_text: str) -> List[int]:
        """Store chunks with embeddings"""
        chunk_ids = []
        
        for idx, chunk in enumerate(chunks):
            content = chunk['text']
            page_num = chunk.get('page_number', None)
            section_type = chunk.get('section_type', None)
            
            # Generate embedding
            embedding = self.embedder.encode(content, show_progress_bar=False)
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            
            # Count tokens (approximate)
            token_count = len(content.split())
            
            # Store chunk
            # Check if vector type exists, otherwise use text
            sql = """
                INSERT INTO judgment_chunks
                (judgment_id, chunk_index, content, page_number, section_type, 
                 token_count, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                RETURNING id
            """
            
            metadata_json = json.dumps({
                'chunk_index': idx,
                'section_type': section_type
            })
            
            result = self.db.execute_one(
                sql,
                (judgment_id, idx, content, page_num, section_type, 
                 token_count, embedding_str, metadata_json)
            )
            
            if result:
                chunk_ids.append(result['id'])
        
        return chunk_ids
    
    def _store_entities(self, judgment_id: int, text: str, chunk_ids: List[int]):
        """Extract and store named entities"""
        entities = self.ner.extract_entities(text)
        
        for entity in entities:
            # Find which chunk this entity belongs to
            chunk_id = self._find_chunk_for_entity(entity.start, chunk_ids, judgment_id)
            
            sql = """
                INSERT INTO named_entities
                (judgment_id, chunk_id, entity_type, entity_text, 
                 start_position, end_position, confidence, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            """
            
            metadata_json = json.dumps(entity.metadata or {})
            
            try:
                self.db.execute_update(
                    sql,
                    (
                        judgment_id,
                        chunk_id,
                        entity.entity_type.name,
                        entity.text,
                        entity.start,
                        entity.end,
                        entity.confidence,
                        metadata_json
                    )
                )
            except Exception as e:
                logger.warning(f"Error storing entity {entity.text}: {e}")
    
    def _find_chunk_for_entity(self, position: int, chunk_ids: List[int], judgment_id: int) -> Optional[int]:
        """Find which chunk an entity belongs to"""
        # This is simplified - in practice, need to track chunk positions
        # For now, just return first chunk or None
        return chunk_ids[0] if chunk_ids else None
    
    def ingest_batch(self, pdf_paths: List[str], max_workers: int = 4) -> Dict:
        """Ingest multiple PDFs"""
        results = {
            'successful': [],
            'failed': [],
            'skipped': []
        }
        
        for pdf_path in pdf_paths:
            try:
                judgment_id = self.ingest_pdf(pdf_path)
                if judgment_id:
                    results['successful'].append((pdf_path, judgment_id))
                else:
                    results['skipped'].append(pdf_path)
            except Exception as e:
                logger.error(f"Failed to ingest {pdf_path}: {e}")
                results['failed'].append(pdf_path)
        
        logger.info(f"Ingestion complete: {len(results['successful'])} successful, "
                   f"{len(results['skipped'])} skipped, {len(results['failed'])} failed")
        
        return results


# Helper imports
import json
