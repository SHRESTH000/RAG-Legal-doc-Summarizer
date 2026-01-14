"""
Test Retrieval and Summarization with Mistral API
Tests the improved RRF retrieval + Mistral API summarization
"""

import sys
from pathlib import Path
import os
from typing import Dict, List

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from rag.integrated_rag_with_summarization import IntegratedRAGWithSummarization
from database.connection import get_db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_sample_judgment(limit: int = 1) -> Dict:
    """Get a sample judgment from database"""
    db = get_db_manager()
    
    query = """
        SELECT 
            j.id,
            j.case_number,
            j.title,
            j.judgment_date,
            j.court,
            j.year,
            STRING_AGG(jc.content, ' ') as full_text
        FROM judgments j
        LEFT JOIN judgment_chunks jc ON j.id = jc.judgment_id
        WHERE j.year IS NOT NULL
        GROUP BY j.id, j.case_number, j.title, j.judgment_date, j.court, j.year
        ORDER BY j.year DESC, j.id
        LIMIT %s
    """
    
    results = db.execute_query(query, (limit,))
    
    if not results:
        return None
    
    row = results[0]
    return {
        'id': row['id'],
        'case_number': row['case_number'],
        'title': row.get('title', ''),
        'date': str(row['judgment_date']) if row['judgment_date'] else None,
        'court': row.get('court', ''),
        'year': row.get('year'),
        'full_text': row.get('full_text', '')[:5000] if row.get('full_text') else ''
    }


def test_retrieval_and_summarization(mistral_api_key: str):
    """Test retrieval and summarization with Mistral API"""
    
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = 'postgres'
    
    print("="*80)
    print("TEST: RETRIEVAL + SUMMARIZATION WITH MISTRAL API")
    print("="*80)
    print()
    
    # Get sample judgment
    print("Step 1: Fetching sample judgment from database...")
    judgment = get_sample_judgment(limit=1)
    
    if not judgment:
        print("[ERROR] No judgments found in database")
        return
    
    print(f"[OK] Found judgment: {judgment['case_number']}")
    print(f"     Title: {judgment['title'][:80]}...")
    print(f"     Year: {judgment['year']}")
    print()
    
    # Initialize RAG system with Mistral API
    print("Step 2: Initializing RAG system with Mistral API...")
    print(f"     Model: mistral-medium-latest (or similar)")
    print(f"     Retrieval: Hybrid (BM25 + Vector with RRF)")
    print()
    
    try:
        system = IntegratedRAGWithSummarization(
            summarizer_model_type="mistral_api",
            summarizer_model_name="mistral-medium-latest",
            mistral_api_key=mistral_api_key,
            rag_top_k=5,
            similarity_threshold=0.5
        )
        print("[OK] RAG system initialized")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to initialize RAG system: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 1: Retrieval only
    print("="*80)
    print("TEST 1: RETRIEVAL ONLY")
    print("="*80)
    print()
    
    test_query = "What are the legal provisions for murder conviction?"
    
    print(f"Query: {test_query}")
    print()
    
    try:
        result = system.rag.process(
            query_or_text=test_query,
            judgment_id=judgment['id'],
            retrieve_legal_sections=True
        )
        
        print(f"[OK] Retrieval successful")
        print(f"     Entities found: {len(result.entities)}")
        print(f"     Chunks retrieved: {len(result.retrieved_chunks)}")
        print(f"     Dark zones found: {len(result.dark_zones)}")
        print(f"     Context length: {len(result.context)} characters")
        print()
        
        # Show sample retrieved chunks
        if result.retrieved_chunks:
            print("Sample retrieved chunks:")
            for i, chunk in enumerate(result.retrieved_chunks[:3], 1):
                chunk_text = chunk.get('content', '')[:150]
                print(f"  [{i}] {chunk_text}...")
            print()
    
    except Exception as e:
        print(f"[ERROR] Retrieval failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: Full pipeline (Retrieval + Summarization)
    print("="*80)
    print("TEST 2: RETRIEVAL + SUMMARIZATION")
    print("="*80)
    print()
    
    print(f"Processing judgment: {judgment['case_number']}")
    print(f"Text length: {len(judgment['full_text'])} characters")
    print()
    print("[INFO] Generating summary with Mistral API (this may take 30-60 seconds)...")
    print()
    
    try:
        full_result = system.process(
            query_or_text=judgment['full_text'],
            judgment_id=judgment['id'],
            generate_summary=True
        )
        
        print("[OK] Summary generation successful!")
        print()
        
        # Display results
        print("="*80)
        print("RETRIEVAL RESULTS")
        print("="*80)
        rag_result = full_result.get('rag_result', {})
        if rag_result:
            print(f"Entities found: {len(rag_result.entities)}")
            print(f"Chunks retrieved: {len(rag_result.retrieved_chunks)}")
            print(f"Dark zones found: {len(rag_result.dark_zones)}")
        print()
        
        print("="*80)
        print("SUMMARY (Mistral API)")
        print("="*80)
        
        summary_text = full_result.get('summary', '')
        if summary_text:
            try:
                # Try to print with UTF-8 encoding
                print(summary_text[:1000])
                if len(summary_text) > 1000:
                    print(f"\n... (truncated, full length: {len(summary_text)} characters)")
            except UnicodeEncodeError:
                # Fallback: encode to ASCII with replacements
                safe_text = summary_text[:1000].encode('ascii', 'replace').decode('ascii')
                print(safe_text)
                if len(summary_text) > 1000:
                    print(f"\n... (truncated, full length: {len(summary_text)} characters)")
            print()
        else:
            print("[WARNING] No summary generated")
            print()
        
        # Show summary metadata
        if 'summary_result' in full_result:
            summary_result = full_result['summary_result']
            print("Summary Structure:")
            print(f"  Case Summary: {len(summary_result.case_summary) if summary_result.case_summary else 0} chars")
            print(f"  Key Issues: {len(summary_result.key_issues) if summary_result.key_issues else 0} issues")
            print(f"  Legal Analysis: {len(summary_result.legal_analysis) if summary_result.legal_analysis else 0} chars")
            print(f"  Relevant Sections: {len(summary_result.relevant_sections) if summary_result.relevant_sections else 0} sections")
            print()
        
        print("="*80)
        print("TEST COMPLETE")
        print("="*80)
        print()
        print("[SUCCESS] Retrieval and summarization working correctly!")
        print(f"         Model: Mistral API ({system.summarizer.model_name})")
        print(f"         Retrieval: Hybrid (RRF)")
        print(f"         Summary length: {len(summary_text)} characters")
        print()
        
    except Exception as e:
        print(f"[ERROR] Summarization failed: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test retrieval and summarization with Mistral API")
    parser.add_argument(
        "--api-key",
        type=str,
        default="XwbyWBs6us68lMsQcO5ThTqNuxfweoqR",
        help="Mistral API key (default: provided key)"
    )
    
    args = parser.parse_args()
    
    test_retrieval_and_summarization(mistral_api_key=args.api_key)
