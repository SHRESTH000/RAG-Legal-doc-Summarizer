"""
Dark Zone Detection Module
Following base paper methodology: identifies unexplained statute-provision pairs
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from ner.legal_ner import LegalNER, Entity, EntityType
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class DarkZone:
    """Represents a dark zone: unexplained legal reference"""
    section_entity: Entity
    context_window: str
    position: Tuple[int, int]  # (start, end) in original text
    related_entities: List[Entity]
    explanation_needed: bool
    resolution_suggestions: List[str] = None

    def __post_init__(self):
        if self.resolution_suggestions is None:
            self.resolution_suggestions = []


class DarkZoneDetector:
    """
    Detects dark zones in legal judgments
    
    Dark zones are:
    - Unexplained statute-provision pairs
    - Section references without context
    - Legal terms mentioned but not elaborated
    """
    
    def __init__(self, context_window_size: int = 500):
        """
        Initialize dark zone detector
        
        Args:
            context_window_size: Size of context window around entities (characters)
        """
        self.ner = LegalNER()
        self.context_window_size = context_window_size
        
        # Patterns indicating explanation
        self.explanation_indicators = [
            r'as\s+provided\s+in',
            r'according\s+to',
            r'under\s+the\s+provisions\s+of',
            r'as\s+per',
            r'in\s+accordance\s+with',
            r'which\s+states',
            r'which\s+provides',
            r'which\s+reads',
            r'section.*provides',
            r'section.*states',
            r'as\s+defined\s+in',
        ]
        
        # Patterns indicating lack of explanation
        self.unexplained_indicators = [
            r'section\s+\d+',  # Just section number mentioned
            r'u/s\.?\s*\d+',  # Under section abbreviation
            r'ipc\s+section\s+\d+',  # IPC section mentioned
            r'crpc\s+section\s+\d+',  # CrPC section mentioned
        ]
    
    def detect_dark_zones(self, text: str) -> List[DarkZone]:
        """
        Detect all dark zones in the text
        
        Args:
            text: Legal judgment text
            
        Returns:
            List of detected dark zones
        """
        # Extract all entities
        entities = self.ner.extract_entities(text)
        
        # Focus on legal sections (primary dark zone source)
        section_entities = [
            e for e in entities 
            if e.entity_type == EntityType.LEGAL_SECTION
        ]
        
        dark_zones = []
        
        for section_entity in section_entities:
            # Get context window around the section
            context = self._get_context_window(text, section_entity)
            
            # Check if section is explained
            is_explained = self._is_section_explained(
                context, section_entity
            )
            
            if not is_explained:
                # Find related entities in context
                related = self._find_related_entities(
                    context, entities, section_entity
                )
                
                dark_zone = DarkZone(
                    section_entity=section_entity,
                    context_window=context,
                    position=(section_entity.start, section_entity.end),
                    related_entities=related,
                    explanation_needed=True
                )
                
                # Generate resolution suggestions
                dark_zone.resolution_suggestions = self._generate_resolution_suggestions(
                    dark_zone
                )
                
                dark_zones.append(dark_zone)
        
        logger.info(f"Detected {len(dark_zones)} dark zones in text")
        return dark_zones
    
    def _get_context_window(self, text: str, entity: Entity) -> str:
        """Get context window around an entity"""
        # Expand context before and after entity
        start = max(0, entity.start - self.context_window_size)
        end = min(len(text), entity.end + self.context_window_size)
        
        return text[start:end]
    
    def _is_section_explained(self, context: str, section_entity: Entity) -> bool:
        """
        Check if a section is explained in the context
        
        Returns True if explanation indicators are found
        """
        context_lower = context.lower()
        section_text_lower = section_entity.text.lower()
        
        # Check for explanation indicators
        for pattern in self.explanation_indicators:
            if re.search(pattern, context_lower):
                # Found explanation indicator
                # Check if it's near the section mention
                matches = list(re.finditer(pattern, context_lower))
                for match in matches:
                    # Check proximity to section
                    distance = abs(match.start() - context_lower.find(section_text_lower))
                    if distance < 200:  # Within 200 chars
                        return True
        
        # Check for section content explanation
        # Look for detailed text after section mention
        section_pos = context_lower.find(section_text_lower)
        if section_pos != -1:
            after_section = context[section_pos + len(section_entity.text):]
            # If there's substantial text after, might be explained
            if len(after_section.strip()) > 100:
                # Check for legal definitions or explanations
                if any(word in after_section.lower()[:200] 
                      for word in ['means', 'refers', 'includes', 'defines']):
                    return True
        
        return False
    
    def _find_related_entities(self, 
                              context: str,
                              all_entities: List[Entity],
                              target_entity: Entity) -> List[Entity]:
        """Find entities related to the target entity in context"""
        related = []
        
        # Get position range in context
        context_start = max(0, target_entity.start - self.context_window_size)
        
        for entity in all_entities:
            if entity == target_entity:
                continue
            
            # Check if entity is in the context window
            if (context_start <= entity.start < target_entity.end + self.context_window_size):
                related.append(entity)
        
        return related
    
    def _generate_resolution_suggestions(self, dark_zone: DarkZone) -> List[str]:
        """Generate suggestions for resolving dark zone"""
        suggestions = []
        
        section = dark_zone.section_entity
        act = section.metadata.get('act', 'Unknown') if section.metadata else 'Unknown'
        section_num = section.metadata.get('section_number', '') if section.metadata else ''
        
        # Suggestion 1: Retrieve section text
        suggestions.append(
            f"Retrieve full text of {act} Section {section_num}"
        )
        
        # Suggestion 2: Get related sections
        if dark_zone.related_entities:
            related_sections = [
                e for e in dark_zone.related_entities 
                if e.entity_type == EntityType.LEGAL_SECTION
            ]
            if related_sections:
                suggestions.append(
                    f"Retrieve related sections: {', '.join([e.text for e in related_sections[:3]])}"
                )
        
        # Suggestion 3: Find precedents
        suggestions.append(
            f"Search for judgments citing {act} Section {section_num}"
        )
        
        return suggestions
    
    def get_dark_zone_query(self, dark_zones: List[DarkZone]) -> str:
        """
        Generate query to resolve dark zones
        Following base paper approach
        """
        query_parts = []
        
        for dz in dark_zones:
            # Add section reference
            query_parts.append(dz.section_entity.text)
            
            # Add context hint
            if dz.context_window:
                # Extract key phrases from context
                key_phrases = self._extract_key_phrases(dz.context_window)
                query_parts.extend(key_phrases[:3])  # Top 3 phrases
        
        return " ".join(query_parts)
    
    def _extract_key_phrases(self, text: str, max_phrases: int = 5) -> List[str]:
        """Extract key phrases from text"""
        # Simple extraction: find noun phrases or important terms
        # In production, use more sophisticated NLP
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        # Extract sentences with legal keywords
        legal_keywords = [
            'section', 'act', 'code', 'provision', 'statute',
            'judgment', 'court', 'accused', 'conviction', 'appeal'
        ]
        
        key_phrases = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in legal_keywords):
                # Take first 100 chars of sentence
                phrase = sentence.strip()[:100]
                if phrase and phrase not in key_phrases:
                    key_phrases.append(phrase)
                    if len(key_phrases) >= max_phrases:
                        break
        
        return key_phrases


def detect_and_resolve_dark_zones(text: str, 
                                  retriever=None,
                                  knowledge_base=None) -> Dict:
    """
    High-level function to detect and suggest resolution for dark zones
    
    Args:
        text: Legal judgment text
        retriever: Optional retriever to resolve dark zones
        knowledge_base: Optional knowledge base for resolution
        
    Returns:
        Dictionary with dark zones and resolutions
    """
    detector = DarkZoneDetector()
    dark_zones = detector.detect_dark_zones(text)
    
    result = {
        'dark_zones': dark_zones,
        'query': detector.get_dark_zone_query(dark_zones),
        'count': len(dark_zones)
    }
    
    # If retriever provided, try to resolve
    if retriever and dark_zones:
        resolutions = []
        for dz in dark_zones:
            query = f"{dz.section_entity.text} {dz.context_window[:200]}"
            retrieved = retriever.retrieve(query, top_k=3)
            resolutions.append({
                'dark_zone': dz,
                'retrieved_contexts': retrieved
            })
        result['resolutions'] = resolutions
    
    return result
