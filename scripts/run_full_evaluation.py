"""
Complete evaluation: Generate summaries and evaluate with BERTScore
Compare with base paper's 0.89
"""

import sys
from pathlib import Path
import os
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from database.connection import get_db_manager
from rag.integrated_rag_with_summarization import IntegratedRAGWithSummarization
from evaluation.bertscore_evaluator import BERTScoreEvaluator, compare_with_baseline, ROUGEEvaluator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_reference_summaries(ref_file: str = "evaluation/reference_summaries.json") -> dict:
    """Load reference summaries"""
    ref_path = Path(ref_file)
    
    if not ref_path.exists():
        logger.error(f"Reference summaries not found: {ref_path}")
        return {}
    
    with open(ref_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
        # Extract summaries from nested structure
        ref_summaries = {}
        ref_data = data.get('reference_summaries', {})
        
        for case_num, content in ref_data.items():
            if isinstance(content, dict):
                # If it's a dict with 'summary' key
                summary_text = content.get('summary', '')
                if summary_text:
                    ref_summaries[case_num] = summary_text
                else:
                    # If no 'summary' key, use the whole dict as string (shouldn't happen)
                    ref_summaries[case_num] = str(content)
            elif isinstance(content, str):
                # If it's directly a string
                ref_summaries[case_num] = content
            else:
                # Fallback
                ref_summaries[case_num] = str(content)
        
        return ref_summaries


def run_complete_evaluation():
    """Run complete evaluation pipeline"""
    
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = 'postgres'
    
    print("="*80)
    print("COMPLETE EVALUATION: SUMMARIZATION + BERTScore")
    print("="*80)
    
    # Step 1: Load generated summaries
    print("\nStep 1: Loading generated summaries...")
    summaries_file = Path("generated_summaries/all_summaries.json")
    
    if not summaries_file.exists():
        print("[ERROR] Generated summaries not found")
        print("Generate first: python scripts/generate_judgment_summaries.py")
        return None
    
    with open(summaries_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        generated_summaries = data.get('summaries', [])
    
    print(f"[OK] Loaded {len(generated_summaries)} generated summaries")
    
    # Step 2: Load reference summaries
    print("\nStep 2: Loading reference summaries...")
    reference_summaries = load_reference_summaries()
    
    if not reference_summaries:
        print("[ERROR] No reference summaries found")
        print("Add references to: evaluation/reference_summaries.json")
        return None
    
    print(f"[OK] Loaded {len(reference_summaries)} reference summaries")
    
    # Step 3: Match and prepare for evaluation
    print("\nStep 3: Matching summaries for evaluation...")
    matched_pairs = []
    
    for gen_summary in generated_summaries:
        case_number = gen_summary.get('case_number', '')
        generated_text = gen_summary.get('summary', '')
        ref_text = reference_summaries.get(case_number, '')
        
        if ref_text and generated_text:
            matched_pairs.append({
                'case_number': case_number,
                'generated': generated_text,
                'reference': ref_text
            })
            print(f"  [OK] Matched: {case_number}")
        else:
            if not ref_text:
                print(f"  [SKIP] No reference for: {case_number}")
            if not generated_text:
                print(f"  [SKIP] No generated summary for: {case_number}")
    
    if not matched_pairs:
        print("[ERROR] No matched pairs found for evaluation")
        return None
    
    print(f"\n[OK] {len(matched_pairs)} pairs matched for evaluation")
    
    # Step 4: Evaluate with BERTScore
    print("\n" + "="*80)
    print("EVALUATING WITH BERTScore")
    print("="*80)
    
    generated_list = [p['generated'] for p in matched_pairs]
    reference_list = [p['reference'] for p in matched_pairs]
    
    try:
        print("\nCalculating BERTScore (this may take a few minutes)...")
        evaluator = BERTScoreEvaluator()
        bertscore_results = evaluator.evaluate(
            generated_list,
            reference_list,
            verbose=True
        )
        
        # Step 5: Compare with baseline
        print("\nComparing with base paper...")
        comparison = compare_with_baseline(
            bertscore_results,
            baseline_score=0.89,
            metric='f1'
        )
        
        # Step 6: Evaluate with ROUGE (optional)
        rouge_results = None
        try:
            print("\nCalculating ROUGE scores...")
            rouge_eval = ROUGEEvaluator()
            rouge_results = rouge_eval.evaluate(generated_list, reference_list)
        except Exception as e:
            logger.warning(f"ROUGE evaluation failed: {e}")
        
        # Step 7: Display results
        print("\n" + "="*80)
        print("EVALUATION RESULTS")
        print("="*80)
        
        print(f"\nBERTScore Results ({len(matched_pairs)} summaries):")
        print("-"*80)
        print(f"  Average Precision: {bertscore_results['avg_precision']:.4f}")
        print(f"  Average Recall:    {bertscore_results['avg_recall']:.4f}")
        print(f"  Average F1:        {bertscore_results['avg_f1']:.4f}")
        
        print(f"\n{'='*80}")
        print("COMPARISON WITH BASE PAPER")
        print("="*80)
        print(f"\nBase Paper BERTScore: {comparison['baseline_score']:.4f}")
        print(f"Our System BERTScore: {comparison['our_score']:.4f}")
        print(f"Difference:          {comparison['difference']:+.4f} ({comparison['percent_difference']:+.2f}%)")
        print(f"Status:              {comparison['comparison'].upper()}")
        
        if comparison['is_better']:
            print(f"\n[SUCCESS] Our system achieves BETTER BERTScore than base paper!")
            print(f"          Improvement: {comparison['percent_difference']:+.2f}%")
        elif comparison['is_similar']:
            print(f"\n[SUCCESS] Our system achieves SIMILAR BERTScore to base paper!")
            print(f"          Difference: {comparison['difference']:+.4f} (< 0.01)")
        else:
            print(f"\n[INFO] Our system's BERTScore is {comparison['percent_difference']:.2f}% different from base paper.")
            print("       Possible reasons:")
            print("       - Different test set or reference summaries")
            print("       - Model differences (Mistral vs LLaMA 3.1-8B)")
            print("       - Need for prompt tuning or model fine-tuning")
        
        # ROUGE results
        if rouge_results:
            print(f"\n{'='*80}")
            print("ROUGE SCORES (Additional Metrics)")
            print("="*80)
            print(f"  ROUGE-1: {rouge_results['rouge1']['avg']:.4f}")
            print(f"  ROUGE-2: {rouge_results['rouge2']['avg']:.4f}")
            print(f"  ROUGE-L: {rouge_results['rougeL']['avg']:.4f}")
        
        # Individual scores
        print(f"\n{'='*80}")
        print("INDIVIDUAL SUMMARY SCORES")
        print("="*80)
        for i, pair in enumerate(matched_pairs, 1):
            precision = bertscore_results['precision'][i-1]
            recall = bertscore_results['recall'][i-1]
            f1 = bertscore_results['f1'][i-1]
            
            print(f"\n[{i}] {pair['case_number']}:")
            print(f"    Precision: {precision:.4f}")
            print(f"    Recall:    {recall:.4f}")
            print(f"    F1:        {f1:.4f}")
        
        # Save results
        results_data = {
            'bertscore': {
                'avg_precision': float(bertscore_results['avg_precision']),
                'avg_recall': float(bertscore_results['avg_recall']),
                'avg_f1': float(bertscore_results['avg_f1']),
                'individual_scores': [
                    {
                        'case_number': pair['case_number'],
                        'precision': float(bertscore_results['precision'][i]),
                        'recall': float(bertscore_results['recall'][i]),
                        'f1': float(bertscore_results['f1'][i])
                    }
                    for i, pair in enumerate(matched_pairs)
                ]
            },
            'baseline_comparison': {
                'baseline_score': float(comparison['baseline_score']),
                'our_score': float(comparison['our_score']),
                'difference': float(comparison['mean_difference']),
                'percent_difference': float(comparison['percent_improvement']),
                'is_better': bool(comparison['is_better']),
                'is_similar': bool(comparison['is_similar']),
                'comparison': comparison['comparison']
            },
            'rouge': {
                'rouge1': float(rouge_results['rouge1']['avg']) if rouge_results else None,
                'rouge2': float(rouge_results['rouge2']['avg']) if rouge_results else None,
                'rougeL': float(rouge_results['rougeL']['avg']) if rouge_results else None
            } if rouge_results else None,
            'num_evaluated': len(matched_pairs),
            'cases': [p['case_number'] for p in matched_pairs]
        }
        
        output_file = "evaluation_results_complete.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*80}")
        print(f"[OK] Complete results saved to: {output_file}")
        print("="*80)
        
        return results_data
    
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    results = run_complete_evaluation()
    
    if results:
        print("\n[SUCCESS] Evaluation complete!")
    else:
        print("\n[ERROR] Evaluation failed. Check logs above.")
