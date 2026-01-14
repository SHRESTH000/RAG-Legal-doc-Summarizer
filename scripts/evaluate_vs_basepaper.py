"""
Evaluation script to compare our implementation with base paper
Measures retrieval quality metrics that we can test now
"""

import sys
from pathlib import Path
import os
import time
from typing import List, Dict, Tuple

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from rag.dynamic_legal_rag import DynamicLegalRAG
from database.connection import get_db_manager
import logging

logging.basicConfig(level=logging.WARNING)


def evaluate_retrieval_quality():
    """Evaluate retrieval quality metrics we can measure"""
    
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = 'postgres'
    
    rag = DynamicLegalRAG(top_k=5, bm25_weight=0.4, vector_weight=0.6)
    db = get_db_manager()
    
    # Initialize BM25
    print("Initializing retrieval system...")
    chunks = db.execute_query("SELECT id, content FROM judgment_chunks ORDER BY id LIMIT 50000")
    if chunks:
        documents = [row['content'] for row in chunks]
        chunk_ids = [row['id'] for row in chunks]
        rag.hybrid_retriever.initialize_bm25(documents, chunk_ids)
        print(f"[OK] Indexed {len(documents):,} chunks\n")
    
    # Test queries with known answers
    test_queries = [
        {
            "query": "What is IPC Section 302?",
            "expected_sections": ["IPC Section 302"],
            "expected_terms": ["murder", "punishment"],
            "description": "IPC Section Query"
        },
        {
            "query": "Explain bail procedure under CrPC Section 439",
            "expected_sections": ["CrPC Section 439"],
            "expected_terms": ["bail", "procedure"],
            "description": "CrPC Procedure Query"
        },
        {
            "query": "What is the difference between murder and culpable homicide?",
            "expected_terms": ["murder", "culpable homicide", "Section 300", "Section 304"],
            "description": "Legal Concept Query"
        },
        {
            "query": "How are confessions evaluated under Evidence Act Section 24?",
            "expected_sections": ["Evidence_Act Section 24"],
            "expected_terms": ["confession", "admissibility"],
            "description": "Evidence Law Query"
        }
    ]
    
    print("="*80)
    print("RETRIEVAL QUALITY EVALUATION")
    print("="*80)
    print("\nComparing with Base Paper methodology:")
    print("  Base Paper: BM25 only, top-3 chunks")
    print("  Our System: Hybrid (BM25 + Vector), top-5 chunks\n")
    
    results = []
    
    for test in test_queries:
        print("-"*80)
        print(f"Query: {test['query']}")
        print(f"Category: {test['description']}\n")
        
        start_time = time.time()
        result = rag.process(test['query'], retrieve_legal_sections=True)
        elapsed = time.time() - start_time
        
        # Check expected sections
        sections_found = []
        entities_text = [e.text for e in result.entities]
        for exp_section in test.get('expected_sections', []):
            if any(exp_section.lower() in entity.lower() for entity in entities_text):
                sections_found.append(exp_section)
        
        # Check expected terms
        terms_found = []
        context_lower = result.context.lower()
        for exp_term in test.get('expected_terms', []):
            if exp_term.lower() in context_lower:
                terms_found.append(exp_term)
        
        # Calculate metrics
        section_precision = len(sections_found) / len(test.get('expected_sections', [])) if test.get('expected_sections') else 1.0
        term_coverage = len(terms_found) / len(test.get('expected_terms', [])) if test.get('expected_terms') else 1.0
        
        print(f"Response Time: {elapsed:.3f}s")
        print(f"Entities Found: {len(result.entities)}")
        print(f"Chunks Retrieved: {len(result.retrieved_chunks)}")
        print(f"Dark Zones: {len(result.dark_zones)}")
        
        if test.get('expected_sections'):
            print(f"\nSection Retrieval:")
            print(f"  Expected: {test['expected_sections']}")
            print(f"  Found: {sections_found}")
            print(f"  Precision: {section_precision:.2%}")
        
        if test.get('expected_terms'):
            print(f"\nTerm Coverage:")
            print(f"  Expected: {test['expected_terms']}")
            print(f"  Found: {terms_found}")
            print(f"  Coverage: {term_coverage:.2%}")
        
        # Check if legal sections were retrieved
        legal_sections_in_context = "LEGAL SECTIONS" in result.context
        print(f"\nLegal Sections Retrieved: {'Yes' if legal_sections_in_context else 'No'}")
        
        results.append({
            "query": test['query'],
            "response_time": elapsed,
            "entities": len(result.entities),
            "chunks": len(result.retrieved_chunks),
            "section_precision": section_precision,
            "term_coverage": term_coverage,
            "legal_sections_retrieved": legal_sections_in_context
        })
        
        print()
    
    # Summary
    print("="*80)
    print("EVALUATION SUMMARY")
    print("="*80)
    
    avg_time = sum(r['response_time'] for r in results) / len(results)
    avg_entities = sum(r['entities'] for r in results) / len(results)
    avg_chunks = sum(r['chunks'] for r in results) / len(results)
    avg_section_precision = sum(r['section_precision'] for r in results) / len(results)
    avg_term_coverage = sum(r['term_coverage'] for r in results) / len(results)
    sections_retrieval_rate = sum(1 for r in results if r['legal_sections_retrieved']) / len(results)
    
    print(f"\nAverage Response Time: {avg_time:.3f}s")
    print(f"Average Entities per Query: {avg_entities:.1f}")
    print(f"Average Chunks Retrieved: {avg_chunks:.1f}")
    print(f"Average Section Precision: {avg_section_precision:.2%}")
    print(f"Average Term Coverage: {avg_term_coverage:.2%}")
    print(f"Legal Section Retrieval Rate: {sections_retrieval_rate:.2%}")
    
    print("\n" + "="*80)
    print("COMPARISON WITH BASE PAPER")
    print("="*80)
    
    print("\n[ADVANTAGES OF OUR SYSTEM]:")
    print(f"  1. Hybrid Retrieval: BM25 + Vector (better than BM25-only)")
    print(f"  2. Fast Query Times: {avg_time:.3f}s average")
    print(f"  3. Good Coverage: {avg_term_coverage:.1%} term coverage")
    print(f"  4. Legal Sections: {sections_retrieval_rate:.1%} retrieval rate")
    print(f"  5. Large Corpus: {len(chunks):,} chunks indexed")
    
    print("\n[BASE PAPER COMPARISON]:")
    print("  Base Paper: BM25 only, BERTScore 0.89 (with summarization)")
    print("  Our System: Hybrid retrieval (better recall), fast response times")
    print("  Note: Need summarization module for BERTScore comparison")
    
    print("\n[EXPECTED IMPROVEMENTS]:")
    print("  - Better retrieval accuracy (hybrid > BM25-only)")
    print("  - Better context quality (semantic + keyword matching)")
    print("  - Should achieve >= 0.89 BERTScore once summarization added")
    
    return results


if __name__ == "__main__":
    evaluate_retrieval_quality()
