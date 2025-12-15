import os
import psycopg
from dotenv import load_dotenv

from app.db.postgres import get_app_db

load_dotenv()

TRUNCATE_SQL = """
TRUNCATE TABLE 
    projection_offsets,
    thread_heads,
    thread_timeline,
    message_checkpoints,
    branches_projection
RESTART IDENTITY;
"""

def clear_db():
    conn = None
    try:
        conn = get_app_db()
        conn.autocommit = True
        with conn.cursor() as cur:
            print("Clearing all projection tables...")
            cur.execute(TRUNCATE_SQL)
            print("✅ All projection tables cleared.")
    except Exception as e:
        print(f"❌ Error clearing projection tables: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    clear_db()
