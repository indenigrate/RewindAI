import time
from psycopg import Connection

from app.core.event_store import EventStore
from app.projections.projector import Projector
from app.projections.models import (
    THREAD_TIMELINE_SQL,
    MESSAGE_CHECKPOINTS_SQL,
    THREAD_HEADS_SQL,
    PROJECTION_OFFSET_SQL,
)
from app.projections import handlers


class ProjectionWorker:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.store = EventStore(conn)
        self.projector = Projector(conn)
        self.projection_name = "main_projection"

        self._init_tables()

    def _init_tables(self):
        with self.conn.cursor() as cur:
            cur.execute(THREAD_TIMELINE_SQL)
            cur.execute(MESSAGE_CHECKPOINTS_SQL)
            cur.execute(THREAD_HEADS_SQL)
            cur.execute(PROJECTION_OFFSET_SQL)
        self.conn.commit()


    def _get_last_event_number(self) -> int:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT last_event_number
                FROM projection_offsets
                WHERE projection_name = %s
                """,
                (self.projection_name,),
            )
            row = cur.fetchone()
            return row["last_event_number"] if row else 0

    def _update_offset(self, event_number: int):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO projection_offsets (projection_name, last_event_number)
                VALUES (%s, %s)
                ON CONFLICT (projection_name)
                DO UPDATE SET last_event_number = EXCLUDED.last_event_number
                """,
                (self.projection_name, event_number),
            )


    def _process_batch(self, limit: int = 100):
        last_event_number = self._get_last_event_number()

        events = self.store.load_events_after(
            last_event_number,
            limit=limit
        )

        if not events:
            return False

        for event in events:
            self.projector.project_event(event)
            self._update_offset(event.event_number)

        return True


    def run(self):
        print("📽️ Projection worker started")

        while True:
            try:
                processed = self._process_batch()
                if not processed:
                    time.sleep(0.5)
            except Exception as e:
                print("❌ Projection worker error:", e)
                time.sleep(1)
