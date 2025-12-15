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
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    thread_id TEXT NOT NULL,
    event_number BIGINT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uniq_thread_event_number
ON events (thread_id, event_number);

CREATE INDEX idx_events_thread_order
ON events (thread_id, event_number);

CREATE INDEX idx_events_type
ON events (event_type);

CREATE INDEX idx_events_created_at
ON events (created_at);

CREATE OR REPLACE FUNCTION forbid_event_update()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Events are immutable';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER no_event_update
BEFORE UPDATE ON events
FOR EACH ROW EXECUTE FUNCTION forbid_event_update();

CREATE OR REPLACE FUNCTION forbid_event_delete()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Events cannot be deleted';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER no_event_delete
BEFORE DELETE ON events
FOR EACH ROW EXECUTE FUNCTION forbid_event_delete();
"""

def init_db():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    try:
        with conn.cursor() as cur:
            cur.execute(INIT_SQL)
            print("event store schema initialized / updated successfully")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
