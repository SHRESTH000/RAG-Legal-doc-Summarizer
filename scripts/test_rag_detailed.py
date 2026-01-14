"""
Detailed RAG testing with full context display and legal section retrieval
"""

import sys
from pathlib import Path
import os

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from rag.dynamic_legal_rag import DynamicLegalRAG
from database.connection import get_db_manager
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def test_with_legal_sections(query: str):
    """Test query and show retrieved legal sections"""
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = 'postgres'
    
    # Initialize RAG
    rag = DynamicLegalRAG(top_k=5, bm25_weight=0.4, vector_weight=0.6)
    
    # Initialize BM25
    print("Initializing BM25 index...")
    db = get_db_manager()
    chunks = db.execute_query("SELECT id, content FROM judgment_chunks ORDER BY id")
    if chunks:
        documents = [row['content'] for row in chunks]
        chunk_ids = [row['id'] for row in chunks]
        rag.hybrid_retriever.initialize_bm25(documents, chunk_ids)
        print(f"[OK] BM25 index initialized with {len(documents)} chunks\n")
    
    print("="*80)
    print(f"QUERY: {query}")
    print("="*80)
    
    result = rag.process(query, retrieve_legal_sections=True)
    
    # Show entities in detail
    if result.entities:
        print("\n" + "-"*80)
        print("EXTRACTED ENTITIES:")
        print("-"*80)
        for entity in result.entities:
            metadata_str = ""
            if entity.metadata:
                metadata_str = f" [{entity.metadata}]"
            print(f"  {entity.entity_type.name:15s}: {entity.text}{metadata_str}")
    
    # Show dark zones
    if result.dark_zones:
        print("\n" + "-"*80)
        print("DARK ZONES (Unexplained Legal References):")
        print("-"*80)
        for i, dz in enumerate(result.dark_zones, 1):
            print(f"\n  {i}. {dz.section_entity.text}")
            print(f"     Context: {dz.context_window[:200]}...")
            if dz.resolution_suggestions:
                print(f"     Resolution: {dz.resolution_suggestions[0][:150]}...")
    
    # Show retrieved legal sections
    context_parts = result.context.split("[LEGAL SECTIONS]")
    if len(context_parts) > 1:
        legal_sections_text = context_parts[1].split("[DARK ZONE RESOLUTIONS]")[0]
        if legal_sections_text.strip():
            print("\n" + "="*80)
            print("RETRIEVED LEGAL SECTIONS:")
            print("="*80)
            print(legal_sections_text[:2000])
            if len(legal_sections_text) > 2000:
                print("\n... (truncated)")
    
    # Show retrieved chunks with scores
    print("\n" + "="*80)
    print("RETRIEVED JUDGMENT CHUNKS:")
    print("="*80)
    for i, chunk in enumerate(result.retrieved_chunks, 1):
        print(f"\n[{i}] Case: {chunk.get('case_number', 'N/A')}")
        print(f"    Section Type: {chunk.get('section_type', 'N/A')}")
        if chunk.get('date'):
            print(f"    Date: {chunk['date']}")
        content_preview = chunk['content'][:400].replace('\n', ' ')
        print(f"    Content: {content_preview}...")
    
    # Show summary stats
    print("\n" + "="*80)
    print("RETRIEVAL STATISTICS:")
    print("="*80)
    print(f"  Total Chunks Retrieved: {result.metadata['chunks_retrieved']}")
    print(f"  Entities Extracted: {result.metadata['entities_found']}")
    print(f"  Dark Zones Detected: {result.metadata['dark_zones_found']}")
    print(f"  Legal Sections Retrieved: {result.metadata['legal_sections_retrieved']}")
    
    return result


def main():
    test_queries = [
        "Explain IPC Section 302 and find relevant case law",
        "What are the provisions under CrPC Section 436A for bail?",
        "Find cases discussing Section 300 and Section 302 of IPC together",
        "What is the procedure under Evidence Act Section 27?",
    ]
    
    for query in test_queries:
        test_with_legal_sections(query)
        print("\n\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
