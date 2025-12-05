import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "dns.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS domains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT UNIQUE,
            monitor INTEGER DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS dns_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            records_json TEXT,
            changed INTEGER,
            FOREIGN KEY(domain_id) REFERENCES domains(id)
        )
    """)

    conn.commit()
    conn.close()
