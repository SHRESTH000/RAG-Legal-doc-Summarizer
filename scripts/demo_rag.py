"""
Interactive demo script for Dynamic Legal RAG
Shows system capabilities with example queries
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


def print_section(title, char="=", width=80):
    """Print a formatted section header"""
    print("\n" + char * width)
    print(title.center(width))
    print(char * width)


def demo_rag():
    """Interactive demo of RAG system"""
    
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = 'postgres'
    
    print_section("DYNAMIC LEGAL RAG SYSTEM - INTERACTIVE DEMO")
    
    # Initialize RAG
    print("\nInitializing RAG system...")
    rag = DynamicLegalRAG(top_k=5, bm25_weight=0.4, vector_weight=0.6)
    
    # Initialize BM25
    print("Loading BM25 index...")
    db = get_db_manager()
    chunks = db.execute_query("SELECT id, content FROM judgment_chunks ORDER BY id LIMIT 50000")
    if chunks:
        documents = [row['content'] for row in chunks]
        chunk_ids = [row['id'] for row in chunks]
        rag.hybrid_retriever.initialize_bm25(documents, chunk_ids)
        print(f"[OK] Loaded {len(documents):,} chunks\n")
    else:
        print("[ERROR] No chunks found")
        return
    
    # Example queries
    example_queries = [
        "What is IPC Section 302?",
        "Explain bail procedure under CrPC",
        "What is the difference between murder and culpable homicide?",
        "How are confessions handled under Evidence Act?",
        "Find cases on death penalty commutation"
    ]
    
    print_section("EXAMPLE QUERIES", "-")
    print("\nTry these example queries or enter your own:")
    for i, q in enumerate(example_queries, 1):
        print(f"  {i}. {q}")
    
    print("\n" + "=" * 80)
    print("Enter queries below (type 'quit' to exit, 'examples' to see examples)")
    print("=" * 80 + "\n")
    
    while True:
        try:
            query = input("\nQuery> ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nThank you for using Dynamic Legal RAG!")
                break
            
            if query.lower() == 'examples':
                print("\nExample Queries:")
                for i, q in enumerate(example_queries, 1):
                    print(f"  {i}. {q}")
                continue
            
            # Process query
            print("\nProcessing query...")
            result = rag.process(query, retrieve_legal_sections=True)
            
            # Display results
            print_section("RESULTS", "-")
            
            print(f"\nEnhanced Query:\n  {result.enhanced_query}")
            
            if result.entities:
                print(f"\nEntities Found ({len(result.entities)}):")
                for entity in result.entities[:5]:
                    print(f"  • {entity.entity_type.name}: {entity.text}")
            
            if result.dark_zones:
                print(f"\nDark Zones Detected ({len(result.dark_zones)}):")
                for dz in result.dark_zones[:3]:
                    print(f"  • {dz.section_entity.text}")
            
            print(f"\nRetrieved Chunks ({len(result.retrieved_chunks)}):")
            for i, chunk in enumerate(result.retrieved_chunks[:3], 1):
                print(f"\n  [{i}] Case: {chunk.get('case_number', 'N/A')}")
                if chunk.get('date'):
                    print(f"      Date: {chunk['date']}")
                print(f"      Type: {chunk.get('section_type', 'N/A')}")
                print(f"      Preview: {chunk['content'][:150]}...")
            
            if "LEGAL SECTIONS" in result.context:
                print("\n[OK] Legal sections retrieved and included in context")
            
            print(f"\n{'─' * 80}")
            print("Context assembled successfully! Ready for summarization.")
            print(f"{'─' * 80}")
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    demo_rag()
