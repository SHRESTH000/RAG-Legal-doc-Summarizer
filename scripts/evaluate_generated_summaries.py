"""
Evaluate generated summaries with BERTScore
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

from evaluation.bertscore_evaluator import BERTScoreEvaluator, compare_with_baseline, ROUGEEvaluator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_generated_summaries(summaries_dir: str = "generated_summaries") -> List[Dict]:
    """Load generated summaries"""
    summaries_path = Path(summaries_dir) / "all_summaries.json"
    
    if not summaries_path.exists():
        logger.error(f"Summaries file not found: {summaries_path}")
        return []
    
    with open(summaries_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('summaries', [])


def load_reference_summaries(ref_file: str = "evaluation/reference_summaries.json") -> Dict[str, str]:
    """Load reference summaries"""
    ref_path = Path(ref_file)
    
    if not ref_path.exists():
        logger.warning(f"Reference summaries not found: {ref_path}")
        logger.info("Creating template file...")
        
        # Create template
        ref_path.parent.mkdir(exist_ok=True)
        template = {
            "note": "Add reference summaries here. Format: case_number -> summary text",
            "example": {
                "case_number_1": "Reference summary text here...",
                "case_number_2": "Another reference summary..."
            }
        }
        
        with open(ref_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Template created at: {ref_path}")
        logger.info("Please add reference summaries and re-run evaluation")
        return {}
    
    with open(ref_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Remove template keys
        return {k: v for k, v in data.items() if k not in ['note', 'example']}


def evaluate_summaries(
    generated_summaries: List[Dict],
    reference_summaries: Dict[str, str]
) -> Dict:
    """
    Evaluate generated summaries against references
    
    Args:
        generated_summaries: List of generated summary dicts
        reference_summaries: Dict mapping case_number to reference summary
        
    Returns:
        Evaluation results
    """
    # Match generated with references
    matched_pairs = []
    
    for gen_summary in generated_summaries:
        case_number = gen_summary.get('case_number', '')
        generated_text = gen_summary.get('summary', '')
        
        # Try to find reference
        ref_text = reference_summaries.get(case_number, '')
        
        if ref_text:
            matched_pairs.append({
                'case_number': case_number,
                'generated': generated_text,
                'reference': ref_text
            })
        else:
            logger.debug(f"No reference found for {case_number}")
    
    if not matched_pairs:
        logger.warning("No matched pairs found for evaluation")
        logger.info("You need to create reference summaries for evaluation")
        return None
    
    logger.info(f"Evaluating {len(matched_pairs)} summary pairs...")
    
    # Extract lists for evaluation
    generated_list = [p['generated'] for p in matched_pairs]
    reference_list = [p['reference'] for p in matched_pairs]
    
    # Evaluate with BERTScore
    try:
        evaluator = BERTScoreEvaluator()
        bertscore_results = evaluator.evaluate(generated_list, reference_list, verbose=True)
        
        # Compare with baseline
        comparison = compare_with_baseline(bertscore_results, baseline_score=0.89, metric='f1')
        
        # Evaluate with ROUGE (optional)
        rouge_results = None
        try:
            rouge_eval = ROUGEEvaluator()
            rouge_results = rouge_eval.evaluate(generated_list, reference_list)
        except Exception as e:
            logger.warning(f"ROUGE evaluation failed: {e}")
        
        return {
            'bertscore': bertscore_results,
            'baseline_comparison': comparison,
            'rouge': rouge_results,
            'num_evaluated': len(matched_pairs),
            'case_numbers': [p['case_number'] for p in matched_pairs]
        }
    
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_reference_template(generated_summaries: List[Dict], output_file: str = "evaluation/reference_summaries_template.json"):
    """Create a template file for reference summaries"""
    template = {
        "instructions": [
            "This file contains reference (ground truth) summaries for evaluation",
            "Add reference summaries for each case_number",
            "Reference summaries should be high-quality, expert-written summaries",
            "Format: case_number -> summary text"
        ],
        "reference_summaries": {}
    }
    
    # Add placeholders for each generated summary
    for gen_summary in generated_summaries:
        case_number = gen_summary.get('case_number', '')
        template['reference_summaries'][case_number] = f"[Add reference summary for {case_number} here]"
    
    output_path = Path(output_file)
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Reference template created: {output_path}")
    logger.info(f"Add reference summaries for {len(generated_summaries)} cases")


def main():
    """Main evaluation script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate generated summaries")
    parser.add_argument('--summaries-dir', type=str, default='generated_summaries',
                       help='Directory containing generated summaries')
    parser.add_argument('--reference-file', type=str, default='evaluation/reference_summaries.json',
                       help='File with reference summaries')
    parser.add_argument('--create-template', action='store_true',
                       help='Create template for reference summaries')
    
    args = parser.parse_args()
    
    print("="*80)
    print("SUMMARIZATION EVALUATION")
    print("="*80)
    
    # Load generated summaries
    print("\nLoading generated summaries...")
    generated = load_generated_summaries(args.summaries_dir)
    
    if not generated:
        print("[ERROR] No generated summaries found")
        return
    
    print(f"[OK] Found {len(generated)} generated summaries")
    
    # Create template if requested
    if args.create_template:
        print("\nCreating reference summary template...")
        create_reference_template(generated)
        print("[OK] Template created. Add reference summaries and re-run evaluation.")
        return
    
    # Load reference summaries
    print("\nLoading reference summaries...")
    references = load_reference_summaries(args.reference_file)
    
    if not references:
        print("\n[WARNING] No reference summaries found!")
        print("\nTo evaluate BERTScore, you need reference summaries.")
        print("Options:")
        print("1. Create template: python scripts/evaluate_generated_summaries.py --create-template")
        print("2. Add reference summaries to: evaluation/reference_summaries.json")
        print("3. Re-run evaluation")
        return
    
    print(f"[OK] Found {len(references)} reference summaries")
    
    # Evaluate
    print("\n" + "="*80)
    print("EVALUATING SUMMARIES")
    print("="*80)
    
    results = evaluate_summaries(generated, references)
    
    if results:
        print("\n" + "="*80)
        print("EVALUATION RESULTS")
        print("="*80)
        
        # BERTScore results
        bs = results['bertscore']
        print(f"\nBERTScore Results ({results['num_evaluated']} summaries):")
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
        
        if comp['is_better']:
            print(f"\n[SUCCESS] Our system achieves BETTER BERTScore than base paper!")
        elif comp['is_similar']:
            print(f"\n[SUCCESS] Our system achieves SIMILAR BERTScore to base paper!")
        else:
            print(f"\n[INFO] Our system's BERTScore is lower. This may be due to:")
            print("  - Different test set")
            print("  - Model differences (Mistral vs LLaMA 3.1-8B)")
            print("  - Reference summary quality")
            print("  - Need for prompt tuning")
        
        # ROUGE results (if available)
        if results.get('rouge'):
            rouge = results['rouge']
            print(f"\nROUGE Scores:")
            print(f"  ROUGE-1: {rouge['rouge1']['avg']:.4f}")
            print(f"  ROUGE-2: {rouge['rouge2']['avg']:.4f}")
            print(f"  ROUGE-L: {rouge['rougeL']['avg']:.4f}")
        
        # Save results
        output_file = "evaluation_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n[OK] Results saved to: {output_file}")
    else:
        print("\n[ERROR] Evaluation failed. Check logs above.")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
