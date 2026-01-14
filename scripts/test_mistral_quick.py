"""
Quick test of Mistral summarization with Ollama
Simplified output to avoid encoding issues
"""

import sys
from pathlib import Path
import os
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from rag.integrated_rag_with_summarization import IntegratedRAGWithSummarization
from database.connection import get_db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def safe_print(text, max_len=500):
    """Print text safely handling Unicode"""
    try:
        # Try to print directly
        print(text[:max_len] + "..." if len(text) > max_len else text)
    except UnicodeEncodeError:
        # Fallback: encode to ASCII with replacements
        safe_text = text.encode('ascii', 'replace').decode('ascii')
        print(safe_text[:max_len] + "..." if len(safe_text) > max_len else safe_text)


def test_mistral():
    """Test Mistral summarization"""
    
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = 'postgres'
    
    print("="*80)
    print("TESTING MISTRAL SUMMARIZATION")
    print("="*80)
    
    # Initialize system with Mistral
    print("\nInitializing system with Mistral...")
    system = IntegratedRAGWithSummarization(
        rag_top_k=3,
        summarizer_model_type="ollama",
        summarizer_model_name="mistral"  # Will match "mistral:latest"
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
    
    print(f"Query: {query}")
    print("-"*80)
    print("\nProcessing (this may take 30-60 seconds for local LLM)...")
    
    try:
        # Process with summarization
        result = system.process(query, generate_summary=True)
        
        if result.get('summary'):
            summary = result['summary']
            print(f"\n[SUCCESS] Summary generated ({len(summary)} characters)")
            print("="*80)
            print("SUMMARY:")
            print("="*80)
            safe_print(summary, max_len=1000)
            
            # Show structured parts
            if result.get('summary_result'):
                sr = result['summary_result']
                print("\n" + "-"*80)
                print("STRUCTURED PARTS:")
                print("-"*80)
                
                if sr.case_summary:
                    print(f"\nCase Summary ({len(sr.case_summary)} chars):")
                    safe_print(sr.case_summary, max_len=300)
                
                if sr.key_issues:
                    print(f"\nKey Issues ({len(sr.key_issues)} found):")
                    for i, issue in enumerate(sr.key_issues[:5], 1):
                        safe_print(f"  {i}. {issue}", max_len=200)
                
                if sr.relevant_sections:
                    print(f"\nRelevant Sections ({len(sr.relevant_sections)} found):")
                    for section in sr.relevant_sections[:5]:
                        safe_print(f"  - {section}", max_len=100)
                
                if sr.legal_analysis:
                    print(f"\nLegal Analysis ({len(sr.legal_analysis)} chars):")
                    safe_print(sr.legal_analysis, max_len=400)
                
                if sr.judgment:
                    print(f"\nJudgment ({len(sr.judgment)} chars):")
                    safe_print(sr.judgment, max_len=300)
            
            # Compression ratio
            if result.get('compression_ratio'):
                print(f"\nCompression Ratio: {result['compression_ratio']:.2%}")
            
            # RAG metadata
            print("\n" + "-"*80)
            print("RAG METADATA:")
            print("-"*80)
            rag_meta = result.get('rag_result', {}).metadata if result.get('rag_result') else {}
            print(f"Entities Found: {rag_meta.get('entities_found', 0)}")
            print(f"Chunks Retrieved: {rag_meta.get('chunks_retrieved', 0)}")
            print(f"Dark Zones: {rag_meta.get('dark_zones_found', 0)}")
            print(f"Legal Sections Retrieved: {rag_meta.get('legal_sections_retrieved', False)}")
            
        else:
            print("\n[WARNING] Summary not generated")
            if result.get('summary_error'):
                print(f"Error: {result['summary_error']}")
            else:
                print("Check if Ollama is running and Mistral model is available")
    
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("Test Complete!")
    print("="*80)


if __name__ == "__main__":
    test_mistral()
