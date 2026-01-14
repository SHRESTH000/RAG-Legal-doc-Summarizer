"""
Create reference summary template from generated summaries
Helps set up for BERTScore evaluation
"""

import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))


def create_template():
    """Create reference summary template"""
    
    # Load generated summaries
    summaries_file = Path("generated_summaries/all_summaries.json")
    
    if not summaries_file.exists():
        print(f"[ERROR] Generated summaries not found: {summaries_file}")
        print("Generate summaries first: python scripts/generate_judgment_summaries.py")
        return
    
    with open(summaries_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        summaries = data.get('summaries', [])
    
    if not summaries:
        print("[ERROR] No summaries found in file")
        return
    
    # Create template
    template = {
        "instructions": [
            "This file contains reference (ground truth) summaries for BERTScore evaluation",
            "Replace the placeholder text with high-quality reference summaries",
            "Reference summaries should be:",
            "  - Expert-written or verified",
            "  - Comprehensive and accurate",
            "  - Similar length to generated summaries",
            "  - Covering key facts, issues, analysis, and judgment"
        ],
        "note": "You can use the generated summaries as a starting point, but improve them",
        "reference_summaries": {}
    }
    
    # Add placeholders with generated summaries as examples
    for summary in summaries:
        case_number = summary.get('case_number', '')
        generated = summary.get('summary', '')
        
        template['reference_summaries'][case_number] = {
            "placeholder": f"[Add expert-written reference summary for {case_number} here]",
            "generated_summary_example": generated[:500] + "..." if len(generated) > 500 else generated,
            "metadata": {
                "title": summary.get('title', ''),
                "year": summary.get('year'),
                "court": summary.get('court', '')
            }
        }
    
    # Save template
    output_file = Path("evaluation/reference_summaries.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    print("="*80)
    print("REFERENCE SUMMARY TEMPLATE CREATED")
    print("="*80)
    print(f"\nTemplate saved to: {output_file}")
    print(f"Cases to add references for: {len(summaries)}")
    print("\nNext steps:")
    print("1. Open the template file")
    print("2. Replace placeholders with expert-written reference summaries")
    print("3. Run evaluation: python scripts/evaluate_generated_summaries.py")
    print("\nNote: For now, you can use generated summaries as references")
    print("      to test the evaluation framework, but for real comparison")
    print("      you need expert-written references.")


if __name__ == "__main__":
    create_template()
