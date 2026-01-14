"""
Text Chunking for Legal Documents
Intelligent chunking that preserves legal structure
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass
import tiktoken

logger = None  # Will be initialized if logging available


@dataclass
class Chunk:
    """Represents a text chunk"""
    text: str
    start_pos: int
    end_pos: int
    section_type: Optional[str] = None
    page_number: Optional[int] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class LegalChunker:
    """
    Intelligent chunking for legal documents
    
    Features:
    - Preserves sentence boundaries
    - Detects legal document sections
    - Overlapping chunks
    - Token-aware splitting
    """
    
    def __init__(self,
                 chunk_size: int = 512,
                 chunk_overlap: int = 50,
                 min_chunk_size: int = 100,
                 encoding_name: str = "cl100k_base"):
        """
        Initialize chunker
        
        Args:
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens
            min_chunk_size: Minimum chunk size in tokens
            encoding_name: Tokenizer encoding
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        try:
            self.tokenizer = tiktoken.get_encoding(encoding_name)
        except:
            self.tokenizer = None
            # Fallback: approximate tokens as words * 1.3
        
        # Legal section markers
        self.section_patterns = {
            'facts': r'(?:FACTS|FACTUAL\s+BACKGROUND|BACKGROUND|CASE\s+FACTS)',
            'analysis': r'(?:ANALYSIS|DISCUSSION|REASONING|HELD|OBSERVATION)',
            'conclusion': r'(?:CONCLUSION|DECISION|ORDER|JUDGMENT)',
            'headnote': r'(?:HEADNOTE|SYNOPSIS|SUMMARY)',
            'issue': r'(?:ISSUE|ISSUES|QUESTION)',
        }
    
    def chunk(self, text: str) -> List[Dict]:
        """
        Chunk text into smaller pieces
        
        Returns:
            List of chunk dictionaries
        """
        # First, detect document sections
        sections = self._detect_sections(text)
        
        chunks = []
        
        if sections:
            # Chunk each section separately
            for section in sections:
                section_chunks = self._chunk_text(
                    section['text'],
                    section_type=section['type'],
                    start_offset=section['start']
                )
                chunks.extend(section_chunks)
        else:
            # No sections detected, chunk entire text
            chunks = self._chunk_text(text)
        
        return [
            {
                'text': chunk.text,
                'start': chunk.start_pos,
                'end': chunk.end_pos,
                'section_type': chunk.section_type,
                'page_number': chunk.page_number,
                'metadata': chunk.metadata
            }
            for chunk in chunks
        ]
    
    def _detect_sections(self, text: str) -> List[Dict]:
        """Detect document sections"""
        sections = []
        text_upper = text.upper()
        
        for section_type, pattern in self.section_patterns.items():
            matches = list(re.finditer(pattern, text_upper, re.IGNORECASE | re.MULTILINE))
            for match in matches:
                sections.append({
                    'type': section_type,
                    'start': match.start(),
                    'end': match.end(),
                    'text': text[match.end():],  # Text after marker
                })
        
        # Sort by position
        sections.sort(key=lambda x: x['start'])
        
        # Clean up overlapping sections
        cleaned = []
        for i, section in enumerate(sections):
            if i == 0:
                cleaned.append(section)
            else:
                prev = cleaned[-1]
                if section['start'] > prev['start'] + 500:  # At least 500 chars apart
                    cleaned.append(section)
        
        return cleaned
    
    def _chunk_text(self,
                   text: str,
                   section_type: Optional[str] = None,
                   start_offset: int = 0) -> List[Chunk]:
        """Chunk text with overlap"""
        chunks = []
        
        # Split into sentences
        sentences = self._split_sentences(text)
        
        current_chunk = []
        current_tokens = 0
        current_start = start_offset
        
        for sentence in sentences:
            sentence_tokens = self._count_tokens(sentence)
            
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunk = Chunk(
                    text=chunk_text,
                    start_pos=current_start,
                    end_pos=current_start + len(chunk_text),
                    section_type=section_type
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                overlap_tokens = self._count_tokens(overlap_text)
                
                current_chunk = [overlap_text] if overlap_text else []
                current_tokens = overlap_tokens
                current_start = chunk.end_pos - len(overlap_text) if overlap_text else chunk.end_pos
            
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            if self._count_tokens(chunk_text) >= self.min_chunk_size:
                chunk = Chunk(
                    text=chunk_text,
                    start_pos=current_start,
                    end_pos=current_start + len(chunk_text),
                    section_type=section_type
                )
                chunks.append(chunk)
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting (can be improved)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Approximate: words * 1.3
            return int(len(text.split()) * 1.3)
    
    def _get_overlap_text(self, chunk_sentences: List[str]) -> str:
        """Get overlap text from end of chunk"""
        if len(chunk_sentences) < 2:
            return ""
        
        # Take last few sentences that fit in overlap size
        overlap_sentences = []
        overlap_tokens = 0
        
        for sentence in reversed(chunk_sentences):
            sent_tokens = self._count_tokens(sentence)
            if overlap_tokens + sent_tokens <= self.chunk_overlap:
                overlap_sentences.insert(0, sentence)
                overlap_tokens += sent_tokens
            else:
                break
        
        return ' '.join(overlap_sentences)
