"""Check database ingestion status"""
import sys
from pathlib import Path
import os

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from database.connection import get_db_manager

if __name__ == "__main__":
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = 'postgres'
    
    db = get_db_manager()
    
    print("="*60)
    print("DATABASE STATUS")
    print("="*60)
    
    # Get counts
    counts = db.execute_query("""
        SELECT 
            COUNT(*) as judgments,
            (SELECT COUNT(*) FROM judgment_chunks) as chunks,
            (SELECT COUNT(*) FROM named_entities) as entities
        FROM judgments
    """)
    
    if counts:
        row = counts[0]
        print(f"\nJudgments: {row['judgments']}")
        print(f"Chunks: {row['chunks']}")
        print(f"Entities: {row['entities']}")
    
    # Get judgments by year
    years = db.execute_query("""
        SELECT year, COUNT(*) as count 
        FROM judgments 
        WHERE year IS NOT NULL
        GROUP BY year 
        ORDER BY year DESC
    """)
    
    if years:
        print("\nJudgments by Year:")
        print("-"*60)
        for row in years:
            print(f"  {row['year']}: {row['count']} judgments")
    
    print("\n" + "="*60)
