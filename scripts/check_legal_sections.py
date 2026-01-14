"""Check legal sections in database"""
import sys
from pathlib import Path
import os

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.connection import get_db_manager

if __name__ == "__main__":
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = 'postgres'
    
    db = get_db_manager()
    
    print("="*60)
    print("LEGAL SECTIONS TABLE: legal_sections")
    print("="*60)
    
    # Get counts by act
    result = db.execute_query("""
        SELECT act_name, COUNT(*) as count 
        FROM legal_sections 
        GROUP BY act_name 
        ORDER BY act_name
    """)
    
    print("\nActs stored in 'legal_sections' table:")
    print("-"*60)
    for row in result:
        print(f"  {row['act_name']}: {row['count']} sections")
    
    # Show table structure
    print("\n" + "="*60)
    print("Table Structure:")
    print("="*60)
    print("""
Table Name: legal_sections

Columns:
  - id: Primary key
  - act_name: Name of the act (IPC, CrPC, Evidence_Act, Constitution)
  - section_number: Section/article/schedule number
  - title: Section title
  - content: Full text of the section
  - chapter: Chapter number (for IPC, CrPC)
  - part: Part number (for CrPC, Constitution)
  - classification: Cognizable/Non-cognizable, etc. (IPC)
  - punishment: Punishment details (IPC)
  - triable_by: Which court can try (IPC)
  - compoundable: Whether compoundable (IPC)
  - metadata: JSON metadata
  - embedding: Vector embedding (stored as text if pgvector not available)
  - created_at: Timestamp
    """)
    
    # Show sample data
    print("\n" + "="*60)
    print("Sample Records:")
    print("="*60)
    samples = db.execute_query("""
        SELECT act_name, section_number, title, 
               LEFT(content, 100) as content_preview
        FROM legal_sections 
        WHERE act_name = 'IPC' AND section_number = '302'
           OR act_name = 'CrPC' AND section_number = '154'
           OR act_name = 'Evidence_Act' AND section_number = '3'
        ORDER BY act_name
    """)
    
    for row in samples:
        print(f"\n{row['act_name']} Section {row['section_number']}:")
        print(f"  Title: {row['title']}")
        print(f"  Content: {row['content_preview']}...")
