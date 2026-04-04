import sqlite3

DB = "users.db"

def get_conn():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # USERS TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT,
        status TEXT,
        created_by TEXT,
        approved_by TEXT
    )
    """)

    conn.commit()
    conn.close()