import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "sslmode": os.getenv("DB_SSLMODE", "disable"),
}

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
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
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
