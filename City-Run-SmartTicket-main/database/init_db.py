"""
init_db.py — Run this to initialize (or reset) the SQLite database
"""
import sqlite3
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

DB_PATH = os.path.join(os.path.dirname(__file__), 'transport.db')

def reset_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("🗑️  Removed old database")

    conn = sqlite3.connect(DB_PATH)
    print("✅ Created transport.db")
    conn.close()

    # Use backend app to init properly
    from app import init_db
    init_db()
    print("✅ All tables created and seeded")

if __name__ == '__main__':
    reset_db()
