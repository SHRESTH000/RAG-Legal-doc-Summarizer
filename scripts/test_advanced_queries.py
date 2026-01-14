"""
Advanced query testing with detailed analysis
Tests complex legal queries and performance metrics
"""

import sys
from pathlib import Path
import os
import time

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from rag.dynamic_legal_rag import DynamicLegalRAG
from database.connection import get_db_manager
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def test_advanced_queries():
    """Test advanced legal queries"""
    
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = 'postgres'
    
    rag = DynamicLegalRAG(top_k=5, bm25_weight=0.4, vector_weight=0.6)
    db = get_db_manager()
    
    # Initialize BM25
    print("Initializing BM25 index...")
    chunks = db.execute_query("SELECT id, content FROM judgment_chunks ORDER BY id")
    if chunks:
        documents = [row['content'] for row in chunks]
        chunk_ids = [row['id'] for row in chunks]
        rag.hybrid_retriever.initialize_bm25(documents, chunk_ids)
        print(f"[OK] BM25 initialized with {len(documents)} chunks\n")
    
    advanced_queries = [
        {
            "category": "Multi-Statute Query",
            "query": "Compare procedures under Section 439 CrPC for bail cancellation and Section 482 CrPC for quashing criminal proceedings",
            "expected": ["Section 439", "Section 482", "bail", "quashing"]
        },
        {
            "category": "Constitutional Law Query",
            "query": "What are the constitutional provisions regarding fundamental rights in criminal cases?",
            "expected": ["constitution", "fundamental rights"]
        },
        {
            "category": "Evidence Law Query",
            "query": "Explain the admissibility of confessions under Section 24 and Section 25 of the Evidence Act",
            "expected": ["Section 24", "Section 25", "confession", "Evidence Act"]
        },
        {
            "category": "Case Law Query",
            "query": "Find Supreme Court judgments on death penalty commutation in murder cases",
            "expected": ["death penalty", "commutation", "murder"]
        },
        {
            "category": "Procedural Law Query",
            "query": "What is the procedure for framing charges under Section 228 CrPC?",
            "expected": ["Section 228", "framing charges", "CrPC"]
        },
        {
            "category": "Criminal Law Doctrine",
            "query": "Explain the doctrine of common intention under Section 34 IPC with relevant case law",
            "expected": ["Section 34", "common intention", "doctrine"]
        },
        {
            "category": "Evidence Evaluation",
            "query": "How are dying declarations evaluated under Section 32 of the Evidence Act?",
            "expected": ["Section 32", "dying declaration", "Evidence Act"]
        },
        {
            "category": "Sentencing Guidelines",
            "query": "What factors are considered for determining appropriate punishment in culpable homicide cases?",
            "expected": ["punishment", "culpable homicide", "sentencing"]
        }
    ]
    
    results = []
    
    print("="*80)
    print("ADVANCED LEGAL QUERY TESTING")
    print("="*80)
    
    for i, test in enumerate(advanced_queries, 1):
        print(f"\n[{i}/{len(advanced_queries)}] {test['category']}")
        print("-"*80)
        print(f"Query: {test['query']}\n")
        
        start_time = time.time()
        result = rag.process(test['query'], retrieve_legal_sections=True)
        elapsed = time.time() - start_time
        
        # Analyze results
        entities_found = [e.text.lower() for e in result.entities]
        enhanced_query_lower = result.enhanced_query.lower()
        expected_found = [exp for exp in test['expected'] 
                         if exp.lower() in ' '.join(entities_found) or exp.lower() in enhanced_query_lower]
        
        print(f"Response Time: {elapsed:.2f}s")
        print(f"Entities Found: {len(result.entities)}")
        print(f"Dark Zones: {len(result.dark_zones)}")
        print(f"Chunks Retrieved: {len(result.retrieved_chunks)}")
        print(f"Expected Terms Found: {len(expected_found)}/{len(test['expected'])}")
        
        # Show key entities
        if result.entities:
            print("\nKey Entities:")
            for entity in result.entities[:5]:
                print(f"  - {entity.entity_type.name}: {entity.text}")
        
        # Show retrieved chunks summary
        if result.retrieved_chunks:
            print("\nRetrieved Chunks:")
            for j, chunk in enumerate(result.retrieved_chunks[:3], 1):
                print(f"  {j}. {chunk.get('case_number', 'N/A')} ({chunk.get('section_type', 'N/A')})")
                print(f"     {chunk['content'][:100]}...")
        
        # Legal sections retrieved
        if "LEGAL SECTIONS" in result.context:
            print("\n[OK] Legal sections retrieved")
        
        results.append({
            "category": test['category'],
            "query": test['query'],
            "response_time": elapsed,
            "entities_count": len(result.entities),
            "dark_zones_count": len(result.dark_zones),
            "chunks_retrieved": len(result.retrieved_chunks),
            "expected_terms_covered": len(expected_found),
            "legal_sections_retrieved": "LEGAL SECTIONS" in result.context
        })
        
        time.sleep(0.5)  # Brief pause between queries
    
    # Summary Report
    print("\n" + "="*80)
    print("PERFORMANCE SUMMARY")
    print("="*80)
    
    avg_time = sum(r['response_time'] for r in results) / len(results)
    avg_entities = sum(r['entities_count'] for r in results) / len(results)
    avg_chunks = sum(r['chunks_retrieved'] for r in results) / len(results)
    avg_terms = sum(r['expected_terms_covered'] for r in results) / len(results)
    sections_coverage = sum(1 for r in results if r['legal_sections_retrieved']) / len(results) * 100
    
    print(f"\nTotal Queries: {len(results)}")
    print(f"Average Response Time: {avg_time:.2f}s")
    print(f"Average Entities per Query: {avg_entities:.1f}")
    print(f"Average Chunks Retrieved: {avg_chunks:.1f}")
    print(f"Expected Terms Coverage: {avg_terms:.1f}")
    print(f"Legal Sections Coverage: {sections_coverage:.1f}%")
    
    print("\n" + "-"*80)
    print("Query Performance Breakdown:")
    print("-"*80)
    for r in results:
        print(f"\n{r['category']}:")
        print(f"  Time: {r['response_time']:.2f}s | Entities: {r['entities_count']} | "
              f"Chunks: {r['chunks_retrieved']} | Sections: {'Yes' if r['legal_sections_retrieved'] else 'No'}")
    
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    if avg_time > 2.0:
        print("- Response times could be optimized (consider caching BM25 index)")
    if avg_entities < 2:
        print("- NER extraction could be improved for better entity coverage")
    if sections_coverage < 70:
        print("- Legal section retrieval could be enhanced")
    if avg_chunks < 3:
        print("- Consider increasing corpus size for better retrieval coverage")
    
    print("\n[OK] Testing complete!")
    
    return results


def test_specific_legal_sections():
    """Test retrieval of specific legal sections"""
    
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = 'postgres'
    
    rag = DynamicLegalRAG(top_k=3, bm25_weight=0.4, vector_weight=0.6)
    db = get_db_manager()
    
    # Initialize BM25
    chunks = db.execute_query("SELECT id, content FROM judgment_chunks ORDER BY id LIMIT 50000")
    if chunks:
        documents = [row['content'] for row in chunks]
        chunk_ids = [row['id'] for row in chunks]
        rag.hybrid_retriever.initialize_bm25(documents, chunk_ids)
    
    print("\n" + "="*80)
    print("LEGAL SECTION RETRIEVAL TEST")
    print("="*80)
    
    test_sections = [
        "IPC Section 302",
        "IPC Section 304",
        "CrPC Section 439",
        "Evidence Act Section 32",
        "IPC Section 34",
        "CrPC Section 482"
    ]
    
    for section in test_sections:
        print(f"\nTesting: {section}")
        query = f"What does {section} say?"
        result = rag.process(query, retrieve_legal_sections=True)
        
        if result.entities:
            section_entities = [e for e in result.entities if e.entity_type.name == 'LEGAL_SECTION']
            if section_entities:
                print(f"  [OK] Section detected: {section_entities[0].text}")
        
        if "LEGAL SECTIONS" in result.context:
            print(f"  [OK] Legal section content retrieved")
            # Extract section content from context
            sections_part = result.context.split("[LEGAL SECTIONS]")[1].split("[")[0] if "[LEGAL SECTIONS]" in result.context else ""
            if sections_part:
                preview = sections_part.strip()[:200]
                print(f"  Preview: {preview}...")
        else:
            print(f"  [WARNING] Legal section not retrieved")


if __name__ == "__main__":
    print("\nStarting Advanced Query Testing...")
    results = test_advanced_queries()
    
    print("\n" + "="*80)
    print("\nStarting Legal Section Retrieval Test...")
    test_specific_legal_sections()
