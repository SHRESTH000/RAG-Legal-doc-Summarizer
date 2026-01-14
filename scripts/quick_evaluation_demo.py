"""
Quick evaluation demo using generated summaries as references
This demonstrates the evaluation framework (not a real comparison)
"""

import sys
from pathlib import Path
import os
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from evaluation.bertscore_evaluator import BERTScoreEvaluator, compare_with_baseline

def demo_evaluation():
    """Demo evaluation framework"""
    
    print("="*80)
    print("EVALUATION FRAMEWORK DEMONSTRATION")
    print("="*80)
    print("\nNote: This uses generated summaries as references for demo purposes.")
    print("      For real evaluation, use expert-written reference summaries.\n")
    
    # Load generated summaries
    summaries_file = Path("generated_summaries/all_summaries.json")
    
    if not summaries_file.exists():
        print(f"[ERROR] Generated summaries not found")
        print("Generate summaries first: python scripts/generate_judgment_summaries.py")
        return
    
    with open(summaries_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        summaries = data.get('summaries', [])
    
    if len(summaries) < 2:
        print("[ERROR] Need at least 2 summaries for evaluation")
        return
    
    print(f"Loaded {len(summaries)} generated summaries\n")
    
    # For demo: use summaries as both generated and reference
    # (This shows the framework works, but isn't a real evaluation)
    print("[DEMO] Using generated summaries as both generated and reference")
    print("       (This demonstrates the framework - not a real comparison)\n")
    
    generated_texts = [s.get('summary', '') for s in summaries]
    reference_texts = generated_texts.copy()  # Same for demo
    
    # Evaluate
    try:
        print("Evaluating with BERTScore...")
        evaluator = BERTScoreEvaluator()
        results = evaluator.evaluate(generated_texts, reference_texts, verbose=False)
        
        print("\n" + "="*80)
        print("DEMO RESULTS")
        print("="*80)
        print(f"\nBERTScore (using same summaries as reference - perfect match expected):")
        print(f"  Average Precision: {results['avg_precision']:.4f}")
        print(f"  Average Recall:    {results['avg_recall']:.4f}")
        print(f"  Average F1:        {results['avg_f1']:.4f}")
        
        # Compare with baseline
        comparison = compare_with_baseline(results, baseline_score=0.89, metric='f1')
        
        print(f"\nComparison with Base Paper (BERTScore 0.89):")
        print(f"  Base Paper:  {comparison['baseline_score']:.4f}")
        print(f"  Our Score:   {comparison['our_score']:.4f}")
        print(f"  Difference:  {comparison['difference']:+.4f}")
        print(f"  Status:      {comparison['comparison'].upper()}")
        
        print("\n" + "="*80)
        print("FRAMEWORK STATUS")
        print("="*80)
        print("\n[OK] BERTScore evaluation framework is working!")
        print("\nTo do real evaluation:")
        print("1. Create expert-written reference summaries")
        print("2. Save to: evaluation/reference_summaries.json")
        print("3. Run: python scripts/evaluate_generated_summaries.py")
        print("\nThe framework is ready - you just need reference summaries!")
        
    except Exception as e:
        print(f"\n[ERROR] Evaluation failed: {e}")
        print("\nMake sure bert-score is installed:")
        print("  pip install bert-score")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo_evaluation()
