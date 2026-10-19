# S1: SQLite connection
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "database.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # access columns by name: row["email"]
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite ignores FKs unless set per connection
    return conn
