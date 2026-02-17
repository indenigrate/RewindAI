import os
import psycopg
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
-- Required for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS ai_message_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Conversation identity
    thread_id TEXT NOT NULL,

    -- Assistant message (anchor for branching)
    ai_message_id TEXT NOT NULL,

    -- LangGraph checkpoint
    checkpoint_id TEXT NOT NULL,

    -- Branch lineage
    parent_thread_id TEXT,
    parent_ai_message_id TEXT,

    -- Ordering & metadata
    turn_index INTEGER NOT NULL,
    model_name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- One mapping per assistant message per thread (safe add)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uniq_thread_ai_msg'
    ) THEN
        ALTER TABLE ai_message_checkpoints
        ADD CONSTRAINT uniq_thread_ai_msg
        UNIQUE (thread_id, ai_message_id);
    END IF;
END $$;

-- Timeline rendering
CREATE INDEX IF NOT EXISTS idx_thread_timeline
ON ai_message_checkpoints (thread_id, turn_index);

-- Branch graph traversal
CREATE INDEX IF NOT EXISTS idx_parent_lineage
ON ai_message_checkpoints (parent_thread_id, parent_ai_message_id);
"""

def init_db():
    try:
        # Connect using psycopg v3 with autocommit enabled
        conn = psycopg.connect(autocommit=True, **DB_CONFIG)
        
        with conn.cursor() as cur:
            cur.execute(INIT_SQL)
            print("✅ ai_message_checkpoints schema initialized / updated successfully")
            
        conn.close()
    except psycopg.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Tip: Ensure your Docker database container is running (docker compose up -d)")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    init_db()
