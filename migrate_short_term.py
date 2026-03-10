import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_sqlite_path = os.getenv("SQLITE_PATH", str(Path.home() / ".openclaw" / "short_term.db"))
DB_PATH = os.path.expanduser(_sqlite_path)

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            scope TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_context_scope ON daily_context(scope)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_context_timestamp ON daily_context(timestamp)')
    conn.commit()
    conn.close()
    print("✅ Table 'daily_context' successfully created/verified.")

if __name__ == '__main__':
    migrate()
