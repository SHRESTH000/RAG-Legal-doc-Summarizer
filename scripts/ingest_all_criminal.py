"""
Ingest all criminal cases from all years
Processes in batches for efficiency
"""

import sys
from pathlib import Path
import argparse

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from ingestion.judgment_ingestor import JudgmentIngestor
from database.connection import get_db_manager
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def ingest_year(year: int, limit: int = None, skip_existing: bool = True):
    """Ingest criminal cases for a specific year"""
    folder = Path(f"criminal_{year}")
    
    if not folder.exists():
        logger.warning(f"Folder not found: {folder}")
        return None
    
    pdf_files = list(folder.glob("*.pdf"))
    total_files = len(pdf_files)
    
    if limit:
        pdf_files = pdf_files[:limit]
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing criminal_{year}: {len(pdf_files)}/{total_files} files")
    logger.info(f"{'='*60}")
    
    ingestor = JudgmentIngestor()
    results = ingestor.ingest_batch([str(f) for f in pdf_files])
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Ingest all criminal cases')
    parser.add_argument('--years', type=str, help='Comma-separated years (e.g., 2024,2023,2022)')
    parser.add_argument('--limit-per-year', type=int, help='Limit files per year')
    parser.add_argument('--start-year', type=int, default=2019, help='Start year')
    parser.add_argument('--end-year', type=int, default=2025, help='End year')
    
    args = parser.parse_args()
    
    # Determine years to process
    if args.years:
        years = [int(y.strip()) for y in args.years.split(',')]
    else:
        years = list(range(args.start_year, args.end_year + 1))
    
    total_results = {
        'successful': [],
        'failed': [],
        'skipped': []
    }
    
    start_time = datetime.now()
    
    for year in years:
        try:
            results = ingest_year(year, limit=args.limit_per_year)
            if results:
                total_results['successful'].extend(results['successful'])
                total_results['failed'].extend(results['failed'])
                total_results['skipped'].extend(results['skipped'])
        except Exception as e:
            logger.error(f"Error processing year {year}: {e}")
            import traceback
            traceback.print_exc()
    
    elapsed = datetime.now() - start_time
    
    # Print summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"Years processed: {years}")
    print(f"Successful: {len(total_results['successful'])}")
    print(f"Skipped: {len(total_results['skipped'])}")
    print(f"Failed: {len(total_results['failed'])}")
    print(f"Time taken: {elapsed}")
    print("="*60)
    
    # Check final database status
    db = get_db_manager()
    counts = db.execute_query("""
        SELECT 
            COUNT(*) as judgments,
            (SELECT COUNT(*) FROM judgment_chunks) as chunks,
            (SELECT COUNT(*) FROM named_entities) as entities
        FROM judgments
    """)
    
    if counts:
        row = counts[0]
        print(f"\nDatabase Status:")
        print(f"  Total Judgments: {row['judgments']}")
        print(f"  Total Chunks: {row['chunks']}")
        print(f"  Total Entities: {row['entities']}")


if __name__ == "__main__":
    main()
