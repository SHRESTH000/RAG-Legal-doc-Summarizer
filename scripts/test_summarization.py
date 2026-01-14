"""
Test script for summarization module
Tests integration with RAG system
"""

import sys
from pathlib import Path
import os

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from rag.integrated_rag_with_summarization import IntegratedRAGWithSummarization
from database.connection import get_db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_summarization():
    """Test summarization with sample query"""
    
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = 'postgres'
    
    print("="*80)
    print("TESTING INTEGRATED RAG + SUMMARIZATION")
    print("="*80)
    
    # Initialize system
    # Note: For testing without LLM, set generate_summary=False
    print("\nInitializing system...")
    system = IntegratedRAGWithSummarization(
        rag_top_k=3,
        summarizer_model_type="openai",  # Change to "huggingface" or "llama" if needed
        summarizer_model_name="gpt-4"
    )
    
    # Initialize BM25
    print("Loading BM25 index...")
    db = get_db_manager()
    chunks = db.execute_query("SELECT id, content FROM judgment_chunks ORDER BY id LIMIT 10000")
    if chunks:
        documents = [row['content'] for row in chunks]
        chunk_ids = [row['id'] for row in chunks]
        system.initialize_bm25(documents, chunk_ids)
        print(f"[OK] Loaded {len(documents)} chunks\n")
    
    # Test query
    query = "What are the legal provisions for murder conviction under IPC Section 302? Summarize relevant case law."
    
    print(f"Query: {query}\n")
    print("-"*80)
    
    try:
        # Process with summarization disabled first (to test RAG)
        print("\n[TEST 1] RAG Retrieval Only:")
        result = system.process(query, generate_summary=False)
        
        print(f"Entities Found: {len(result['rag_result'].entities)}")
        print(f"Chunks Retrieved: {len(result['rag_result'].retrieved_chunks)}")
        print(f"Context Length: {len(result['rag_result'].context)} chars")
        
        # Test with summarization (if LLM available)
        print("\n[TEST 2] Full Pipeline (RAG + Summarization):")
        print("Note: Requires LLM API key configured")
        
        # Check if we can generate summary
        try:
            result_with_summary = system.process(query, generate_summary=True)
            
            if result_with_summary.get('summary'):
                print("\n[OK] Summary generated:")
                print("-"*80)
                print(result_with_summary['summary'][:500] + "...")
                
                if result_with_summary.get('summary_result'):
                    sr = result_with_summary['summary_result']
                    print(f"\nCase Summary: {sr.case_summary[:200]}...")
                    print(f"Key Issues: {len(sr.key_issues)} issues found")
                    print(f"Relevant Sections: {len(sr.relevant_sections)} sections")
            else:
                print("\n[WARNING] Summary not generated (check LLM configuration)")
        except Exception as e:
            print(f"\n[ERROR] Summarization failed: {e}")
            print("This is expected if LLM is not configured.")
            print("\nTo use summarization:")
            print("1. For OpenAI: Set OPENAI_API_KEY environment variable")
            print("2. For HuggingFace: Install transformers and specify model name")
            print("3. For LLaMA: Install llama-cpp-python and provide model path")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_summarization()
