"""
Database connection utilities for Metro Recommender.
"""

import sqlite3
import logging
from contextlib import contextmanager

from src.config import DB_PATH, SCHEMA_PATH, DATA_DIR

logger = logging.getLogger(__name__)


def get_connection(db_path=None):
    """
    Get a SQLite connection with optimal settings.

    Returns a connection with WAL mode, foreign keys enabled,
    and Row factory for dict-like access.
    """
    path = db_path or DB_PATH
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
    return conn


@contextmanager
def get_db_context(db_path=None):
    """Context manager that auto-closes the connection."""
    conn = get_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


def init_db(conn):
    """Initialize database schema from schema.sql."""
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    conn.commit()
    logger.info("Database schema initialized")


def table_exists(conn, table_name):
    """Check if a table exists in the database."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def table_row_count(conn, table_name):
    """Get the row count for a table."""
    cursor = conn.execute(f"SELECT COUNT(*) FROM [{table_name}]")
    return cursor.fetchone()[0]


def drop_table_if_exists(conn, table_name):
    """Drop a table if it exists (for rebuilding feature tables)."""
    conn.execute(f"DROP TABLE IF EXISTS [{table_name}]")
    conn.commit()
