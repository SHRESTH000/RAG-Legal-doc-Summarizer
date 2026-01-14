"""
Dynamic Legal RAG System
Main pipeline following base paper methodology with hybrid retrieval enhancement
"""

import sys
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Fix import conflict
project_root = Path(__file__).parent.parent
if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from ner.legal_ner import get_ner, Entity
from retrieval.dark_zone_detector import DarkZoneDetector, DarkZone
from retrieval.query_enhancer import QueryEnhancer
from retrieval.hybrid_retriever import HybridRetriever
from database.connection import get_db_manager

logger = logging.getLogger(__name__)


@dataclass
class RAGResult:
    """Result from Dynamic Legal RAG system"""
    query: str
    enhanced_query: str
    entities: List[Entity]
    dark_zones: List[DarkZone]
    retrieved_chunks: List[Dict]
    context: str
    metadata: Dict


class DynamicLegalRAG:
    """
    Dynamic Legal RAG System
    Following base paper: "Optimizing Legal Text Summarization Through 
    Dynamic Retrieval-Augmented Generation and Domain-Specific Adaptation"
    
    Enhanced with:
    - Hybrid retrieval (BM25 + Vector) instead of BM25 only
    - Expanded knowledge base (IPC, CrPC, Evidence Act)
    """
    
    def __init__(self,
                 top_k: int = 3,  # Base paper uses top-3
                 bm25_weight: float = 0.4,
                 vector_weight: float = 0.6,
                 similarity_threshold: float = 0.7):
        """
        Initialize Dynamic Legal RAG
        
        Args:
            top_k: Number of chunks to retrieve (base paper: 3)
            bm25_weight: Weight for BM25 scores
            vector_weight: Weight for vector scores
            similarity_threshold: Minimum similarity for vector search
        """
        self.top_k = top_k
        self.ner = get_ner()
        self.dark_zone_detector = DarkZoneDetector()
        self.query_enhancer = QueryEnhancer()
        self.hybrid_retriever = HybridRetriever(
            bm25_weight=bm25_weight,
            vector_weight=vector_weight,
            similarity_threshold=similarity_threshold
        )
        self.db = get_db_manager()
        
        logger.info(f"Dynamic Legal RAG initialized: top_k={top_k}, "
                   f"bm25={bm25_weight}, vector={vector_weight}")
    
    def process(self, 
                query_or_text: str,
                judgment_id: Optional[int] = None,
                retrieve_legal_sections: bool = True) -> RAGResult:
        """
        Process query/text through Dynamic RAG pipeline
        
        Args:
            query_or_text: Query string or judgment text
            judgment_id: Optional judgment ID for filtering
            retrieve_legal_sections: Whether to retrieve legal sections
            
        Returns:
            RAGResult with all retrieved context and metadata
        """
        logger.info(f"Processing query/text (length: {len(query_or_text)})")
        
        # Step 1: Extract entities (NER)
        logger.debug("Step 1: Extracting entities...")
        entities = self.ner.extract_entities(query_or_text)
        logger.info(f"Extracted {len(entities)} entities")
        
        # Step 2: Detect dark zones
        logger.debug("Step 2: Detecting dark zones...")
        dark_zones = self.dark_zone_detector.detect_dark_zones(query_or_text)
        logger.info(f"Detected {len(dark_zones)} dark zones")
        
        # Step 3: Enhance query
        logger.debug("Step 3: Enhancing query...")
        enhanced_result = self.query_enhancer.enhance_query(
            query_or_text,
            include_entities=True,
            include_dark_zones=True,
            include_legal_terms=True
        )
        enhanced_query = enhanced_result['enhanced_query']
        
        # Step 4: Hybrid retrieval
        logger.debug("Step 4: Hybrid retrieval...")
        retrieved_results = self.hybrid_retriever.retrieve(
            enhanced_query,
            top_k=self.top_k * 2,  # Retrieve more, then select top-K
            judgment_id=judgment_id
        )
        
        # Step 5: Select top-K chunks (base paper approach)
        top_chunks = retrieved_results[:self.top_k]
        logger.info(f"Selected top-{self.top_k} chunks from {len(retrieved_results)} results")
        
        # Step 6: Get chunk contents from database
        chunk_contents = self._get_chunk_contents([c[0] for c in top_chunks])
        
        # Step 7: Retrieve legal sections if needed
        legal_sections_context = ""
        if retrieve_legal_sections and entities:
            legal_sections_context = self._retrieve_legal_sections(entities, dark_zones)
        
        # Step 8: Resolve dark zones
        dark_zone_resolutions = self._resolve_dark_zones(dark_zones)
        
        # Step 9: Assemble context
        context = self._assemble_context(
            chunk_contents,
            legal_sections_context,
            dark_zone_resolutions,
            query_or_text
        )
        
        return RAGResult(
            query=query_or_text,
            enhanced_query=enhanced_query,
            entities=entities,
            dark_zones=dark_zones,
            retrieved_chunks=chunk_contents,
            context=context,
            metadata={
                'top_k': self.top_k,
                'chunks_retrieved': len(chunk_contents),
                'dark_zones_found': len(dark_zones),
                'entities_found': len(entities),
                'legal_sections_retrieved': len(legal_sections_context) > 0
            }
        )
    
    def _get_chunk_contents(self, chunk_ids: List[int]) -> List[Dict]:
        """Get chunk contents from database"""
        if not chunk_ids:
            return []
        
        chunk_ids_str = ','.join(map(str, chunk_ids))
        sql = f"""
            SELECT 
                jc.id,
                jc.judgment_id,
                jc.content,
                jc.section_type,
                jc.page_number,
                j.case_number,
                j.title,
                j.judgment_date,
                j.court
            FROM judgment_chunks jc
            JOIN judgments j ON jc.judgment_id = j.id
            WHERE jc.id IN ({chunk_ids_str})
            ORDER BY jc.id
        """
        
        try:
            results = self.db.execute_query(sql)
            return [
                {
                    'chunk_id': row['id'],
                    'judgment_id': row['judgment_id'],
                    'content': row['content'],
                    'section_type': row['section_type'],
                    'page_number': row['page_number'],
                    'case_number': row['case_number'],
                    'title': row['title'],
                    'date': str(row['judgment_date']) if row['judgment_date'] else None,
                    'court': row['court']
                }
                for row in results
            ]
        except Exception as e:
            logger.error(f"Error fetching chunk contents: {e}")
            return []
    
    def _retrieve_legal_sections(self, 
                                entities: List[Entity],
                                dark_zones: List[DarkZone]) -> str:
        """Retrieve relevant legal sections"""
        sections = []
        
        # Get sections from entities
        section_refs = [
            e for e in entities 
            if e.entity_type.name == 'LEGAL_SECTION' and e.metadata
        ]
        
        # Get sections from dark zones
        dark_zone_sections = [dz.section_entity for dz in dark_zones]
        
        all_sections = section_refs + dark_zone_sections
        
        for entity in all_sections:
            if not entity.metadata:
                continue
            
            act = entity.metadata.get('act')
            section_num = entity.metadata.get('section_number')
            
            if act and section_num:
                sql = """
                    SELECT title, content, section_number, act_name
                    FROM legal_sections
                    WHERE act_name = %s AND section_number = %s
                    LIMIT 1
                """
                try:
                    result = self.db.execute_one(sql, (act, str(section_num)))
                    if result and result.get('content'):
                        sections.append({
                            'act': act,
                            'section': section_num,
                            'title': result.get('title', ''),
                            'content': result.get('content', '')
                        })
                except Exception as e:
                    logger.warning(f"Error retrieving section {act} {section_num}: {e}")
        
        # Format sections
        if not sections:
            return ""
        
        formatted = ["\n[LEGAL SECTIONS]"]
        for sec in sections[:5]:  # Limit to 5 sections
            formatted.append(
                f"\n{sec['act']} Section {sec['section']}: {sec['title']}\n{sec['content'][:500]}"
            )
        
        return "\n".join(formatted)
    
    def _resolve_dark_zones(self, dark_zones: List[DarkZone]) -> str:
        """Resolve dark zones by retrieving context"""
        if not dark_zones:
            return ""
        
        resolutions = []
        for dz in dark_zones[:3]:  # Resolve top 3 dark zones
            query = f"{dz.section_entity.text} {dz.context_window[:200]}"
            
            # Retrieve relevant sections
            section_refs = self._retrieve_legal_sections([dz.section_entity], [])
            if section_refs:
                resolutions.append(
                    f"Dark Zone: {dz.section_entity.text}\nResolution: {section_refs[:300]}"
                )
        
        if resolutions:
            return "\n\n[DARK ZONE RESOLUTIONS]\n" + "\n\n".join(resolutions)
        return ""
    
    def _assemble_context(self,
                         chunk_contents: List[Dict],
                         legal_sections: str,
                         dark_zone_resolutions: str,
                         original_query: str) -> str:
        """Assemble final context for summarization"""
        context_parts = []
        
        # Add retrieved judgment chunks
        if chunk_contents:
            context_parts.append("[RETRIEVED JUDGMENT EXCERPTS]")
            for i, chunk in enumerate(chunk_contents, 1):
                case_info = f"\nCase: {chunk.get('case_number', 'N/A')}"
                if chunk.get('date'):
                    case_info += f" | Date: {chunk['date']}"
                if chunk.get('court'):
                    case_info += f" | Court: {chunk['court']}"
                
                context_parts.append(
                    f"\n--- Excerpt {i} ---{case_info}\n{chunk['content']}"
                )
        
        # Add legal sections
        if legal_sections:
            context_parts.append(legal_sections)
        
        # Add dark zone resolutions
        if dark_zone_resolutions:
            context_parts.append(dark_zone_resolutions)
        
        # Add original query/context
        context_parts.append(f"\n[ORIGINAL QUERY/CONTEXT]\n{original_query[:1000]}")
        
        return "\n".join(context_parts)
    
    def initialize_bm25_index(self, documents: List[str], chunk_ids: List[int]):
        """Initialize BM25 index with documents"""
        self.hybrid_retriever.initialize_bm25(documents, chunk_ids)
        logger.info(f"BM25 index initialized with {len(documents)} documents")


def create_rag_system(top_k: int = 3,
                     bm25_weight: float = 0.4,
                     vector_weight: float = 0.6) -> DynamicLegalRAG:
    """Factory function to create RAG system"""
    return DynamicLegalRAG(
        top_k=top_k,
        bm25_weight=bm25_weight,
        vector_weight=vector_weight
    )
