from psycopg import Connection
from app.core.event_store import Event


def handle_user_message_added(conn: Connection, event: Event):
    payload = event.payload

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO thread_timeline (
                thread_id,
                message_id,
                role,
                content,
                event_number,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (
                event.thread_id,
                payload.get("message_id", event.event_id.hex),
                payload["role"],
                payload["content"],
                event.event_number,
                event.created_at,
            ),
        )


def handle_llm_response_generated(conn: Connection, event: Event):
    payload = event.payload

    with conn.cursor() as cur:
        # Timeline
        cur.execute(
            """
            INSERT INTO thread_timeline (
                thread_id,
                message_id,
                role,
                content,
                event_number,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (
                event.thread_id,
                payload["ai_message_id"],
                "assistant",
                payload["content"],
                event.event_number,
                event.created_at,
            ),
        )


def handle_checkpoint_created(conn: Connection, event: Event):
    payload = event.payload

    with conn.cursor() as cur:
        # Message → checkpoint index
        cur.execute(
            """
            INSERT INTO message_checkpoints (
                thread_id,
                ai_message_id,
                checkpoint_id
            )
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (
                event.thread_id,
                payload["ai_message_id"],
                payload["checkpoint_id"],
            ),
        )

        # Thread head
        cur.execute(
            """
            INSERT INTO thread_heads (
                thread_id,
                latest_checkpoint_id,
                event_number
            )
            VALUES (%s, %s, %s)
            ON CONFLICT (thread_id)
            DO UPDATE SET
                latest_checkpoint_id = EXCLUDED.latest_checkpoint_id,
                event_number = EXCLUDED.event_number
            """,
            (
                event.thread_id,
                payload["checkpoint_id"],
                event.event_number,
            ),
        )
