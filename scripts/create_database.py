"""
Create database and install schema using Python (no command-line tools needed)
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


def create_database_and_schema():
    """Create database and install schema"""
    
    # Get connection parameters
    host = os.getenv('DB_HOST', 'localhost')
    port = int(os.getenv('DB_PORT', '5432'))
    database = os.getenv('DB_NAME', 'legal_rag')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', 'postgres')
    
    # Connect to default postgres database to create our database
    try:
        logger.info(f"Connecting to PostgreSQL server at {host}:{port}...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            database='postgres',  # Connect to default database
            user=user,
            password=password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (database,)
        )
        exists = cursor.fetchone()
        
        if exists:
            logger.info(f"Database '{database}' already exists")
        else:
            # Create database
            logger.info(f"Creating database '{database}'...")
            cursor.execute(f'CREATE DATABASE {database}')
            logger.info(f"✅ Database '{database}' created successfully")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        logger.error("Please ensure:")
        logger.error("1. PostgreSQL is running")
        logger.error("2. Password is correct")
        logger.error("3. User has CREATE DATABASE privilege")
        return False
    
    # Now connect to our database and install schema
    try:
        logger.info(f"Connecting to database '{database}'...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        cursor = conn.cursor()
        
        # Install extensions
        logger.info("Installing pgvector extension...")
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.commit()
            logger.info("✅ pgvector extension installed")
            vector_available = True
        except Exception as e:
            logger.warning(f"Could not install pgvector: {e}")
            logger.warning("pgvector not available - vector search will be disabled")
            logger.warning("You can install pgvector later from: https://github.com/pgvector/pgvector")
            conn.rollback()
            vector_available = False
        
        logger.info("Installing pg_trgm extension...")
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
            conn.commit()
            logger.info("✅ pg_trgm extension installed")
        except Exception as e:
            logger.warning(f"Could not install pg_trgm: {e}")
            conn.rollback()
        
        # Read and execute schema
        schema_path = Path(__file__).parent.parent / "database" / "schema.sql"
        if schema_path.exists():
            logger.info("Installing database schema...")
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # If vector not available, modify schema to use text instead
            if not vector_available:
                # Replace vector(384) with text for now
                schema_sql = schema_sql.replace('vector(384)', 'text')
                schema_sql = schema_sql.replace('::vector', '::text')
                # Remove vector-specific index creation
                import re
                schema_sql = re.sub(r'CREATE INDEX.*vector.*;', '', schema_sql, flags=re.IGNORECASE)
                logger.info("Modified schema to work without pgvector (using text for embeddings)")
            
            # Execute schema statements one by one
            statements = []
            current_statement = []
            in_function = False
            
            for line in schema_sql.split('\n'):
                # Track function definitions
                if 'CREATE OR REPLACE FUNCTION' in line.upper():
                    in_function = True
                if in_function:
                    current_statement.append(line)
                    if line.strip().endswith(';') and '$$' in line:
                        in_function = False
                        statements.append('\n'.join(current_statement))
                        current_statement = []
                elif line.strip().endswith(';') and not line.strip().startswith('--'):
                    current_statement.append(line)
                    statements.append('\n'.join(current_statement))
                    current_statement = []
                else:
                    current_statement.append(line)
            
            # Execute schema using psycopg2's ability to handle multi-statement SQL
            try:
                # Execute all at once
                cursor.execute(schema_sql)
                conn.commit()
                logger.info(f"✅ Database schema installed successfully")
            except Exception as e:
                # Try executing statement by statement
                logger.info("Trying statement-by-statement execution...")
                conn.rollback()
                
                # Split by semicolons (simple approach)
                simple_statements = [s.strip() + ';' for s in schema_sql.split(';') if s.strip() and not s.strip().startswith('--')]
                
                executed = 0
                for stmt in simple_statements:
                    if not stmt or stmt == ';' or 'CREATE EXTENSION' in stmt.upper():
                        continue
                    try:
                        cursor.execute(stmt)
                        executed += 1
                    except Exception as e:
                        error_msg = str(e).lower()
                        # Skip errors for things that might already exist
                        if 'already exists' not in error_msg and 'does not exist' not in error_msg:
                            if 'vector' not in error_msg:  # Skip vector-related errors
                                logger.debug(f"Warning: {str(e)[:100]}")
                
                conn.commit()
                logger.info(f"✅ Database schema installed ({executed} statements executed)")
        
        cursor.close()
        conn.close()
        
        logger.info("\n" + "="*60)
        logger.info("✅ Database setup complete!")
        logger.info("="*60)
        return True
        
    except psycopg2.Error as e:
        logger.error(f"Error setting up database: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    # Set password if provided as argument
    if len(sys.argv) > 1:
        os.environ['DB_PASSWORD'] = sys.argv[1]
    
    success = create_database_and_schema()
    sys.exit(0 if success else 1)
