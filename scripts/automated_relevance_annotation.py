"""
Automated Relevance Annotation System
Alternative to expert annotation using multiple heuristics
"""

import sys
from pathlib import Path
import json
from typing import List, Dict, Set
import re

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))


class AutomatedRelevanceAnnotator:
    """
    Automated relevance annotation using multiple heuristics:
    1. Keyword matching (BM25-style)
    2. Semantic term matching (expanded vocabulary)
    3. Section reference matching
    4. Legal concept matching
    """
    
    def __init__(self):
        self.legal_concept_map = {
            "murder": ["intentional killing", "premeditated killing", "deliberate killing", 
                      "homicide", "killing with intent", "culpable homicide not amounting to murder"],
            "culpable homicide": ["negligent killing", "unintentional killing", "death by negligence",
                                "rash act causing death", "reckless killing"],
            "bail": ["release from custody", "interim release", "temporary liberty", 
                    "pre-trial release", "custody release"],
            "confession": ["admission of guilt", "self-incriminating statement", 
                         "voluntary admission", "acknowledgment of crime"],
            "dying declaration": ["statement before death", "deathbed statement", 
                                "final statement", "statement of dying person"],
            "common intention": ["joint liability", "collective action", "acting together",
                               "shared intent", "group crime", "multiple perpetrators"],
            "evidence": ["proof", "testimony", "witness statement", "material proof", 
                        "evidentiary material"],
            "punishment": ["sentence", "penalty", "imprisonment", "fine", "sentencing"],
            "intention": ["mens rea", "mental state", "guilty mind", "criminal intent",
                         "willful act", "deliberate act"]
        }
    
    def expand_query_terms(self, query: str, expected_terms: List[str], 
                          expected_semantic_terms: List[str]) -> Set[str]:
        """Expand query with synonyms and related terms"""
        expanded = set()
        
        # Add original terms
        expanded.update([term.lower() for term in expected_terms])
        expanded.update([term.lower() for term in expected_semantic_terms])
        
        # Extract words from query
        query_words = re.findall(r'\b\w+\b', query.lower())
        expanded.update(query_words)
        
        # Add legal concept synonyms
        for term in expected_terms + query_words:
            term_lower = term.lower()
            if term_lower in self.legal_concept_map:
                expanded.update(self.legal_concept_map[term_lower])
        
        return expanded
    
    def calculate_relevance_score(self, 
                                  document: str,
                                  expected_sections: List[str],
                                  expected_terms: List[str],
                                  expected_semantic_terms: List[str],
                                  query: str) -> float:
        """
        Calculate relevance score for a document
        Returns score 0.0 to 1.0
        """
        doc_lower = document.lower()
        score = 0.0
        max_score = 0.0
        
        # Section matching (high weight)
        section_weight = 0.4
        max_score += section_weight
        section_match = any(section.lower() in doc_lower for section in expected_sections)
        if section_match:
            score += section_weight
        
        # Exact term matching (medium weight)
        term_weight = 0.3
        max_score += term_weight
        term_matches = sum(1 for term in expected_terms if term.lower() in doc_lower)
        if term_matches > 0:
            score += term_weight * (term_matches / len(expected_terms))
        
        # Semantic term matching (medium weight)
        semantic_weight = 0.2
        max_score += semantic_weight
        expanded_terms = self.expand_query_terms(query, expected_terms, expected_semantic_terms)
        semantic_matches = sum(1 for term in expanded_terms if term in doc_lower)
        if semantic_matches > 0:
            # Normalize by number of unique terms found
            score += semantic_weight * min(1.0, semantic_matches / 5.0)
        
        # Query word matching (low weight)
        query_weight = 0.1
        max_score += query_weight
        query_words = re.findall(r'\b\w+\b', query.lower())
        query_matches = sum(1 for word in query_words if len(word) > 3 and word in doc_lower)
        if query_matches > 0:
            score += query_weight * min(1.0, query_matches / len(query_words))
        
        # Normalize score
        if max_score > 0:
            return min(1.0, score / max_score)
        return 0.0
    
    def annotate_relevant_chunks(self,
                                 chunks: List[Dict],
                                 query: str,
                                 expected_sections: List[str],
                                 expected_terms: List[str],
                                 expected_semantic_terms: List[str],
                                 threshold: float = 0.3) -> Set[int]:
        """
        Annotate which chunks are relevant
        Returns set of chunk IDs that are relevant
        """
        relevant_chunks = set()
        
        for chunk in chunks:
            chunk_id = chunk.get('id')
            content = chunk.get('content', '')
            
            if not content:
                continue
            
            # Calculate relevance score
            relevance_score = self.calculate_relevance_score(
                content,
                expected_sections,
                expected_terms,
                expected_semantic_terms,
                query
            )
            
            # Mark as relevant if score exceeds threshold
            if relevance_score >= threshold:
                relevant_chunks.add(chunk_id)
        
        return relevant_chunks
    
    def get_relevance_with_scores(self,
                                  chunks: List[Dict],
                                  query: str,
                                  expected_sections: List[str],
                                  expected_terms: List[str],
                                  expected_semantic_terms: List[str]) -> Dict[int, float]:
        """
        Get relevance scores for all chunks
        Returns dict: {chunk_id: relevance_score}
        """
        relevance_scores = {}
        
        for chunk in chunks:
            chunk_id = chunk.get('id')
            content = chunk.get('content', '')
            
            if not content:
                relevance_scores[chunk_id] = 0.0
                continue
            
            score = self.calculate_relevance_score(
                content,
                expected_sections,
                expected_terms,
                expected_semantic_terms,
                query
            )
            relevance_scores[chunk_id] = score
        
        return relevance_scores


def load_test_queries(query_file: str = "test_queries/semantic_queries.json") -> List[Dict]:
    """Load test queries from JSON file"""
    query_path = Path(project_root) / query_file
    
    if not query_path.exists():
        raise FileNotFoundError(f"Query file not found: {query_path}")
    
    with open(query_path, 'r') as f:
        data = json.load(f)
        return data.get('queries', [])


if __name__ == "__main__":
    # Test the annotator
    annotator = AutomatedRelevanceAnnotator()
    
    test_doc = "The accused was charged under IPC Section 302 for the murder of the victim. The prosecution established that the killing was intentional and premeditated."
    
    score = annotator.calculate_relevance_score(
        test_doc,
        ["Section 302"],
        ["murder"],
        ["intentional killing", "premeditated"],
        "What is IPC Section 302 about murder?"
    )
    
    print(f"Relevance score: {score:.3f}")
