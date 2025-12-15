from psycopg import Connection
from app.core.event_store import Event
from app.projections import handlers


EVENT_HANDLER_MAP = {
    "UserMessageAdded": handlers.handle_user_message_added,
    "LLMResponseGenerated": handlers.handle_llm_response_generated,
    "CheckpointCreated": handlers.handle_checkpoint_created,
    "ThreadForked": handlers.handle_thread_forked,
}


class Projector:
    def __init__(self, conn: Connection):
        self.conn = conn

    def project_event(self, event: Event):
        handler = EVENT_HANDLER_MAP.get(event.event_type)
        if not handler:
            return  # silence is valid

        handler(self.conn, event)
        self.conn.commit()

    def project_events(self, events: list[Event]):
        for event in events:
            self.project_event(event)
