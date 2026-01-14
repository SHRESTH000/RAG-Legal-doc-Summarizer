"""
Migrate database from TEXT embeddings to pgvector
Converts existing text embeddings to vector type
"""

import sys
from pathlib import Path
import os
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.connection import get_db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_table_to_vector(table_name: str, column_name: str = 'embedding'):
    """Migrate a table's embedding column from text to vector"""
    
    db = get_db_manager()
    
    # Check current type
    type_check = db.execute_one(f"""
        SELECT data_type 
        FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
    """, (table_name, column_name))
    
    if not type_check:
        logger.warning(f"Column {table_name}.{column_name} not found")
        return False
    
    current_type = type_check['data_type']
    
    if current_type == 'USER-DEFINED' or current_type == 'vector':
        logger.info(f"✅ {table_name}.{column_name} is already vector type")
        return True
    
    logger.info(f"\nMigrating {table_name}.{column_name} from {current_type} to vector(384)...")
    
    try:
        # Step 1: Add new vector column
        logger.info("Step 1: Adding temporary vector column...")
        db.execute_update(f"""
            ALTER TABLE {table_name}
            ADD COLUMN IF NOT EXISTS {column_name}_new vector(384)
        """)
        
        # Step 2: Convert text embeddings to vector (batch processing)
        logger.info("Step 2: Converting embeddings (this may take a while)...")
        
        # Get count
        count_result = db.execute_one(f"""
            SELECT COUNT(*) as total
            FROM {table_name}
            WHERE {column_name} IS NOT NULL
        """)
        total = count_result['total'] if count_result else 0
        logger.info(f"  Converting {total} embeddings...")
        
        # Process in batches
        batch_size = 100
        offset = 0
        converted = 0
        
        while offset < total:
            # Get batch
            rows = db.execute_query(f"""
                SELECT id, {column_name}
                FROM {table_name}
                WHERE {column_name} IS NOT NULL
                AND {column_name}_new IS NULL
                ORDER BY id
                LIMIT %s
            """, (batch_size,))
            
            if not rows:
                break
            
            # Convert and update
            for row in rows:
                embedding_text = row[column_name]
                row_id = row['id']
                
                try:
                    # Parse text to vector
                    if isinstance(embedding_text, str):
                        # Remove brackets and split
                        clean = embedding_text.strip().strip('[]')
                        if clean:
                            # Convert to vector format
                            vector_str = '[' + clean + ']'
                            
                            # Update with vector cast
                            db.execute_update(f"""
                                UPDATE {table_name}
                                SET {column_name}_new = %s::vector
                                WHERE id = %s
                            """, (vector_str, row_id))
                            converted += 1
                except Exception as e:
                    logger.debug(f"Error converting row {row_id}: {e}")
                    continue
            
            offset += batch_size
            if converted % 1000 == 0:
                logger.info(f"  Converted: {converted}/{total}")
        
        logger.info(f"  ✅ Converted {converted} embeddings")
        
        # Step 3: Drop old column and rename new one
        logger.info("Step 3: Replacing old column...")
        
        # Drop old column
        db.execute_update(f"""
            ALTER TABLE {table_name}
            DROP COLUMN IF EXISTS {column_name}
        """)
        
        # Rename new column
        db.execute_update(f"""
            ALTER TABLE {table_name}
            RENAME COLUMN {column_name}_new TO {column_name}
        """)
        
        logger.info(f"✅ Migration complete for {table_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error migrating {table_name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_vector_indexes():
    """Create vector indexes for fast similarity search"""
    db = get_db_manager()
    
    logger.info("\nCreating vector indexes...")
    
    try:
        # Index for judgment_chunks
        db.execute_update("""
            DROP INDEX IF EXISTS idx_judgment_chunks_embedding_vector;
            CREATE INDEX idx_judgment_chunks_embedding_vector
            ON judgment_chunks USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        """)
        logger.info("✅ Vector index created for judgment_chunks")
    except Exception as e:
        logger.warning(f"Could not create index for judgment_chunks: {e}")
    
    try:
        # Index for legal_sections
        db.execute_update("""
            DROP INDEX IF EXISTS idx_legal_sections_embedding_vector;
            CREATE INDEX idx_legal_sections_embedding_vector
            ON legal_sections USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        """)
        logger.info("✅ Vector index created for legal_sections")
    except Exception as e:
        logger.warning(f"Could not create index for legal_sections: {e}")


def main():
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = 'postgres'
    
    db = get_db_manager()
    
    # Verify pgvector
    logger.info("Checking pgvector installation...")
    try:
        result = db.execute_one("""
            SELECT EXISTS(
                SELECT 1 FROM pg_extension WHERE extname = 'vector'
            ) as installed
        """)
        
        if not result or not result.get('installed'):
            logger.error("❌ pgvector extension not installed!")
            logger.info("Please install: CREATE EXTENSION vector;")
            return False
        
        logger.info("✅ pgvector extension is installed")
    except Exception as e:
        logger.error(f"Error checking pgvector: {e}")
        return False
    
    print("\n" + "="*70)
    print("MIGRATING TO PGVECTOR")
    print("="*70)
    
    # Migrate tables
    success = True
    
    if migrate_table_to_vector('judgment_chunks', 'embedding'):
        logger.info("✅ judgment_chunks migrated")
    else:
        logger.error("❌ judgment_chunks migration failed")
        success = False
    
    if migrate_table_to_vector('legal_sections', 'embedding'):
        logger.info("✅ legal_sections migrated")
    else:
        logger.error("❌ legal_sections migration failed")
        success = False
    
    # Create indexes
    if success:
        create_vector_indexes()
    
    print("\n" + "="*70)
    if success:
        print("✅ Migration complete! Vector search is now enabled.")
    else:
        print("⚠️  Migration had issues. Check logs above.")
    print("="*70)
    
    return success


if __name__ == "__main__":
    main()
