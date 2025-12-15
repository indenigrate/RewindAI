from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List
from uuid import UUID
from datetime import datetime
import psycopg
from psycopg.rows import dict_row

from uuid import uuid4


@dataclass(frozen=True)
class Event:
    event_id: UUID
    event_type: str
    thread_id: str
    event_number: int
    payload: Dict[str, Any]
    created_at: datetime

class EventStore:
    def __init__(self, conn: psycopg.Connection):
        self.conn = conn

    def _next_event_number(
        self, thread_id: str, cur: psycopg.Cursor
    ) -> int:
        cur.execute(
            """
            SELECT COALESCE(MAX(event_number), 0) + 1 AS next_event_number
            FROM events
            WHERE thread_id = %s
            FOR UPDATE
            """,
            (thread_id,),
        )
        return cur.fetchone()["next_event_number"]


    def append_event(
        self,
        *,
        thread_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> Event:
        with self.conn.transaction():
            with self.conn.cursor(row_factory=dict_row) as cur:
                event_number = self._next_event_number(thread_id, cur)
                event_id = uuid4()

                cur.execute(
                    """
                    INSERT INTO events (
                        event_id,
                        event_type,
                        thread_id,
                        event_number,
                        payload
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        event_id,
                        event_type,
                        thread_id,
                        event_number,
                        payload,
                    ),
                )

                row = cur.fetchone()
                return Event(**row)

    def append_events(
        self,
        *,
        thread_id: str,
        events: Iterable[tuple[str, Dict[str, Any]]],
    ) -> List[Event]:
        created: List[Event] = []

        with self.conn.transaction():
            with self.conn.cursor(row_factory=dict_row) as cur:
                for event_type, payload in events:
                    event_number = self._next_event_number(thread_id, cur)
                    event_id = uuid4()

                    cur.execute(
                        """
                        INSERT INTO events (
                            event_id,
                            event_type,
                            thread_id,
                            event_number,
                            payload
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING *
                        """,
                        (
                            event_id,
                            event_type,
                            thread_id,
                            event_number,
                            payload,
                        ),
                    )

                    created.append(Event(**cur.fetchone()))

        return created

    def load_thread_events(self, thread_id: str) -> List[Event]:
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT *
                FROM events
                WHERE thread_id = %s
                ORDER BY event_number ASC
                """,
                (thread_id,),
            )
            return [Event(**row) for row in cur.fetchall()]

    def load_events_up_to(
        self,
        *,
        thread_id: str,
        event_number: int,
    ) -> List[Event]:
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT *
                FROM events
                WHERE thread_id = %s
                  AND event_number <= %s
                ORDER BY event_number ASC
                """,
                (thread_id, event_number),
            )
            return [Event(**row) for row in cur.fetchall()]
