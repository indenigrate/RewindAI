import time
from psycopg import Connection
from app.db.postgres import get_app_db
from app.core.event_store import EventStore
from app.projections.projector import Projector
from app.projections.models import (
    PROJECTION_OFFSET_SQL,
    THREAD_TIMELINE_SQL,
    MESSAGE_CHECKPOINTS_SQL,
    THREAD_HEADS_SQL,
)


class ProjectionWorker:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.store = EventStore(conn)
        self.projector = Projector(conn)

        # Logical name for this projection pipeline
        self.projection_name = "main_projection"

        self._init_tables()

    # --------------------------------------------------
    # Schema init
    # --------------------------------------------------
    def _init_tables(self):
        with self.conn.cursor() as cur:
            cur.execute(THREAD_TIMELINE_SQL)
            cur.execute(MESSAGE_CHECKPOINTS_SQL)
            cur.execute(THREAD_HEADS_SQL)
            cur.execute(PROJECTION_OFFSET_SQL)
        self.conn.commit()

    # --------------------------------------------------
    # Offset handling (UUID-based)
    # --------------------------------------------------
    def _get_last_event_id(self):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT last_event_id
                FROM projection_offsets
                WHERE projection_name = %s
                """,
                (self.projection_name,),
            )
            row = cur.fetchone()
            return row["last_event_id"] if row else None

    def _update_offset(self, event_id):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO projection_offsets (projection_name, last_event_id)
                VALUES (%s, %s)
                ON CONFLICT (projection_name)
                DO UPDATE SET last_event_id = EXCLUDED.last_event_id
                """,
                (self.projection_name, event_id),
            )
        self.conn.commit()

    # --------------------------------------------------
    # Batch processing
    # --------------------------------------------------
    def _process_batch(self, limit: int = 100) -> bool:
        last_event_id = self._get_last_event_id()

        events = self.store.load_events_after(
            last_event_id=last_event_id,
            limit=limit,
        )

        if not events:
            return False

        for event in events:
            self.projector.project_event(event)
            self._update_offset(event.event_id)

        return True

    # --------------------------------------------------
    # Main loop
    # --------------------------------------------------
    def run(self):
        print("Projection worker started")

        while True:
            try:
                processed = self._process_batch()
                if not processed:
                    time.sleep(0.5)
            except Exception as e:
                print("❌ Projection worker error:", e)
                time.sleep(1)


# --------------------------------------------------
# Entrypoint
# --------------------------------------------------
def main():
    conn = get_app_db()
    worker = ProjectionWorker(conn)
    worker.run()


if __name__ == "__main__":
    main()
