"""
Example script demonstrating Dynamic Legal RAG usage
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Fix import conflict
if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from rag.dynamic_legal_rag import DynamicLegalRAG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    from database.connection import get_db_manager
    
    # Initialize RAG system (following base paper: top-3)
    rag = DynamicLegalRAG(top_k=3, bm25_weight=0.4, vector_weight=0.6)
    
    # Initialize BM25 index if not already done
    print("Initializing BM25 index...")
    db = get_db_manager()
    chunks = db.execute_query("SELECT id, content FROM judgment_chunks ORDER BY id")
    if chunks:
        documents = [row['content'] for row in chunks]
        chunk_ids = [row['id'] for row in chunks]
        rag.hybrid_retriever.initialize_bm25(documents, chunk_ids)
        print(f"[OK] BM25 index initialized with {len(documents)} chunks\n")
    
    # Example query
    query = """
    What are the legal provisions for murder conviction under IPC?
    Find relevant sections and case law.
    """
    
    print("="*60)
    print("Dynamic Legal RAG - Example Usage")
    print("="*60)
    print(f"\nQuery: {query}\n")
    
    # Process through RAG
    result = rag.process(query, retrieve_legal_sections=True)
    
    # Display results
    print(f"\nEnhanced Query: {result.enhanced_query[:200]}...")
    print(f"\nEntities Found: {result.metadata['entities_found']}")
    print(f"Dark Zones: {result.metadata['dark_zones_found']}")
    print(f"Chunks Retrieved: {result.metadata['chunks_retrieved']}")
    
    print(f"\n{'='*60}")
    print("RETRIEVED CONTEXT")
    print("="*60)
    print(result.context[:2000] + "..." if len(result.context) > 2000 else result.context)
    
    print(f"\n{'='*60}")
    print("ENTITIES")
    print("="*60)
    for entity in result.entities[:10]:
        print(f"  {entity.entity_type.name}: {entity.text}")
    
    if result.dark_zones:
        print(f"\n{'='*60}")
        print("DARK ZONES DETECTED")
        print("="*60)
        for dz in result.dark_zones[:5]:
            print(f"  {dz.section_entity.text}")
            print(f"    Context: {dz.context_window[:100]}...")
            if dz.resolution_suggestions:
                print(f"    Suggestions: {dz.resolution_suggestions[0]}")


if __name__ == "__main__":
    main()
