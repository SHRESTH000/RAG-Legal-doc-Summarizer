"""
Test summarization with Ollama local models
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


def list_ollama_models():
    """List available Ollama models"""
    try:
        import requests
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            return [m.get('name') for m in models]
        else:
            print(f"[ERROR] Failed to connect to Ollama: {response.status_code}")
            return []
    except Exception as e:
        print(f"[ERROR] Could not connect to Ollama: {e}")
        print("Make sure Ollama is running: ollama serve")
        return []


def test_ollama_summarization(model_name: str = None):
    """Test summarization with Ollama"""
    
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = 'postgres'
    
    print("="*80)
    print("TESTING OLLAMA SUMMARIZATION")
    print("="*80)
    
    # Check Ollama connection
    print("\nChecking Ollama connection...")
    available_models = list_ollama_models()
    
    if not available_models:
        print("\n[ERROR] No Ollama models found or Ollama not running.")
        print("\nTo start Ollama:")
        print("  1. Make sure Ollama is installed")
        print("  2. Run: ollama serve")
        print("  3. Pull a model: ollama pull mistral")
        return
    
    print(f"[OK] Found {len(available_models)} models:")
    for model in available_models:
        print(f"  - {model}")
    
    # Select model
    if not model_name:
        model_name = available_models[0]
        print(f"\nUsing model: {model_name}")
    elif model_name not in available_models:
        print(f"\n[WARNING] Model '{model_name}' not found. Using: {available_models[0]}")
        model_name = available_models[0]
    else:
        print(f"\nUsing specified model: {model_name}")
    
    # Initialize system
    print("\nInitializing RAG + Summarization system...")
    system = IntegratedRAGWithSummarization(
        rag_top_k=3,
        summarizer_model_type="ollama",
        summarizer_model_name=model_name
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
    test_queries = [
        "What are the legal provisions for murder conviction under IPC Section 302?",
        "Explain bail procedure under CrPC Section 439",
        "What is the difference between murder and culpable homicide?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print("-"*80)
        print(f"Test Query {i}: {query}")
        print("-"*80)
        
        try:
            # Process with summarization
            result = system.process(query, generate_summary=True)
            
            if result.get('summary'):
                print("\n[OK] Summary generated:")
                print("-"*80)
                summary = result['summary']
                
                # Show summary preview
                print(summary[:500] + "..." if len(summary) > 500 else summary)
                
                # Show structured parts if available
                if result.get('summary_result'):
                    sr = result['summary_result']
                    if sr.case_summary:
                        print(f"\nCase Summary: {sr.case_summary[:200]}...")
                    if sr.key_issues:
                        print(f"\nKey Issues ({len(sr.key_issues)}):")
                        for issue in sr.key_issues[:3]:
                            print(f"  - {issue}")
                    if sr.relevant_sections:
                        print(f"\nRelevant Sections: {sr.relevant_sections[:3]}")
                
                print(f"\nSummary length: {len(summary)} characters")
                
                if result.get('compression_ratio'):
                    print(f"Compression ratio: {result['compression_ratio']:.2%}")
            else:
                print("\n[WARNING] Summary not generated")
                if result.get('summary_error'):
                    print(f"Error: {result['summary_error']}")
            
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("="*80)
    print("Testing complete!")
    print("="*80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Ollama summarization")
    parser.add_argument('--model', '-m', type=str, help='Ollama model name (e.g., mistral, llama2)')
    parser.add_argument('--url', type=str, help='Ollama base URL (default: http://localhost:11434)')
    
    args = parser.parse_args()
    
    if args.url:
        os.environ['OLLAMA_BASE_URL'] = args.url
    
    test_ollama_summarization(model_name=args.model)
