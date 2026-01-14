"""
Script to ingest judgments into the database
"""

import sys
from pathlib import Path
import argparse

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Fix import conflict - ensure datasets directory doesn't interfere
if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from ingestion.judgment_ingestor import JudgmentIngestor
from database.connection import get_db_manager
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Ingest legal judgments into database')
    parser.add_argument('--folder', type=str, help='Folder containing PDF judgments')
    parser.add_argument('--file', type=str, help='Single PDF file to ingest')
    parser.add_argument('--year', type=int, help='Year folder (e.g., 2024)')
    parser.add_argument('--limit', type=int, help='Limit number of files to process')
    parser.add_argument('--criminal-only', action='store_true', 
                       help='Only process criminal cases')
    
    args = parser.parse_args()
    
    # Initialize ingestor
    ingestor = JudgmentIngestor()
    
    # Get PDF files
    pdf_files = []
    
    if args.file:
        pdf_files = [args.file]
    elif args.folder:
        pdf_files = list(Path(args.folder).glob("*.pdf"))
    elif args.year:
        if args.criminal_only:
            folder = Path(f"criminal_{args.year}")
        else:
            folder = Path(f"judgments_{args.year}")
        
        if folder.exists():
            pdf_files = list(folder.glob("*.pdf"))
        else:
            logger.error(f"Folder not found: {folder}")
            return
    else:
        logger.error("Please provide --file, --folder, or --year")
        return
    
    # Limit files if specified
    if args.limit:
        pdf_files = pdf_files[:args.limit]
    
    logger.info(f"Found {len(pdf_files)} PDF files to ingest")
    
    # Ingest
    results = ingestor.ingest_batch([str(f) for f in pdf_files])
    
    # Print summary
    print("\n" + "="*60)
    print("INGESTION SUMMARY")
    print("="*60)
    print(f"Successful: {len(results['successful'])}")
    print(f"Skipped: {len(results['skipped'])}")
    print(f"Failed: {len(results['failed'])}")
    print("="*60)
    
    # Check database counts
    db = get_db_manager()
    counts = db.execute_query("""
        SELECT 
            COUNT(*) as judgments,
            (SELECT COUNT(DISTINCT judgment_id) FROM judgment_chunks) as judgments_with_chunks,
            (SELECT COUNT(*) FROM judgment_chunks) as total_chunks,
            (SELECT COUNT(*) FROM named_entities) as total_entities
        FROM judgments
    """)
    
    if counts:
        row = counts[0]
        print("\nDatabase Statistics:")
        print(f"  Total judgments: {row['judgments']}")
        print(f"  Judgments with chunks: {row['judgments_with_chunks']}")
        print(f"  Total chunks: {row['total_chunks']}")
        print(f"  Total entities: {row['total_entities']}")


if __name__ == "__main__":
    main()
