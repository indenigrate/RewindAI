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
    BRANCHES_PROJECTION_SQL,
)


class ProjectionWorker:
    def __init__(self):
        # Logical name for this projection pipeline
        self.projection_name = "main_projection"

    # --------------------------------------------------
    # Schema init
    # --------------------------------------------------
    @staticmethod
    def _init_tables():
        with get_app_db() as conn:
            with conn.cursor() as cur:
                cur.execute(THREAD_TIMELINE_SQL)
                cur.execute(MESSAGE_CHECKPOINTS_SQL)
                cur.execute(THREAD_HEADS_SQL)
                cur.execute(PROJECTION_OFFSET_SQL)
                cur.execute(BRANCHES_PROJECTION_SQL)
            conn.commit()

    # --------------------------------------------------
    # Offset handling (UUID-based)
    # --------------------------------------------------
    def _get_last_event_id(self, conn: Connection):
        with conn.cursor() as cur:
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

    def _update_offset(self, conn: Connection, event_id):
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO projection_offsets (projection_name, last_event_id)
                VALUES (%s, %s)
                ON CONFLICT (projection_name)
                DO UPDATE SET last_event_id = EXCLUDED.last_event_id
                """,
                (self.projection_name, event_id),
            )
        conn.commit()

    # --------------------------------------------------
    # Batch processing
    # --------------------------------------------------
    def run_once(self, limit: int = 100) -> bool:
        with get_app_db() as conn:
            store = EventStore(conn)
            projector = Projector(conn)
            
            last_event_id = self._get_last_event_id(conn)
            print(f"Checking for new events after: {last_event_id}")

            events = store.load_events_after(
                last_event_id=last_event_id,
                limit=limit,
            )

            if not events:
                print("No new events found.")
                return False

            print(f"Found {len(events)} new events to project.")
            for event in events:
                print(f"  -> Projecting event {event.event_id} ({event.event_type})")
                projector.project_event(event)
                self._update_offset(conn, event.event_id)

            return True

    # --------------------------------------------------
    # Main loop
    # --------------------------------------------------
    def run(self):
        print("Projection worker started")

        while True:
            try:
                processed = self.run_once()
                if not processed:
                    time.sleep(0.5)
            except Exception as e:
                print("❌ Projection worker error:", e)
                time.sleep(1)


# --------------------------------------------------
# Entrypoint
# --------------------------------------------------
def main():
    ProjectionWorker._init_tables()
    worker = ProjectionWorker()
    worker.run()


if __name__ == "__main__":
    main()
