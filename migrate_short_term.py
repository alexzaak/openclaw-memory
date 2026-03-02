import sqlite3

DB_PATH = '/home/clawdi/.openclaw/short_term.db'

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
    print("✅ Tabelle 'daily_context' erfolgreich angelegt/überprüft.")

if __name__ == '__main__':
    migrate()
