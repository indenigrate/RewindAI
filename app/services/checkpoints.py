def get_next_turn_index(conn, thread_id: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COALESCE(MAX(turn_index), 0) + 1 AS next_turn
            FROM ai_message_checkpoints
            WHERE thread_id = %s
            """,
            (thread_id,)
        )
        return cur.fetchone()["next_turn"]

def store_ai_message_checkpoint(
    conn,
    *,
    thread_id: str,
    ai_message_id: str,
    checkpoint_id: str,
    turn_index: int,
    model_name: str,
    parent_thread_id: str | None = None,
    parent_ai_message_id: str | None = None,
):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ai_message_checkpoints (
                thread_id,
                ai_message_id,
                checkpoint_id,
                parent_thread_id,
                parent_ai_message_id,
                turn_index,
                model_name
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                thread_id,
                ai_message_id,
                checkpoint_id,
                parent_thread_id,
                parent_ai_message_id,
                turn_index,
                model_name,
            )
        )
    conn.commit()
