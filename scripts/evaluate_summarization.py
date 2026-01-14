"""
Evaluate summarization quality using BERTScore
Compare with base paper's BERTScore 0.89
"""

import sys
from pathlib import Path
import os
import json
from typing import List, Dict

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from rag.integrated_rag_with_summarization import IntegratedRAGWithSummarization
from database.connection import get_db_manager
from evaluation.bertscore_evaluator import BERTScoreEvaluator, compare_with_baseline, ROUGEEvaluator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_reference_summaries(file_path: str) -> Dict[str, str]:
    """
    Load reference summaries from file
    
    Expected format: JSON with case_number -> summary mapping
    {
        "case_number_1": "reference summary text...",
        "case_number_2": "reference summary text...",
        ...
    }
    """
    if not os.path.exists(file_path):
        logger.warning(f"Reference summaries file not found: {file_path}")
        return {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def evaluate_summarization(
    test_cases: List[Dict],
    reference_summaries: Dict[str, str],
    use_llm: bool = False
) -> Dict:
    """
    Evaluate summarization on test cases
    
    Args:
        test_cases: List of test cases with 'query' and optional 'case_number'
        reference_summaries: Dict mapping case_number to reference summary
        use_llm: Whether to actually generate summaries (requires LLM)
        
    Returns:
        Evaluation results
    """
    if not use_llm:
        logger.warning("use_llm=False: Skipping actual summarization. "
                      "This will only test RAG retrieval.")
        return None
    
    # Initialize system
    logger.info("Initializing RAG + Summarization system...")
    system = IntegratedRAGWithSummarization(
        rag_top_k=3,
        summarizer_model_type="openai",  # Change as needed
        summarizer_model_name="gpt-4"
    )
    
    # Initialize BM25
    logger.info("Loading BM25 index...")
    db = get_db_manager()
    chunks = db.execute_query("SELECT id, content FROM judgment_chunks ORDER BY id LIMIT 50000")
    if chunks:
        documents = [row['content'] for row in chunks]
        chunk_ids = [row['id'] for row in chunks]
        system.initialize_bm25(documents, chunk_ids)
        logger.info(f"Loaded {len(documents)} chunks")
    
    # Generate summaries
    generated_summaries = []
    reference_list = []
    case_numbers = []
    
    logger.info(f"Processing {len(test_cases)} test cases...")
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case.get('query', '')
        case_number = test_case.get('case_number', f'test_{i}')
        
        logger.info(f"[{i}/{len(test_cases)}] Processing: {case_number}")
        
        try:
            # Generate summary
            result = system.process(query, generate_summary=True)
            
            if result.get('summary'):
                generated_summaries.append(result['summary'])
                case_numbers.append(case_number)
                
                # Get reference
                ref_summary = reference_summaries.get(case_number, '')
                if not ref_summary:
                    logger.warning(f"No reference summary for {case_number}")
                    ref_summary = ""  # Empty reference
                reference_list.append(ref_summary)
            else:
                logger.warning(f"Failed to generate summary for {case_number}")
        except Exception as e:
            logger.error(f"Error processing {case_number}: {e}")
            continue
    
    if not generated_summaries:
        logger.error("No summaries generated. Check LLM configuration.")
        return None
    
    logger.info(f"Generated {len(generated_summaries)} summaries. Evaluating...")
    
    # Evaluate with BERTScore
    try:
        evaluator = BERTScoreEvaluator()
        bertscore_results = evaluator.evaluate(generated_summaries, reference_list)
        
        # Compare with baseline
        comparison = compare_with_baseline(bertscore_results, baseline_score=0.89, metric='f1')
        
        # Evaluate with ROUGE (optional)
        rouge_results = None
        try:
            rouge_eval = ROUGEEvaluator()
            rouge_results = rouge_eval.evaluate(generated_summaries, reference_list)
        except Exception as e:
            logger.warning(f"ROUGE evaluation failed: {e}")
        
        return {
            'bertscore': bertscore_results,
            'baseline_comparison': comparison,
            'rouge': rouge_results,
            'num_evaluated': len(generated_summaries),
            'case_numbers': case_numbers
        }
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main evaluation script"""
    
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = 'postgres'
    
    print("="*80)
    print("SUMMARIZATION EVALUATION")
    print("="*80)
    
    # Test cases (can be loaded from file)
    test_cases = [
        {
            'query': 'Summarize the judgment on IPC Section 302 murder conviction',
            'case_number': 'test_1'
        },
        # Add more test cases
    ]
    
    # Load reference summaries
    reference_file = "evaluation/reference_summaries.json"
    reference_summaries = load_reference_summaries(reference_file)
    
    if not reference_summaries:
        print("\n[WARNING] No reference summaries found.")
        print("To evaluate BERTScore, you need:")
        print("1. Generate summaries using the integrated system")
        print("2. Create reference_summaries.json with case_number -> summary mapping")
        print("3. Re-run this script")
        print("\nExample reference_summaries.json:")
        print('''{
    "test_1": "Reference summary text here...",
    "test_2": "Another reference summary..."
}''')
        return
    
    # Check if LLM is available
    use_llm = os.getenv('OPENAI_API_KEY') is not None
    
    if not use_llm:
        print("\n[WARNING] OPENAI_API_KEY not set.")
        print("Set it to evaluate summarization:")
        print("  export OPENAI_API_KEY='your-key'")
        print("\nOr test RAG only with use_llm=False")
    
    # Run evaluation
    results = evaluate_summarization(test_cases, reference_summaries, use_llm=use_llm)
    
    if results:
        print("\n" + "="*80)
        print("EVALUATION RESULTS")
        print("="*80)
        
        # BERTScore results
        bs = results['bertscore']
        print(f"\nBERTScore Results:")
        print(f"  Average Precision: {bs['avg_precision']:.4f}")
        print(f"  Average Recall:    {bs['avg_recall']:.4f}")
        print(f"  Average F1:        {bs['avg_f1']:.4f}")
        
        # Comparison with baseline
        comp = results['baseline_comparison']
        print(f"\nComparison with Base Paper (BERTScore 0.89):")
        print(f"  Base Paper:  {comp['baseline_score']:.4f}")
        print(f"  Our System:  {comp['our_score']:.4f}")
        print(f"  Difference:  {comp['difference']:+.4f} ({comp['percent_difference']:+.2f}%)")
        print(f"  Status:      {comp['comparison'].upper()}")
        
        # ROUGE results (if available)
        if results.get('rouge'):
            rouge = results['rouge']
            print(f"\nROUGE Scores:")
            print(f"  ROUGE-1: {rouge['rouge1']['avg']:.4f}")
            print(f"  ROUGE-2: {rouge['rouge2']['avg']:.4f}")
            print(f"  ROUGE-L: {rouge['rougeL']['avg']:.4f}")
        
        # Save results
        output_file = "evaluation_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n[OK] Results saved to: {output_file}")
    else:
        print("\n[ERROR] Evaluation failed. Check logs above.")


if __name__ == "__main__":
    main()
