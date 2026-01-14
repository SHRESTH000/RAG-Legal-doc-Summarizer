"""
Database connection utilities for Legal RAG System
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager
import os
from typing import Optional, Dict, Any
import logging
from pathlib import Path

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed, skip

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages PostgreSQL database connections with connection pooling"""
    
    def __init__(self, 
                 host: str = None,
                 port: int = 5432,
                 database: str = None,
                 user: str = None,
                 password: str = None,
                 min_connections: int = 2,
                 max_connections: int = 10):
        """
        Initialize database connection manager
        
        Args:
            host: Database host (defaults to env DB_HOST)
            port: Database port (defaults to env DB_PORT or 5432)
            database: Database name (defaults to env DB_NAME)
            user: Database user (defaults to env DB_USER)
            password: Database password (defaults to env DB_PASSWORD)
            min_connections: Minimum connections in pool
            max_connections: Maximum connections in pool
        """
        self.host = host or os.getenv('DB_HOST', 'localhost')
        self.port = int(port or os.getenv('DB_PORT', '5432'))
        self.database = database or os.getenv('DB_NAME', 'legal_rag')
        self.user = user or os.getenv('DB_USER', 'postgres')
        self.password = password or os.getenv('DB_PASSWORD', '')
        
        self.pool: Optional[ThreadedConnectionPool] = None
        self.min_connections = min_connections
        self.max_connections = max_connections
        
    def initialize_pool(self):
        """Initialize connection pool"""
        if self.pool is None:
            try:
                self.pool = ThreadedConnectionPool(
                    self.min_connections,
                    self.max_connections,
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password
                )
                logger.info(f"Database connection pool initialized for {self.database}")
            except Exception as e:
                logger.error(f"Failed to initialize database pool: {e}")
                raise
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool (context manager)"""
        if self.pool is None:
            self.initialize_pool()
        
        conn = self.pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            self.pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, dict_cursor: bool = True):
        """Get a cursor from the pool (context manager)"""
        with self.get_connection() as conn:
            cursor_class = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_class)
            try:
                yield cursor
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = True) -> list:
        """Execute a query and return results"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            return []
    
    def execute_one(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Execute a query and return single result"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute an update/insert/delete query and return rowcount"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    def check_connection(self) -> bool:
        """Check if database connection is working"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    def check_extensions(self) -> Dict[str, bool]:
        """Check if required extensions are installed"""
        extensions = {}
        try:
            with self.get_cursor() as cursor:
                # Check vector extension
                cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
                extensions['vector'] = cursor.fetchone()['exists']
                
                # Check pg_trgm extension
                cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm')")
                extensions['pg_trgm'] = cursor.fetchone()['exists']
        except Exception as e:
            logger.error(f"Failed to check extensions: {e}")
            extensions['error'] = str(e)
        
        return extensions
    
    def close_pool(self):
        """Close all connections in the pool"""
        if self.pool:
            self.pool.closeall()
            self.pool = None
            logger.info("Database connection pool closed")
    
    def __enter__(self):
        self.initialize_pool()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_pool()


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get or create global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        _db_manager.initialize_pool()
    return _db_manager


def init_db(host: str = None, port: int = None, database: str = None,
            user: str = None, password: str = None) -> DatabaseManager:
    """Initialize global database manager with custom settings"""
    global _db_manager
    _db_manager = DatabaseManager(host, port, database, user, password)
    _db_manager.initialize_pool()
    return _db_manager
