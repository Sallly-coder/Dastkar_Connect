from pathlib import Path
from db import get_db

SCHEMA_PATH = Path(__file__).parent / "schema.sql"

def init_db():
    with open(SCHEMA_PATH) as f:
        schema = f.read()
    conn = get_db()
    conn.executescript(schema)
    conn.commit()
    conn.close()
    print("Database initialised.")

if __name__ == "__main__":
    init_db()