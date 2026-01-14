"""
Generate summaries for multiple judgments using Mistral/Ollama
Save summaries for BERTScore evaluation
"""

import sys
from pathlib import Path
import os
import json
from typing import List, Dict
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from rag.integrated_rag_with_summarization import IntegratedRAGWithSummarization
from database.connection import get_db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_judgments_from_db(limit: int = 5) -> List[Dict]:
    """Get judgments from database"""
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
    
    judgments = []
    for row in results:
        judgments.append({
            'id': row['id'],
            'case_number': row['case_number'],
            'title': row.get('title', ''),
            'date': str(row['judgment_date']) if row['judgment_date'] else None,
            'court': row.get('court', ''),
            'year': row.get('year'),
            'full_text': row.get('full_text', '')[:5000] if row.get('full_text') else ''  # Limit text length
        })
    
    return judgments


def generate_summaries_for_judgments(
    judgments: List[Dict],
    model_name: str = "mistral",
    output_dir: str = "generated_summaries"
) -> List[Dict]:
    """
    Generate summaries for multiple judgments
    
    Args:
        judgments: List of judgment dictionaries
        model_name: Ollama model name
        output_dir: Directory to save summaries
        
    Returns:
        List of summary results
    """
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = 'postgres'
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print("="*80)
    print("GENERATING JUDGMENT SUMMARIES")
    print("="*80)
    print(f"\nModel: {model_name}")
    print(f"Judgments to process: {len(judgments)}")
    print(f"Output directory: {output_dir}\n")
    
    # Initialize system
    print("Initializing RAG + Summarization system...")
    system = IntegratedRAGWithSummarization(
        rag_top_k=5,  # Retrieve more chunks for full judgment summarization
        summarizer_model_type="ollama",
        summarizer_model_name=model_name
    )
    
    # Initialize BM25
    print("Loading BM25 index...")
    db = get_db_manager()
    chunks = db.execute_query("SELECT id, content FROM judgment_chunks ORDER BY id LIMIT 50000")
    if chunks:
        documents = [row['content'] for row in chunks]
        chunk_ids = [row['id'] for row in chunks]
        system.initialize_bm25(documents, chunk_ids)
        print(f"[OK] Loaded {len(documents)} chunks\n")
    
    # Process each judgment
    results = []
    
    for i, judgment in enumerate(judgments, 1):
        case_number = judgment.get('case_number', f'judgment_{judgment["id"]}')
        print("-"*80)
        print(f"[{i}/{len(judgments)}] Processing: {case_number}")
        if judgment.get('title'):
            print(f"Title: {judgment['title'][:80]}...")
        if judgment.get('year'):
            print(f"Year: {judgment['year']}")
        print()
        
        try:
            # Create query for summarization
            # Use judgment text or create a query based on metadata
            if judgment.get('full_text') and len(judgment['full_text']) > 100:
                query_text = judgment['full_text']
            else:
                # Fallback: create query from metadata
                query_text = f"Summarize the judgment: {judgment.get('title', '')} Case: {case_number}"
            
            # Process with summarization
            print("  Retrieving context and generating summary...")
            result = system.process(query_text, judgment_id=judgment['id'], generate_summary=True)
            
            if result.get('summary'):
                summary_data = {
                    'case_number': case_number,
                    'judgment_id': judgment['id'],
                    'title': judgment.get('title', ''),
                    'date': judgment.get('date'),
                    'court': judgment.get('court', ''),
                    'year': judgment.get('year'),
                    'summary': result['summary'],
                    'summary_result': {
                        'case_summary': result['summary_result'].case_summary if result.get('summary_result') else '',
                        'key_issues': result['summary_result'].key_issues if result.get('summary_result') else [],
                        'legal_analysis': result['summary_result'].legal_analysis if result.get('summary_result') else '',
                        'relevant_sections': result['summary_result'].relevant_sections if result.get('summary_result') else [],
                        'judgment': result['summary_result'].judgment if result.get('summary_result') else '',
                    },
                    'rag_metadata': {
                        'entities_found': result['rag_result'].metadata.get('entities_found', 0) if result.get('rag_result') else 0,
                        'chunks_retrieved': result['rag_result'].metadata.get('chunks_retrieved', 0) if result.get('rag_result') else 0,
                        'dark_zones_found': result['rag_result'].metadata.get('dark_zones_found', 0) if result.get('rag_result') else 0,
                        'legal_sections_retrieved': result['rag_result'].metadata.get('legal_sections_retrieved', False) if result.get('rag_result') else False,
                    },
                    'compression_ratio': result.get('compression_ratio'),
                    'generated_at': datetime.now().isoformat(),
                    'model': model_name
                }
                
                results.append(summary_data)
                
                # Save individual summary
                summary_file = output_path / f"{case_number.replace('/', '_')}_summary.json"
                with open(summary_file, 'w', encoding='utf-8') as f:
                    json.dump(summary_data, f, indent=2, ensure_ascii=False)
                
                print(f"  [OK] Summary generated ({len(result['summary'])} chars)")
                print(f"  [OK] Saved to: {summary_file}")
                
                # Show preview
                if result.get('summary_result'):
                    sr = result['summary_result']
                    if sr.case_summary:
                        print(f"  Case Summary: {sr.case_summary[:100]}...")
                    if sr.key_issues:
                        print(f"  Key Issues: {len(sr.key_issues)} found")
                    if sr.relevant_sections:
                        print(f"  Sections: {', '.join(sr.relevant_sections[:3])}")
            else:
                print(f"  [WARNING] Summary not generated")
                if result.get('summary_error'):
                    print(f"  Error: {result['summary_error']}")
        
        except Exception as e:
            print(f"  [ERROR] Failed: {e}")
            logger.error(f"Error processing {case_number}: {e}", exc_info=True)
            continue
        
        print()
    
    # Save combined results
    combined_file = output_path / "all_summaries.json"
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_judgments': len(judgments),
            'successful': len(results),
            'model': model_name,
            'generated_at': datetime.now().isoformat(),
            'summaries': results
        }, f, indent=2, ensure_ascii=False)
    
    print("="*80)
    print("SUMMARY GENERATION COMPLETE")
    print("="*80)
    print(f"\nTotal Judgments: {len(judgments)}")
    print(f"Successful: {len(results)}")
    print(f"Failed: {len(judgments) - len(results)}")
    print(f"\nSummaries saved to: {output_dir}/")
    print(f"Combined file: {combined_file}")
    
    return results


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate summaries for judgments")
    parser.add_argument('--count', '-c', type=int, default=5, help='Number of judgments to process')
    parser.add_argument('--model', '-m', type=str, default='mistral', help='Ollama model name')
    parser.add_argument('--output', '-o', type=str, default='generated_summaries', help='Output directory')
    
    args = parser.parse_args()
    
    # Get judgments
    print("Loading judgments from database...")
    judgments = get_judgments_from_db(limit=args.count)
    
    if not judgments:
        print("[ERROR] No judgments found in database")
        return
    
    print(f"[OK] Found {len(judgments)} judgments\n")
    
    # Generate summaries
    results = generate_summaries_for_judgments(
        judgments,
        model_name=args.model,
        output_dir=args.output
    )
    
    print(f"\n[OK] Generated {len(results)} summaries")
    print(f"Ready for BERTScore evaluation!")


if __name__ == "__main__":
    main()
