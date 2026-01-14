"""
Named Entity Recognition module for Legal Text
Extracts legal entities from judgments and queries
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Legal entity types"""
    PERSON = "PERSON"
    CASE_NUMBER = "CASE_NUMBER"
    LEGAL_SECTION = "LEGAL_SECTION"
    COURT = "COURT"
    DATE = "DATE"
    PENALTY = "PENALTY"
    LEGAL_TERM = "LEGAL_TERM"
    STATUTE = "STATUTE"
    ORGANIZATION = "ORGANIZATION"
    JUDGE = "JUDGE"
    LAWYER = "LAWYER"


@dataclass
class Entity:
    """Represents a named entity"""
    text: str
    entity_type: EntityType
    start: int
    end: int
    confidence: float = 1.0
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class LegalNER:
    """Named Entity Recognition for Indian Legal Text"""
    
    def __init__(self):
        """Initialize NER with pattern-based and model-based extractors"""
        self.section_patterns = self._init_section_patterns()
        self.case_number_patterns = self._init_case_patterns()
        self.court_patterns = self._init_court_patterns()
        self.statute_patterns = self._init_statute_patterns()
        self.legal_term_patterns = self._init_legal_term_patterns()
        
    def _init_section_patterns(self) -> List[Tuple[str, str]]:
        """Initialize patterns for legal section extraction"""
        return [
            # IPC Sections
            (r'Section\s+(\d+[A-Z]?)\s+of\s+the\s+Indian\s+Penal\s+Code', 'IPC'),
            (r'Section\s+(\d+[A-Z]?)\s+IPC', 'IPC'),
            (r'IPC\s+Section\s+(\d+[A-Z]?)', 'IPC'),
            (r'u/s\.?\s*(\d+[A-Z]?)\s+IPC', 'IPC'),
            (r'under\s+Section\s+(\d+[A-Z]?)\s+IPC', 'IPC'),
            
            # CrPC Sections
            (r'Section\s+(\d+[A-Z]?)\s+of\s+the\s+Code\s+of\s+Criminal\s+Procedure', 'CrPC'),
            (r'Section\s+(\d+[A-Z]?)\s+of\s+Cr\.?P\.?C\.?', 'CrPC'),
            (r'Cr\.?P\.?C\.?\s+Section\s+(\d+[A-Z]?)', 'CrPC'),
            (r'u/s\.?\s*(\d+[A-Z]?)\s+Cr\.?P\.?C\.?', 'CrPC'),
            
            # Evidence Act
            (r'Section\s+(\d+[A-Z]?)\s+of\s+the\s+Evidence\s+Act', 'Evidence_Act'),
            (r'Evidence\s+Act\s+Section\s+(\d+[A-Z]?)', 'Evidence_Act'),
            
            # Constitution
            (r'Article\s+(\d+[A-Z]?)\s+of\s+the\s+Constitution', 'Constitution'),
            (r'Constitution\s+Article\s+(\d+[A-Z]?)', 'Constitution'),
        ]
    
    def _init_case_patterns(self) -> List[str]:
        """Initialize patterns for case number extraction"""
        return [
            r'Crl\.?\s*A\.?\s*No\.?\s*(\d+\/\d+)',
            r'Criminal\s+Appeal\s+No\.?\s*(\d+\/\d+)',
            r'W\.?P\.?\s*\(?C\)?\s*No\.?\s*(\d+\/\d+)',
            r'Writ\s+Petition\s+No\.?\s*(\d+\/\d+)',
            r'SLP\s*\(?C\)?\s*No\.?\s*(\d+\/\d+)',
            r'Special\s+Leave\s+Petition\s+No\.?\s*(\d+\/\d+)',
            r'Civil\s+Appeal\s+No\.?\s*(\d+\/\d+)',
            r'Cr\.?\s*No\.?\s*(\d+\/\d+)',
        ]
    
    def _init_court_patterns(self) -> List[str]:
        """Initialize patterns for court names"""
        return [
            r'Supreme\s+Court\s+of\s+India',
            r'High\s+Court\s+of\s+([A-Z][a-z]+)',
            r'District\s+Court',
            r'Sessions\s+Court',
            r'Magistrate\s+Court',
        ]
    
    def _init_statute_patterns(self) -> List[str]:
        """Initialize patterns for statute names"""
        return [
            r'Indian\s+Penal\s+Code',
            r'Code\s+of\s+Criminal\s+Procedure',
            r'Evidence\s+Act',
            r'Constitution\s+of\s+India',
            r'Criminal\s+Procedure\s+Code',
        ]
    
    def _init_legal_term_patterns(self) -> List[str]:
        """Initialize patterns for legal terms"""
        return [
            r'\bAcquittal\b',
            r'\bConviction\b',
            r'\bBail\b',
            r'\bAppeal\b',
            r'\bRevision\b',
            r'\bPetition\b',
            r'\bWrit\b',
            r'\bHabeas\s+Corpus\b',
            r'\bMandamus\b',
        ]
    
    def extract_entities(self, text: str) -> List[Entity]:
        """Extract all entities from text"""
        entities = []
        
        # Extract legal sections
        entities.extend(self._extract_sections(text))
        
        # Extract case numbers
        entities.extend(self._extract_case_numbers(text))
        
        # Extract courts
        entities.extend(self._extract_courts(text))
        
        # Extract statutes
        entities.extend(self._extract_statutes(text))
        
        # Extract legal terms
        entities.extend(self._extract_legal_terms(text))
        
        # Extract dates (basic pattern)
        entities.extend(self._extract_dates(text))
        
        # Remove overlapping entities (keep higher confidence)
        entities = self._remove_overlaps(entities)
        
        return entities
    
    def _extract_sections(self, text: str) -> List[Entity]:
        """Extract legal section references"""
        entities = []
        
        for pattern, act_name in self.section_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                section_num = match.group(1)
                entity_text = f"{act_name} Section {section_num}"
                entities.append(Entity(
                    text=entity_text,
                    entity_type=EntityType.LEGAL_SECTION,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.9,
                    metadata={'act': act_name, 'section_number': section_num}
                ))
        
        return entities
    
    def _extract_case_numbers(self, text: str) -> List[Entity]:
        """Extract case numbers"""
        entities = []
        
        for pattern in self.case_number_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                case_num = match.group(1) if match.groups() else match.group(0)
                entities.append(Entity(
                    text=case_num,
                    entity_type=EntityType.CASE_NUMBER,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.95,
                    metadata={'full_match': match.group(0)}
                ))
        
        return entities
    
    def _extract_courts(self, text: str) -> List[Entity]:
        """Extract court names"""
        entities = []
        
        for pattern in self.court_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(Entity(
                    text=match.group(0),
                    entity_type=EntityType.COURT,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.9
                ))
        
        return entities
    
    def _extract_statutes(self, text: str) -> List[Entity]:
        """Extract statute names"""
        entities = []
        
        for pattern in self.statute_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(Entity(
                    text=match.group(0),
                    entity_type=EntityType.STATUTE,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.85
                ))
        
        return entities
    
    def _extract_legal_terms(self, text: str) -> List[Entity]:
        """Extract legal terminology"""
        entities = []
        
        for pattern in self.legal_term_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(Entity(
                    text=match.group(0),
                    entity_type=EntityType.LEGAL_TERM,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.7
                ))
        
        return entities
    
    def _extract_dates(self, text: str) -> List[Entity]:
        """Extract dates"""
        entities = []
        
        # Common date patterns
        date_patterns = [
            r'\d{1,2}[./-]\d{1,2}[./-]\d{4}',
            r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
        ]
        
        for pattern in date_patterns:
            for match in re.finditer(pattern, text):
                entities.append(Entity(
                    text=match.group(0),
                    entity_type=EntityType.DATE,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.8
                ))
        
        return entities
    
    def _remove_overlaps(self, entities: List[Entity]) -> List[Entity]:
        """Remove overlapping entities, keeping higher confidence ones"""
        if not entities:
            return []
        
        # Sort by start position, then by confidence (descending)
        sorted_entities = sorted(entities, key=lambda e: (e.start, -e.confidence))
        
        filtered = []
        for entity in sorted_entities:
            # Check if it overlaps with existing entities
            overlap = False
            for existing in filtered:
                if not (entity.end <= existing.start or entity.start >= existing.end):
                    overlap = True
                    # Keep the one with higher confidence
                    if entity.confidence > existing.confidence:
                        filtered.remove(existing)
                        filtered.append(entity)
                    break
            
            if not overlap:
                filtered.append(entity)
        
        return sorted(filtered, key=lambda e: e.start)
    
    def extract_sections_from_text(self, text: str) -> List[Dict]:
        """Extract only section references with act information"""
        sections = []
        for entity in self.extract_entities(text):
            if entity.entity_type == EntityType.LEGAL_SECTION:
                sections.append({
                    'act': entity.metadata.get('act'),
                    'section_number': entity.metadata.get('section_number'),
                    'text': entity.text
                })
        return sections


# Global NER instance
_ner_instance: Optional[LegalNER] = None


def get_ner() -> LegalNER:
    """Get or create global NER instance"""
    global _ner_instance
    if _ner_instance is None:
        _ner_instance = LegalNER()
    return _ner_instance
