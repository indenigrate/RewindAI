from fastapi import APIRouter, Depends, Query, HTTPException
from psycopg import Connection

from app.db.fastapi import get_db

router = APIRouter(prefix="/threads", tags=["reads"])

@router.get("")
def list_threads(db: Connection = Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT
                thread_id,
                parent_thread_id,
                created_at
            FROM thread_heads
            ORDER BY created_at DESC
            """
        )
        return cur.fetchall()


@router.get("/{thread_id}/messages")
def get_messages(
    thread_id: str,
    checkpoint_id: str | None = Query(None),
    db: Connection = Depends(get_db),
):
    if checkpoint_id:
        sql = """
        SELECT
            role,
            content,
            ai_message_id,
            checkpoint_id,
            turn_index,
            created_at
        FROM thread_timeline
        WHERE thread_id = %s
          AND (
              checkpoint_id IS NULL
              OR checkpoint_id <= %s
          )
        ORDER BY turn_index
        """
        params = (thread_id, checkpoint_id)
    else:
        sql = """
        SELECT
            role,
            content,
            ai_message_id,
            checkpoint_id,
            turn_index,
            created_at
        FROM thread_timeline
        WHERE thread_id = %s
        ORDER BY turn_index
        """
        params = (thread_id,)

    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()

@router.get("/{thread_id}/branches")
def list_branches(thread_id: str, db: Connection = Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT
                thread_id,
                parent_thread_id,
                parent_checkpoint_id,
                parent_ai_message_id,
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
                updated_at
            FROM thread_heads
            WHERE thread_id = %s
            """,
            (thread_id,),
        )
        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Thread not found")

        return row
