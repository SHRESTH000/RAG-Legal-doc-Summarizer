"""
Query Enhancement Module
Following base paper: enhances queries with legal entities and dark zones
"""

from typing import List, Dict, Optional
from ner.legal_ner import LegalNER, Entity, EntityType
from retrieval.dark_zone_detector import DarkZoneDetector, DarkZone
import re
import logging

logger = logging.getLogger(__name__)


class QueryEnhancer:
    """
    Enhances queries for retrieval following base paper methodology
    
    Steps:
    1. Extract entities from query/judgment
    2. Identify dark zones
    3. Build enhanced query with entities and context
    4. Add legal terminology
    5. Include section references
    """
    
    def __init__(self):
        self.ner = LegalNER()
        self.dark_zone_detector = DarkZoneDetector()
    
    def enhance_query(self, 
                     query_or_text: str,
                     include_entities: bool = True,
                     include_dark_zones: bool = True,
                     include_legal_terms: bool = True) -> Dict[str, str]:
        """
        Enhance query following base paper approach
        
        Args:
            query_or_text: Original query or judgment text
            include_entities: Include extracted entities
            include_dark_zones: Include dark zone queries
            include_legal_terms: Include legal terminology
            
        Returns:
            Dictionary with enhanced query and metadata
        """
        # Extract entities
        entities = self.ner.extract_entities(query_or_text) if include_entities else []
        
        # Detect dark zones
        dark_zones = []
        if include_dark_zones:
            dark_zones = self.dark_zone_detector.detect_dark_zones(query_or_text)
        
        # Build enhanced query
        query_parts = []
        
        # 1. Original query (key sentences if long text)
        if len(query_or_text) > 500:
            key_sentences = self._extract_key_sentences(query_or_text)
            query_parts.extend(key_sentences)
        else:
            query_parts.append(query_or_text)
        
        # 2. High-confidence entities
        if entities:
            high_conf_entities = [
                e.text for e in entities 
                if e.confidence >= 0.8 and e.entity_type in [
                    EntityType.LEGAL_SECTION,
                    EntityType.CASE_NUMBER,
                    EntityType.STATUTE
                ]
            ]
            query_parts.extend(high_conf_entities)
        
        # 3. Dark zone queries
        if dark_zones:
            for dz in dark_zones:
                query_parts.append(dz.section_entity.text)
                # Add brief context
                if dz.context_window:
                    context_snippet = dz.context_window[:150].strip()
                    query_parts.append(context_snippet)
        
        # 4. Legal terminology
        if include_legal_terms:
            legal_terms = self._extract_legal_terms(query_or_text)
            query_parts.extend(legal_terms)
        
        # Combine into enhanced query
        enhanced_query = " ".join(query_parts)
        
        # Remove duplicates while preserving order
        enhanced_query = self._deduplicate_query(enhanced_query)
        
        return {
            'original_query': query_or_text,
            'enhanced_query': enhanced_query,
            'entities': entities,
            'dark_zones': dark_zones,
            'entity_count': len(entities),
            'dark_zone_count': len(dark_zones)
        }
    
    def _extract_key_sentences(self, text: str, num_sentences: int = 5) -> List[str]:
        """Extract key sentences from text"""
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        # Filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Score sentences (simple heuristic)
        scored_sentences = []
        for sentence in sentences:
            score = 0
            
            # Legal keywords boost score
            legal_keywords = [
                'section', 'act', 'code', 'judgment', 'court',
                'conviction', 'acquittal', 'appeal', 'statute'
            ]
            for keyword in legal_keywords:
                if keyword.lower() in sentence.lower():
                    score += 1
            
            # Length factor (prefer medium-length sentences)
            length = len(sentence.split())
            if 10 <= length <= 30:
                score += 1
            
            # Entity mentions boost
            entities_in_sentence = self.ner.extract_entities(sentence)
            score += len(entities_in_sentence) * 0.5
            
            scored_sentences.append((sentence, score))
        
        # Sort by score and return top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        return [s[0] for s in scored_sentences[:num_sentences]]
    
    def _extract_legal_terms(self, text: str, max_terms: int = 10) -> List[str]:
        """Extract important legal terms"""
        # Legal term patterns
        legal_term_patterns = [
            r'\b(?:Acquittal|Conviction|Bail|Appeal|Revision|Petition|Writ)\b',
            r'\b(?:Habeas\s+Corpus|Mandamus|Certiorari|Prohibition)\b',
            r'\b(?:Prosecution|Defense|Accused|Complainant|Respondent)\b',
            r'\b(?:Evidence|Witness|Testimony|Examination)\b',
            r'\b(?:Punishment|Sentence|Fine|Imprisonment)\b',
        ]
        
        terms = set()
        for pattern in legal_term_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            terms.update([m.lower() for m in matches])
        
        return list(terms)[:max_terms]
    
    def _deduplicate_query(self, query: str) -> str:
        """Remove duplicate words/phrases while preserving order"""
        words = query.split()
        seen = set()
        unique_words = []
        
        for word in words:
            word_lower = word.lower()
            if word_lower not in seen:
                seen.add(word_lower)
                unique_words.append(word)
        
        return " ".join(unique_words)
    
    def build_entity_query(self, entities: List[Entity]) -> str:
        """Build query from entities only"""
        query_parts = []
        
        for entity in entities:
            if entity.entity_type == EntityType.LEGAL_SECTION:
                query_parts.append(entity.text)
            elif entity.entity_type == EntityType.STATUTE:
                query_parts.append(entity.text)
            elif entity.entity_type == EntityType.CASE_NUMBER:
                query_parts.append(entity.text)
        
        return " ".join(query_parts)
    
    def expand_with_synonyms(self, query: str) -> str:
        """Expand query with legal term synonyms"""
        # Legal term synonyms mapping
        synonyms = {
            'murder': ['homicide', 'killing'],
            'theft': ['larceny', 'robbery'],
            'fraud': ['deceit', 'cheating'],
            'assault': ['battery', 'attack'],
            'bail': ['bail bond', 'release'],
            'conviction': ['guilty verdict', 'sentence'],
            'acquittal': ['not guilty', 'discharge'],
        }
        
        words = query.split()
        expanded = []
        
        for word in words:
            word_lower = word.lower()
            expanded.append(word)
            
            # Add synonyms if found
            for key, values in synonyms.items():
                if key == word_lower:
                    expanded.extend(values[:2])  # Add 2 synonyms max
        
        return " ".join(expanded)


# Convenience function
def enhance_query_for_retrieval(query: str, 
                               judgment_text: Optional[str] = None) -> Dict:
    """
    High-level function to enhance query for retrieval
    
    Args:
        query: Original query
        judgment_text: Optional judgment text for context
        
    Returns:
        Enhanced query dictionary
    """
    enhancer = QueryEnhancer()
    
    # If judgment text provided, use it for context
    if judgment_text:
        # Combine query and judgment for better entity extraction
        combined = f"{query} {judgment_text[:1000]}"
        return enhancer.enhance_query(combined)
    else:
        return enhancer.enhance_query(query)
