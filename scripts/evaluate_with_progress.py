"""
Evaluate summaries with BERTScore - with progress tracking
"""

import sys
from pathlib import Path
import os
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from evaluation.bertscore_evaluator import BERTScoreEvaluator, compare_with_baseline, ROUGEEvaluator

def load_data():
    """Load generated and reference summaries"""
    # Load generated
    with open("generated_summaries/all_summaries.json", 'r', encoding='utf-8') as f:
        gen_data = json.load(f)
        generated = gen_data.get('summaries', [])
    
    # Load references
    with open("evaluation/reference_summaries.json", 'r', encoding='utf-8') as f:
        ref_data = json.load(f)
        ref_summaries = ref_data.get('reference_summaries', {})
    
    # Match pairs
    pairs = []
    for gen in generated:
        case_num = gen.get('case_number', '')
        gen_text = gen.get('summary', '')
        ref_text = ref_summaries.get(case_num, {})
        
        if isinstance(ref_text, dict):
            ref_text = ref_text.get('summary', '')
        
        if gen_text and ref_text:
            pairs.append({
                'case': case_num,
                'generated': gen_text,
                'reference': ref_text
            })
    
    return pairs

def main():
    print("="*80)
    print("BERTScore Evaluation with Base Paper Comparison")
    print("="*80)
    
    # Load data
    print("\nLoading summaries...")
    pairs = load_data()
    print(f"[OK] {len(pairs)} pairs loaded")
    
    if not pairs:
        print("[ERROR] No matched pairs")
        return
    
    # Prepare lists
    generated = [p['generated'] for p in pairs]
    references = [p['reference'] for p in pairs]
    
    # Evaluate
    print("\nEvaluating with BERTScore...")
    print("(This may take a few minutes - BERTScore downloads models on first use)")
    
    try:
        evaluator = BERTScoreEvaluator()
        results = evaluator.evaluate(generated, references, verbose=True)
        
        # Compare
        comparison = compare_with_baseline(results, baseline_score=0.89, metric='f1')
        
        # Display
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        print(f"\nBERTScore:")
        print(f"  Precision: {results['avg_precision']:.4f}")
        print(f"  Recall:    {results['avg_recall']:.4f}")
        print(f"  F1:        {results['avg_f1']:.4f}")
        
        print(f"\nComparison with Base Paper (0.89):")
        print(f"  Base Paper:  {comparison['baseline_score']:.4f}")
        print(f"  Our Score:   {comparison['our_score']:.4f}")
        print(f"  Difference:  {comparison['difference']:+.4f} ({comparison['percent_difference']:+.2f}%)")
        print(f"  Status:      {comparison['comparison'].upper()}")
        
        # Save
        output = {
            'bertscore': {
                'precision': float(results['avg_precision']),
                'recall': float(results['avg_recall']),
                'f1': float(results['avg_f1'])
            },
            'comparison': {
                'baseline': 0.89,
                'our_score': float(comparison['our_score']),
                'difference': float(comparison['difference']),
                'percent_diff': float(comparison['percent_difference']),
                'status': comparison['comparison']
            }
        }
        
        with open("evaluation_results.json", 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n[OK] Results saved to evaluation_results.json")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
