from psycopg import Connection
from app.projections.models import (
    THREAD_TIMELINE_SQL,
    MESSAGE_CHECKPOINTS_SQL,
    THREAD_HEADS_SQL,
)


def init_projections(conn: Connection):
    with conn.cursor() as cur:
        cur.execute(THREAD_TIMELINE_SQL)
        cur.execute(MESSAGE_CHECKPOINTS_SQL)
        cur.execute(THREAD_HEADS_SQL)
    conn.commit()
