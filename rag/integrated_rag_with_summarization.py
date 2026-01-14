"""
Integrated RAG System with Summarization
Combines retrieval and summarization for end-to-end legal text summarization
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
import logging

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from rag.dynamic_legal_rag import DynamicLegalRAG, RAGResult
from summarization.legal_summarizer import LegalSummarizer, SummaryResult
import logging

logger = logging.getLogger(__name__)


class IntegratedRAGWithSummarization:
    """
    Complete RAG + Summarization pipeline
    Following base paper: Dynamic RAG + Legal Summarization
    """
    
    def __init__(self,
                 rag_top_k: int = 3,
                 bm25_weight: float = 0.4,
                 vector_weight: float = 0.6,
                 summarizer_model_type: str = "openai",
                 summarizer_model_name: str = "gpt-4",
                 compression_ratio: float = 0.2,
                 similarity_threshold: float = 0.5,
                 mistral_api_key: Optional[str] = None):
        """
        Initialize integrated system
        
        Args:
            rag_top_k: Number of chunks to retrieve
            bm25_weight: Weight for BM25 scores (deprecated, kept for compatibility)
            vector_weight: Weight for vector scores (deprecated, kept for compatibility)
            summarizer_model_type: LLM backend type
            summarizer_model_name: LLM model name
            compression_ratio: Target compression ratio (0.05-0.5)
            similarity_threshold: Vector similarity threshold
            mistral_api_key: Mistral API key (for mistral_api model type)
        """
        # Initialize RAG system
        self.rag = DynamicLegalRAG(
            top_k=rag_top_k,
            bm25_weight=bm25_weight,
            vector_weight=vector_weight,
            similarity_threshold=similarity_threshold
        )
        
        # Initialize summarizer
        summarizer_kwargs = {
            'model_type': summarizer_model_type,
            'model_name': summarizer_model_name,
            'compression_ratio': compression_ratio
        }
        if mistral_api_key:
            summarizer_kwargs['mistral_api_key'] = mistral_api_key
        
        self.summarizer = LegalSummarizer(**summarizer_kwargs)
        
        logger.info("Integrated RAG + Summarization system initialized")
    
    def process(self,
                query_or_text: str,
                judgment_id: Optional[int] = None,
                generate_summary: bool = True) -> Dict:
        """
        Process query/text through complete pipeline
        
        Args:
            query_or_text: Query string or judgment text
            judgment_id: Optional judgment ID for filtering
            generate_summary: Whether to generate summary
            
        Returns:
            Dict containing RAG results and summary
        """
        # Step 1: RAG retrieval
        logger.info("Step 1: RAG retrieval...")
        rag_result = self.rag.process(
            query_or_text,
            judgment_id=judgment_id,
            retrieve_legal_sections=True
        )
        
        result = {
            'rag_result': rag_result,
            'summary': None,
            'summary_result': None
        }
        
        # Step 2: Summarization (if requested)
        if generate_summary:
            logger.info("Step 2: Generating summary...")
            try:
                summary_result = self.summarizer.summarize(
                    context=rag_result.context,
                    original_text=query_or_text if len(query_or_text) > 500 else None,
                    metadata={
                        'case_number': rag_result.retrieved_chunks[0].get('case_number') if rag_result.retrieved_chunks else None,
                        'judgment_id': judgment_id
                    }
                )
                
                result['summary'] = summary_result.summary
                result['summary_result'] = summary_result
                
                # Calculate actual compression ratio
                if len(query_or_text) > 0:
                    actual_ratio = self.summarizer.calculate_compression_ratio(
                        query_or_text, summary_result.summary
                    )
                    result['compression_ratio'] = actual_ratio
                
                logger.info(f"Summary generated: {len(summary_result.summary)} chars")
            except Exception as e:
                logger.error(f"Summarization failed: {e}")
                result['summary_error'] = str(e)
        
        return result
    
    def initialize_bm25(self, documents: List[str], chunk_ids: List[int]):
        """Initialize BM25 index"""
        self.rag.initialize_bm25_index(documents, chunk_ids)


def create_integrated_system(rag_top_k: int = 3,
                            summarizer_model_type: str = "openai",
                            summarizer_model_name: str = "gpt-4") -> IntegratedRAGWithSummarization:
    """Factory function to create integrated system"""
    return IntegratedRAGWithSummarization(
        rag_top_k=rag_top_k,
        summarizer_model_type=summarizer_model_type,
        summarizer_model_name=summarizer_model_name
    )
