"""
Comprehensive test script for Dynamic Legal RAG system
Tests various query types and displays results
"""

import sys
from pathlib import Path
import os

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Fix import conflict
if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from rag.dynamic_legal_rag import DynamicLegalRAG
from database.connection import get_db_manager
import logging
from typing import List, Dict
import json

logging.basicConfig(level=logging.WARNING)  # Reduce noise
logger = logging.getLogger(__name__)


class RAGTester:
    """Test suite for RAG system"""
    
    def __init__(self):
        self.rag = DynamicLegalRAG(top_k=3, bm25_weight=0.4, vector_weight=0.6)
        self.db = get_db_manager()
        self.bm25_initialized = False
    
    def initialize_bm25(self):
        """Initialize BM25 index if not done"""
        if self.bm25_initialized:
            return
        
        print("Initializing BM25 index...")
        chunks = self.db.execute_query("SELECT id, content FROM judgment_chunks ORDER BY id")
        if chunks:
            documents = [row['content'] for row in chunks]
            chunk_ids = [row['id'] for row in chunks]
            self.rag.hybrid_retriever.initialize_bm25(documents, chunk_ids)
            print(f"[OK] BM25 index initialized with {len(documents)} chunks\n")
            self.bm25_initialized = True
        else:
            print("[WARNING] No chunks found in database")
    
    def test_query(self, query: str, description: str = ""):
        """Test a single query and display results"""
        print("\n" + "="*80)
        print(f"TEST QUERY: {description or 'General Query'}")
        print("="*80)
        print(f"\nOriginal Query:\n  {query}\n")
        
        try:
            result = self.rag.process(query, retrieve_legal_sections=True)
            
            # Enhanced Query
            print("-"*80)
            print("ENHANCED QUERY:")
            print("-"*80)
            print(f"  {result.enhanced_query}\n")
            
            # Entities
            if result.entities:
                print("-"*80)
                print(f"EXTRACTED ENTITIES ({len(result.entities)} found):")
                print("-"*80)
                entity_by_type = {}
                for entity in result.entities:
                    etype = entity.entity_type.name
                    if etype not in entity_by_type:
                        entity_by_type[etype] = []
                    entity_by_type[etype].append(entity.text)
                
                for etype, texts in entity_by_type.items():
                    print(f"\n  {etype}:")
                    for text in texts[:5]:  # Show first 5
                        print(f"    - {text}")
                    if len(texts) > 5:
                        print(f"    ... and {len(texts) - 5} more")
            
            # Dark Zones
            if result.dark_zones:
                print("\n" + "-"*80)
                print(f"DARK ZONES DETECTED ({len(result.dark_zones)}):")
                print("-"*80)
                for i, dz in enumerate(result.dark_zones[:3], 1):
                    print(f"\n  {i}. {dz.section_entity.text}")
                    print(f"     Context: {dz.context_window[:150]}...")
                    if dz.resolution_suggestions:
                        print(f"     Suggestion: {dz.resolution_suggestions[0][:100]}...")
            
            # Retrieved Chunks
            print("\n" + "-"*80)
            print(f"RETRIEVED CHUNKS ({len(result.retrieved_chunks)}):")
            print("-"*80)
            for i, chunk in enumerate(result.retrieved_chunks, 1):
                print(f"\n  Chunk {i}:")
                print(f"    Case: {chunk.get('case_number', 'N/A')}")
                print(f"    Section Type: {chunk.get('section_type', 'N/A')}")
                if chunk.get('date'):
                    print(f"    Date: {chunk['date']}")
                print(f"    Content Preview: {chunk['content'][:200]}...")
            
            # Context Summary
            print("\n" + "-"*80)
            print("ASSEMBLED CONTEXT (Preview):")
            print("-"*80)
            context_preview = result.context[:800] + "..." if len(result.context) > 800 else result.context
            print(f"  {context_preview}")
            
            # Metadata
            print("\n" + "-"*80)
            print("METADATA:")
            print("-"*80)
            for key, value in result.metadata.items():
                print(f"  {key}: {value}")
            
            return result
            
        except Exception as e:
            print(f"\n[ERROR] Query failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        self.initialize_bm25()
        
        test_queries = [
            {
                "query": "What are the legal provisions for murder conviction under IPC Section 302?",
                "description": "IPC Section Query"
            },
            {
                "query": "Explain the procedure for bail in criminal cases under CrPC",
                "description": "CrPC Procedure Query"
            },
            {
                "query": "What are the key considerations for sentencing in murder cases?",
                "description": "Sentencing Query"
            },
            {
                "query": "How is evidence evaluated in criminal trials?",
                "description": "Evidence Evaluation Query"
            },
            {
                "query": "Find cases related to Section 302 IPC and Section 307 IPC",
                "description": "Multiple Section Query"
            },
            {
                "query": "What is the difference between culpable homicide and murder?",
                "description": "Legal Concept Comparison"
            }
        ]
        
        results = []
        for test in test_queries:
            result = self.test_query(test["query"], test["description"])
            if result:
                results.append({
                    "description": test["description"],
                    "query": test["query"],
                    "enhanced_query": result.enhanced_query,
                    "entities_count": len(result.entities),
                    "dark_zones_count": len(result.dark_zones),
                    "chunks_retrieved": len(result.retrieved_chunks)
                })
            print("\n\n")
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"\nTotal Tests: {len(test_queries)}")
        print(f"Successful: {len(results)}")
        print(f"\nAverage Entities per Query: {sum(r['entities_count'] for r in results) / len(results):.1f}")
        print(f"Average Dark Zones per Query: {sum(r['dark_zones_count'] for r in results) / len(results):.1f}")
        print(f"Average Chunks Retrieved: {sum(r['chunks_retrieved'] for r in results) / len(results):.1f}")


def interactive_mode():
    """Interactive query mode"""
    tester = RAGTester()
    tester.initialize_bm25()
    
    print("\n" + "="*80)
    print("INTERACTIVE RAG TEST MODE")
    print("="*80)
    print("\nEnter queries to test the RAG system.")
    print("Type 'exit' or 'quit' to stop.\n")
    
    while True:
        try:
            query = input("Query> ").strip()
            if not query or query.lower() in ['exit', 'quit', 'q']:
                break
            
            tester.test_query(query, "Interactive Query")
            print("\n")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Dynamic Legal RAG system")
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Run in interactive mode')
    parser.add_argument('--query', '-q', type=str,
                       help='Test a single query')
    
    args = parser.parse_args()
    
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = 'postgres'
    
    tester = RAGTester()
    
    if args.interactive:
        interactive_mode()
    elif args.query:
        tester.initialize_bm25()
        tester.test_query(args.query, "Custom Query")
    else:
        # Run all tests
        print("\n" + "="*80)
        print("DYNAMIC LEGAL RAG - COMPREHENSIVE TEST SUITE")
        print("="*80)
        tester.run_all_tests()


if __name__ == "__main__":
    main()
