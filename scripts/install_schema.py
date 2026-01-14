"""
Install database schema directly
"""

import sys
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def install_schema():
    """Install database schema"""
    
    host = os.getenv('DB_HOST', 'localhost')
    port = int(os.getenv('DB_PORT', '5432'))
    database = os.getenv('DB_NAME', 'legal_rag')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', 'postgres')
    
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Read schema file
        schema_path = Path(__file__).parent.parent / "database" / "schema.sql"
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Remove CREATE EXTENSION statements (we handle those separately)
        lines = schema_sql.split('\n')
        filtered_lines = []
        skip_next = False
        
        for line in lines:
            if 'CREATE EXTENSION' in line.upper():
                continue  # Skip extension creation
            filtered_lines.append(line)
        
        schema_sql = '\n'.join(filtered_lines)
        
        # Replace vector type with text for now (if pgvector not available)
        schema_sql = schema_sql.replace('vector(384)', 'text')
        schema_sql = schema_sql.replace('::vector', '::text')
        
        # Remove vector-specific indexes
        import re
        schema_sql = re.sub(r'CREATE INDEX.*embedding.*vector.*;', '', schema_sql, flags=re.IGNORECASE | re.MULTILINE)
        
        # Execute schema using psycopg2's execute with multiple statements
        logger.info("Executing schema SQL...")
        cursor.execute(schema_sql)
        
        cursor.close()
        conn.close()
        
        logger.info("✅ Schema installed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error installing schema: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = install_schema()
    sys.exit(0 if success else 1)
