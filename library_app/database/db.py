import sqlite3
import os
import logging
from contextlib import contextmanager
from .schema import SCHEMA_SQL

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database connections and initialization."""
    def __init__(self, db_path="data/library.db"):
        self.db_path = db_path
        self._ensure_dir()
        
    def _ensure_dir(self):
        dir_name = os.path.dirname(self.db_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
    def init_db(self):
        """Creates the database and schema if it does not exist."""
        try:
            with self.get_connection() as conn:
                conn.executescript(SCHEMA_SQL)
            logger.info("Database schema initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
            
    @contextmanager
    def get_connection(self):
        """Context manager for database connections, auto-commits entirely or rolls back."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
