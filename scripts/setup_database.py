"""
Setup script to initialize database schema and verify setup
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import get_db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_database_setup():
    """Check if database is properly set up"""
    logger.info("Checking database setup...")
    
    db = get_db_manager()
    
    # Check connection
    if not db.check_connection():
        logger.error("❌ Database connection failed!")
        return False
    logger.info("✅ Database connection successful")
    
    # Check extensions
    extensions = db.check_extensions()
    if extensions.get('vector'):
        logger.info("✅ pgvector extension installed")
    else:
        logger.warning("⚠️  pgvector extension not installed (optional for now)")
        logger.info("   Vector search will use alternative method")
        logger.info("   To install: https://github.com/pgvector/pgvector")
        # Don't fail - we can work without it
    
    if extensions.get('pg_trgm'):
        logger.info("✅ pg_trgm extension installed")
    else:
        logger.warning("⚠️  pg_trgm extension not installed (optional)")
    
    # Check tables
    tables = ['judgments', 'judgment_chunks', 'legal_sections', 
              'named_entities', 'summaries']
    
    for table in tables:
        try:
            result = db.execute_one(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"
            )
            if result and result['exists']:
                logger.info(f"✅ Table '{table}' exists")
            else:
                logger.error(f"❌ Table '{table}' does not exist")
                logger.info("   Run: psql -d legal_rag -f database/schema.sql")
                return False
        except Exception as e:
            logger.error(f"❌ Error checking table '{table}': {e}")
            return False
    
    # Check indexes
    try:
        indexes = db.execute_query("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND tablename IN ('judgment_chunks', 'legal_sections')
        """)
        logger.info(f"✅ Found {len(indexes)} indexes on key tables")
    except Exception as e:
        logger.warning(f"⚠️  Could not check indexes: {e}")
    
    logger.info("\n✅ Database setup verified successfully!")
    return True


def main():
    """Main setup function"""
    if check_database_setup():
        logger.info("\nDatabase is ready. You can now:")
        logger.info("1. Load legal datasets: python scripts/load_legal_datasets.py")
        logger.info("2. Start ingesting judgments")
    else:
        logger.error("\n❌ Database setup incomplete. Please fix the issues above.")


if __name__ == "__main__":
    main()
