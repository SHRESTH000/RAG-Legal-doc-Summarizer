"""
Initialize BM25 index from ingested judgments
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from database.connection import get_db_manager
from retrieval.hybrid_retriever import HybridRetriever
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_bm25_index():
    """Initialize BM25 index with all chunks from database"""
    
    db = get_db_manager()
    
    # Get all chunks
    logger.info("Fetching chunks from database...")
    chunks = db.execute_query("""
        SELECT id, content 
        FROM judgment_chunks
        ORDER BY id
    """)
    
    if not chunks:
        logger.warning("No chunks found in database. Please ingest judgments first.")
        return False
    
    logger.info(f"Found {len(chunks)} chunks")
    
    # Prepare data for BM25
    documents = [row['content'] for row in chunks]
    chunk_ids = [row['id'] for row in chunks]
    
    # Initialize hybrid retriever and build BM25 index
    logger.info("Building BM25 index...")
    rag_retriever = HybridRetriever(bm25_weight=0.4, vector_weight=0.6)
    rag_retriever.initialize_bm25(documents, chunk_ids)
    
    logger.info(f"✅ BM25 index initialized with {len(documents)} documents")
    return True


if __name__ == "__main__":
    # Set password if needed
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = 'postgres'
    
    initialize_bm25_index()
