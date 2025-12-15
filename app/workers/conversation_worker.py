from typing import List
from psycopg import Connection

from app.core.event_store import EventStore, Event
from app.workers.langgraph_runner import run_langgraph_from_events

def find_unanswered_user_messages(events: List[Event]) -> List[Event]:
    responses = {
        e.payload.get("reply_to")
        for e in events
        if e.event_type == "LLMResponseGenerated"
    }

    return [
        e for e in events
        if e.event_type == "UserMessageAdded"
        and e.event_id.hex not in responses
    ]

class ConversationWorker:
    def __init__(self, conn: Connection):
        self.store = EventStore(conn)

    def process_thread(self, thread_id: str):
        events = self.store.load_thread_events(thread_id)

        pending = find_unanswered_user_messages(events)
        if not pending:
            return

        for user_event in pending:
            self._handle_user_message(thread_id, user_event)


    def _handle_user_message(self, thread_id, user_event):
        prior_events = [
            e for e in self.store.load_thread_events(thread_id)
            if e.event_number <= user_event.event_number
        ]

        result = run_langgraph_from_events(
            events=prior_events,
            thread_id=thread_id,
            resume_checkpoint_id=None,
        )

        self.store.append_events(
            thread_id=thread_id,
            events=[
                (
                    "LLMResponseGenerated",
                    {
                        "ai_message_id": result["ai_message_id"],
                        "content": result["content"],
                        "reply_to": user_event.event_id.hex,
                    },
                ),
                (
                    "CheckpointCreated",
                    {
                        "checkpoint_id": result["checkpoint_id"],
                        "ai_message_id": result["ai_message_id"],
                    },
                ),
            ],
        )
