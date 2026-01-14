"""
Hybrid Retrieval System
Combines BM25 and Vector Search for better retrieval
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import logging

from database.connection import get_db_manager

logger = logging.getLogger(__name__)


class BM25Retriever:
    """BM25-based retriever using Rank-BM25"""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 retriever
        
        Args:
            k1: Term frequency saturation parameter
            b: Length normalization parameter
        """
        self.k1 = k1
        self.b = b
        self.bm25: Optional[BM25Okapi] = None
        self.corpus: List[str] = []
        self.chunk_ids: List[int] = []
        self._is_initialized = False
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        return text.lower().split()
    
    def build_index(self, documents: List[str], chunk_ids: List[int]):
        """
        Build BM25 index from documents
        
        Args:
            documents: List of document texts
            chunk_ids: Corresponding chunk IDs
        """
        if len(documents) != len(chunk_ids):
            raise ValueError("Documents and chunk_ids must have same length")
        
        self.corpus = documents
        self.chunk_ids = chunk_ids
        tokenized_corpus = [self._tokenize(doc) for doc in documents]
        self.bm25 = BM25Okapi(tokenized_corpus, k1=self.k1, b=self.b)
        self._is_initialized = True
        logger.info(f"BM25 index built with {len(documents)} documents")
    
    def retrieve(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Retrieve top-k documents using BM25
        
        Args:
            query: Query string
            top_k: Number of results to return
            
        Returns:
            List of (chunk_id, score) tuples
        """
        if not self._is_initialized:
            raise ValueError("BM25 index not initialized. Call build_index() first.")
        
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only return documents with positive scores
                results.append((self.chunk_ids[idx], float(scores[idx])))
        
        return results


class VectorRetriever:
    """Vector-based retriever using pgvector"""
    
    def __init__(self, 
                 model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                 similarity_threshold: float = 0.7):
        """
        Initialize vector retriever
        
        Args:
            model_name: Sentence transformer model name
            similarity_threshold: Minimum similarity threshold
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.similarity_threshold = similarity_threshold
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Vector retriever initialized with model: {model_name}")
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """Encode texts to embeddings"""
        return self.model.encode(texts, show_progress_bar=False)
    
    def retrieve(self, 
                 query: str, 
                 top_k: int = 10,
                 judgment_id: Optional[int] = None) -> List[Tuple[int, float]]:
        """
        Retrieve top-k chunks using vector similarity
        
        Args:
            query: Query string
            top_k: Number of results to return
            judgment_id: Optional filter by judgment ID
            
        Returns:
            List of (chunk_id, similarity_score) tuples
        """
        # Encode query
        query_embedding = self.encode([query])[0]
        query_embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        db = get_db_manager()
        
        # Check if pgvector is available
        try:
            # Try pgvector query first
            if judgment_id:
                sql = """
                    SELECT 
                        id,
                        1 - (embedding::vector <=> %s::vector) as similarity
                    FROM judgment_chunks
                    WHERE judgment_id = %s
                    AND 1 - (embedding::vector <=> %s::vector) >= %s
                    ORDER BY embedding::vector <=> %s::vector
                    LIMIT %s
                """
                params = (query_embedding_str, judgment_id, query_embedding_str, 
                         self.similarity_threshold, query_embedding_str, top_k)
            else:
                sql = """
                    SELECT 
                        id,
                        1 - (embedding::vector <=> %s::vector) as similarity
                    FROM judgment_chunks
                    WHERE 1 - (embedding::vector <=> %s::vector) >= %s
                    ORDER BY embedding::vector <=> %s::vector
                    LIMIT %s
                """
                params = (query_embedding_str, query_embedding_str, 
                         self.similarity_threshold, query_embedding_str, top_k)
            
            rows = db.execute_query(sql, params)
            results = []
            for row in rows:
                results.append((row['id'], float(row['similarity'])))
            return results
            
        except Exception as e:
            # Fallback: compute cosine similarity in Python
            logger.warning(f"pgvector not available, using Python-based vector search: {e}")
            return self._retrieve_fallback(query_embedding, top_k, judgment_id)
    
    def _retrieve_fallback(self, 
                          query_embedding: np.ndarray,
                          top_k: int,
                          judgment_id: Optional[int] = None) -> List[Tuple[int, float]]:
        """Fallback vector search using Python cosine similarity"""
        import numpy as np
        
        db = get_db_manager()
        
        # Get all chunks
        if judgment_id:
            sql = "SELECT id, embedding FROM judgment_chunks WHERE judgment_id = %s"
            rows = db.execute_query(sql, (judgment_id,))
        else:
            sql = "SELECT id, embedding FROM judgment_chunks"
            rows = db.execute_query(sql)
        
        if not rows:
            return []
        
        # Compute similarities
        similarities = []
        query_norm = np.linalg.norm(query_embedding)
        
        for row in rows:
            chunk_id = row['id']
            embedding_str = row['embedding']
            
            if not embedding_str:
                continue
            
            try:
                # Parse embedding (stored as text like "[0.1,0.2,0.3]")
                if isinstance(embedding_str, str):
                    # Remove brackets and split
                    clean_str = embedding_str.strip().strip('[]')
                    if clean_str:
                        chunk_embedding = np.array([float(x.strip()) for x in clean_str.split(',') if x.strip()])
                    else:
                        continue
                elif isinstance(embedding_str, (list, tuple)):
                    chunk_embedding = np.array(embedding_str)
                else:
                    continue
                
                # Cosine similarity
                chunk_norm = np.linalg.norm(chunk_embedding)
                if chunk_norm > 0:
                    similarity = np.dot(query_embedding, chunk_embedding) / (query_norm * chunk_norm)
                    if similarity >= self.similarity_threshold:
                        similarities.append((chunk_id, float(similarity)))
            except Exception as e:
                logger.debug(f"Error processing chunk {chunk_id}: {e}")
                continue
        
        # Sort by similarity and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


class HybridRetriever:
    """
    Hybrid retriever combining BM25 and Vector Search
    Uses Reciprocal Rank Fusion (RRF) - industry standard for hybrid retrieval
    """
    
    def __init__(self,
                 bm25_weight: float = 0.4,  # Deprecated, kept for backward compatibility
                 vector_weight: float = 0.6,  # Deprecated, kept for backward compatibility
                 bm25_k1: float = 1.5,
                 bm25_b: float = 0.75,
                 vector_model: str = "sentence-transformers/all-MiniLM-L6-v2",
                 similarity_threshold: float = 0.5,  # Lowered from 0.7 to 0.5 for better coverage
                 rrf_k: int = 60):
        """
        Initialize hybrid retriever using RRF (Reciprocal Rank Fusion)
        
        Args:
            bm25_weight: Deprecated (kept for backward compatibility, not used)
            vector_weight: Deprecated (kept for backward compatibility, not used)
            bm25_k1: BM25 k1 parameter
            bm25_b: BM25 b parameter
            vector_model: Vector model name
            similarity_threshold: Vector similarity threshold (default: 0.5)
            rrf_k: RRF constant (default: 60, standard value)
        """
        self.rrf_k = rrf_k
        self.bm25_retriever = BM25Retriever(k1=bm25_k1, b=bm25_b)
        self.vector_retriever = VectorRetriever(
            model_name=vector_model,
            similarity_threshold=similarity_threshold
        )
        
        logger.info(f"Hybrid retriever initialized with RRF (k={rrf_k}), "
                   f"similarity_threshold={similarity_threshold}")
    
    def initialize_bm25(self, documents: List[str], chunk_ids: List[int]):
        """Initialize BM25 index with documents"""
        self.bm25_retriever.build_index(documents, chunk_ids)
    
    def retrieve(self, 
                 query: str, 
                 top_k: int = 20,
                 judgment_id: Optional[int] = None) -> List[Tuple[int, float]]:
        """
        Retrieve documents using Reciprocal Rank Fusion (RRF)
        
        RRF formula: score = sum(1 / (rank_i + k)) for each retriever
        This combines ranks from both retrievers without requiring score normalization.
        
        Args:
            query: Query string
            top_k: Number of results to return
            judgment_id: Optional filter by judgment ID
            
        Returns:
            List of (chunk_id, rrf_score) tuples
        """
        # Get results from both retrievers (retrieve more candidates for better fusion)
        bm25_results: List[Tuple[int, float]] = []
        vector_results: List[Tuple[int, float]] = []
        
        # BM25 retrieval
        if self.bm25_retriever._is_initialized:
            bm25_results = self.bm25_retriever.retrieve(query, top_k * 5)  # Get more candidates
        
        # Vector retrieval
        vector_results = self.vector_retriever.retrieve(query, top_k * 5, judgment_id)  # Get more candidates
        
        # Use RRF to combine results
        combined_results = self._reciprocal_rank_fusion(bm25_results, vector_results, top_k)
        
        return combined_results
    
    def _reciprocal_rank_fusion(self,
                                bm25_results: List[Tuple[int, float]],
                                vector_results: List[Tuple[int, float]],
                                top_k: int) -> List[Tuple[int, float]]:
        """
        Combine results using Reciprocal Rank Fusion (RRF)
        
        RRF formula: score = sum(1 / (rank_i + k)) for each retriever
        where rank_i is the rank in retriever i (1-indexed)
        
        Args:
            bm25_results: List of (chunk_id, score) from BM25
            vector_results: List of (chunk_id, score) from Vector
            top_k: Number of final results to return
            
        Returns:
            List of (chunk_id, rrf_score) sorted by RRF score
        """
        # Create rank mappings (rank starts at 1)
        bm25_ranks: Dict[int, int] = {}
        for rank, (chunk_id, _) in enumerate(bm25_results, start=1):
            bm25_ranks[chunk_id] = rank
        
        vector_ranks: Dict[int, int] = {}
        for rank, (chunk_id, _) in enumerate(vector_results, start=1):
            vector_ranks[chunk_id] = rank
        
        # Calculate RRF scores for all unique chunk IDs
        all_chunk_ids = set(bm25_ranks.keys()) | set(vector_ranks.keys())
        rrf_scores: Dict[int, float] = {}
        
        for chunk_id in all_chunk_ids:
            score = 0.0
            
            # Add BM25 contribution
            if chunk_id in bm25_ranks:
                rank = bm25_ranks[chunk_id]
                score += 1.0 / (rank + self.rrf_k)
            
            # Add Vector contribution
            if chunk_id in vector_ranks:
                rank = vector_ranks[chunk_id]
                score += 1.0 / (rank + self.rrf_k)
            
            rrf_scores[chunk_id] = score
        
        # Sort by RRF score (descending) and return top-k
        sorted_results = sorted(rrf_scores.items(), 
                              key=lambda x: x[1], 
                              reverse=True)
        
        return sorted_results[:top_k]
