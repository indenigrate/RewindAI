from fastapi import APIRouter, Depends, Query, HTTPException
from psycopg import Connection
from psycopg.rows import dict_row

from app.db.fastapi import get_db
from app.core.event_store import EventStore


router = APIRouter(prefix="/threads", tags=["reads"])


def get_event_store(db: Connection = Depends(get_db)) -> EventStore:
    return EventStore(db)


@router.get("")
def list_threads(db: Connection = Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT
                thread_id,
                latest_checkpoint_id,
                latest_ai_message_id,
                event_number
            FROM thread_heads
            ORDER BY event_number DESC
            """
        )
        return cur.fetchall()


@router.get("/{thread_id}/messages")
def get_messages(
    thread_id: str,
    checkpoint_id: str | None = Query(None),
    db: Connection = Depends(get_db),
    store: EventStore = Depends(get_event_store), # Added EventStore dependency
):
    # Check if this is a forked thread
    fork_event = next((e for e in store.load_thread_events(thread_id) if e.event_type == "ThreadForked"), None)

    all_messages = []

    if fork_event:
        parent_thread_id = fork_event.payload["parent_thread_id"]
        from_event_number = fork_event.payload["from_event_number"]

        # Load parent thread's messages up to the fork point
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    role,
                    content,
                    message_id,
                    event_number,
                    created_at
                FROM thread_timeline
                WHERE thread_id = %s
                  AND event_number <= %s
                ORDER BY event_number ASC
                """,
                (parent_thread_id, from_event_number),
            )
            all_messages.extend(cur.fetchall())
        
        # Now load messages for the current forked thread
        with db.cursor(row_factory=dict_row) as cur:
            if checkpoint_id:
                sql = """
                SELECT
                    role,
                    content,
                    message_id,
                    event_number,
                    created_at
                FROM thread_timeline
                WHERE thread_id = %s
                  AND (
                      checkpoint_id IS NULL
                      OR checkpoint_id <= %s
                  )
                ORDER BY event_number
                """
                params = (thread_id, checkpoint_id)
            else:
                sql = """
                SELECT
                    role,
                    content,
                    message_id,
                    event_number,
                    created_at
                FROM thread_timeline
                WHERE thread_id = %s
                ORDER BY event_number
                """
                params = (thread_id,)
            cur.execute(sql, params)
            all_messages.extend(cur.fetchall())

        # Sort combined messages by event_number
        all_messages.sort(key=lambda msg: msg["event_number"])
        return all_messages
    else:
        # Original logic for non-forked threads
        with db.cursor(row_factory=dict_row) as cur:
            if checkpoint_id:
                sql = """
                SELECT
                    role,
                    content,
                    message_id,
                    event_number,
                    created_at
                FROM thread_timeline
                WHERE thread_id = %s
                  AND (
                      checkpoint_id IS NULL
                      OR checkpoint_id <= %s
                  )
                ORDER BY event_number
                """
                params = (thread_id, checkpoint_id)
            else:
                sql = """
                SELECT
                    role,
                    content,
                    message_id,
                    event_number,
                    created_at
                FROM thread_timeline
                WHERE thread_id = %s
                ORDER BY event_number
                """
                params = (thread_id,)
            cur.execute(sql, params)
            return cur.fetchall()

@router.get("/{thread_id}/branches")
def list_branches(thread_id: str, db: Connection = Depends(get_db)):
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT
                thread_id,
                parent_thread_id,
                from_event_number,
                created_at
            FROM branches_projection
            WHERE parent_thread_id = %s
            ORDER BY created_at
            """,
            (thread_id,),
        )
        return cur.fetchall()


@router.get("/{thread_id}/head")
def get_thread_head(thread_id: str, db: Connection = Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT
                thread_id,
                latest_checkpoint_id,
                latest_ai_message_id,
                event_number
            FROM thread_heads
            WHERE thread_id = %s
            """,
            (thread_id,),
        )
        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Thread not found")

        return row
