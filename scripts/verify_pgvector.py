"""Verify pgvector installation and usage"""
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
    
    print("="*70)
    print("PGVECTOR VERIFICATION")
    print("="*70)
    
    # Check extension
    try:
        ext_result = db.execute_one("""
            SELECT EXISTS(
                SELECT 1 FROM pg_extension WHERE extname = 'vector'
            ) as installed
        """)
        if ext_result and ext_result.get('installed'):
            print("[OK] pgvector extension is installed")
        else:
            print("[NOT FOUND] pgvector extension not installed")
    except Exception as e:
        print(f"[ERROR] Could not check extension: {e}")
    
    # Check embedding column types
    print("\nEmbedding Column Types:")
    print("-"*70)
    
    try:
        column_types = db.execute_query("""
            SELECT 
                table_name,
                column_name,
                data_type,
                udt_name
            FROM information_schema.columns
            WHERE table_name IN ('judgment_chunks', 'legal_sections')
            AND column_name = 'embedding'
        """)
        
        for row in column_types:
            table = row['table_name']
            dtype = row.get('udt_name') or row.get('data_type', 'unknown')
            print(f"  {table}.embedding: {dtype}")
            
            if dtype == 'vector':
                print(f"    [OK] Using pgvector type")
            elif dtype == 'text':
                print(f"    [TEXT] Still using text (needs migration)")
            else:
                print(f"    [UNKNOWN] Type: {dtype}")
    except Exception as e:
        print(f"Error checking columns: {e}")
    
    # Test vector query
    print("\nTesting Vector Query:")
    print("-"*70)
    
    try:
        # Try to get embedding type from actual data
        test_result = db.execute_one("""
            SELECT pg_typeof(embedding) as embed_type
            FROM judgment_chunks
            WHERE embedding IS NOT NULL
            LIMIT 1
        """)
        
        if test_result:
            embed_type = test_result.get('embed_type', 'unknown')
            print(f"  Actual embedding type: {embed_type}")
            
            if 'vector' in str(embed_type).lower():
                print("  [OK] Vector queries will work")
                
                # Try a similarity query
                try:
                    test_query = db.execute_query("""
                        SELECT id
                        FROM judgment_chunks
                        WHERE embedding IS NOT NULL
                        ORDER BY embedding <=> '[0.1,0.2,0.3,0.4,0.5]'::vector(384)
                        LIMIT 1
                    """)
                    if test_query:
                        print("  [OK] Vector similarity search is working!")
                except Exception as e:
                    print(f"  [WARNING] Vector search test failed: {e}")
                    print("  (This is normal if embedding dimensions don't match)")
            else:
                print("  [INFO] Not using vector type yet")
    except Exception as e:
        print(f"  [ERROR] Could not test: {e}")
    
    # Check indexes
    print("\nVector Indexes:")
    print("-"*70)
    
    try:
        indexes = db.execute_query("""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND (indexname LIKE '%embedding%' OR indexdef LIKE '%vector%')
        """)
        
        if indexes:
            for idx in indexes:
                print(f"  {idx['indexname']}")
                if 'ivfflat' in idx.get('indexdef', '').lower():
                    print("    [OK] IVFFlat vector index")
        else:
            print("  [INFO] No vector indexes found (may need to create)")
    except Exception as e:
        print(f"  [ERROR] Could not check indexes: {e}")
    
    print("\n" + "="*70)
