THREAD_TIMELINE_SQL = """
CREATE TABLE IF NOT EXISTS thread_timeline (
    thread_id TEXT NOT NULL,
    message_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    event_number BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    checkpoint_id UUID,

    PRIMARY KEY (thread_id, event_number)
);
"""

MESSAGE_CHECKPOINTS_SQL = """
CREATE TABLE IF NOT EXISTS message_checkpoints (
    thread_id TEXT NOT NULL,
    ai_message_id TEXT PRIMARY KEY,
    checkpoint_id TEXT NOT NULL
);
"""

THREAD_HEADS_SQL = """
CREATE TABLE IF NOT EXISTS thread_heads (
    thread_id TEXT PRIMARY KEY,
    latest_checkpoint_id TEXT NOT NULL,
    latest_ai_message_id TEXT NOT NULL,
    event_number BIGINT NOT NULL
);
"""

PROJECTION_OFFSET_SQL = """
CREATE TABLE IF NOT EXISTS projection_offsets (
    projection_name TEXT PRIMARY KEY,
    last_event_id UUID NOT NULL
);
"""
