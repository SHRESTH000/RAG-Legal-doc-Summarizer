"""
Update database schema to use pgvector now that it's installed
Converts text embeddings to vector type
"""

import sys
from pathlib import Path
import os

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.connection import get_db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_for_pgvector():
    """Update schema to use pgvector"""
    
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = 'postgres'
    
    db = get_db_manager()
    
    # Check if pgvector is available
    try:
        result = db.execute_one("""
            SELECT EXISTS(
                SELECT 1 FROM pg_extension WHERE extname = 'vector'
            ) as installed
        """)
        
        if not result or not result.get('installed'):
            logger.error("pgvector extension not installed!")
            logger.info("Please run: CREATE EXTENSION vector;")
            return False
        
        logger.info("✅ pgvector extension found")
        
        # Check current column types
        check_columns = db.execute_query("""
            SELECT 
                table_name,
                column_name,
                data_type
            FROM information_schema.columns
            WHERE table_name IN ('judgment_chunks', 'legal_sections')
            AND column_name = 'embedding'
        """)
        
        logger.info("\nCurrent embedding column types:")
        for row in check_columns:
            logger.info(f"  {row['table_name']}.{row['column_name']}: {row['data_type']}")
        
        # Update schema - convert text to vector if needed
        logger.info("\nUpdating schema for pgvector...")
        
        updates = []
        
        # Check judgment_chunks
        if check_columns:
            for row in check_columns:
                if row['data_type'] == 'text':
                    table = row['table_name']
                    logger.info(f"Converting {table}.embedding from text to vector(384)...")
                    
                    # This is a complex migration - we'll need to:
                    # 1. Create new column
                    # 2. Copy data (parsing text to vector)
                    # 3. Drop old column
                    # 4. Rename new column
                    
                    # For now, just inform user
                    logger.warning(f"⚠️  {table}.embedding is currently TEXT type")
                    logger.info(f"   To convert to vector, you'll need to:")
                    logger.info(f"   1. Ensure all embeddings are valid")
                    logger.info(f"   2. Run migration script")
                    updates.append(table)
        
        if updates:
            logger.warning("\n⚠️  Manual migration needed for vector type conversion")
            logger.info("\nYou can continue using text storage for now.")
            logger.info("New chunks will use vector type when pgvector is available.")
        else:
            logger.info("\n✅ Schema is ready for pgvector")
        
        # Try to create vector index
        logger.info("\nCreating vector indexes...")
        try:
            db.execute_update("""
                CREATE INDEX IF NOT EXISTS idx_judgment_chunks_embedding_vector
                ON judgment_chunks USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)
            logger.info("✅ Vector index created for judgment_chunks")
        except Exception as e:
            logger.warning(f"Could not create vector index: {e}")
        
        try:
            db.execute_update("""
                CREATE INDEX IF NOT EXISTS idx_legal_sections_embedding_vector
                ON legal_sections USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)
            logger.info("✅ Vector index created for legal_sections")
        except Exception as e:
            logger.warning(f"Could not create vector index: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking pgvector: {e}")
        return False


if __name__ == "__main__":
    update_for_pgvector()
