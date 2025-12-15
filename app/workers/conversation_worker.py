from typing import List
from psycopg import Connection

from app.core.event_store import EventStore, Event
from app.core.langgraph_runner import run_langgraph_from_events

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
    def __init__(self):
        pass

    def process_thread(self, conn: Connection, thread_id: str):
        store = EventStore(conn)
        events = store.load_thread_events(thread_id)

        pending = find_unanswered_user_messages(events)
        if not pending:
            return
        
        print(f"  -> Found {len(pending)} unanswered messages in thread {thread_id}.")
        for user_event in pending:
            self._handle_user_message(store, thread_id, user_event)


    def _handle_user_message(self, store: EventStore, thread_id: str, user_event: Event):
        print(f"    -> Processing message {user_event.event_id} in thread {thread_id} to generate AI response...")
        try:
            prior_events = [
                e for e in store.load_thread_events(thread_id)
                if e.event_number <= user_event.event_number
            ]

            result = run_langgraph_from_events(
                events=prior_events,
                thread_id=thread_id,
                resume_checkpoint_id=None,
            )
            print(f"      - LangGraph run successful. Result: {result}")

            print("      - Saving LLMResponseGenerated and CheckpointCreated events...")
            store.append_events(
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
            print("      - Events saved successfully.")
        except Exception as e:
            print(f"    ❌ Error processing message {user_event.event_id}: {e}")
