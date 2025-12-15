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

INIT_SQL = """
-- 1. Track how far the worker has processed
CREATE TABLE IF NOT EXISTS projection_offsets (
    projector_name TEXT PRIMARY KEY,
    last_event_id UUID NOT NULL
);

-- 2. Thread heads (latest checkpoint per thread)
CREATE TABLE IF NOT EXISTS thread_heads (
    thread_id TEXT PRIMARY KEY,
    checkpoint_id TEXT NOT NULL,
    ai_message_id TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. Timeline of messages per thread
CREATE TABLE IF NOT EXISTS thread_timeline (
    id UUID PRIMARY KEY,
    thread_id TEXT NOT NULL,
    ai_message_id TEXT NOT NULL,
    parent_ai_message_id TEXT,
    checkpoint_id TEXT NOT NULL,
    turn_index INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_thread_timeline_thread
ON thread_timeline(thread_id, turn_index);

-- 4. Branch relationships
CREATE TABLE IF NOT EXISTS branches_projection (
    child_thread_id TEXT PRIMARY KEY,
    parent_thread_id TEXT NOT NULL,
    parent_ai_message_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
"""

def init_db():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    try:
        with conn.cursor() as cur:
            cur.execute(INIT_SQL)
            print("projections db tables created")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
