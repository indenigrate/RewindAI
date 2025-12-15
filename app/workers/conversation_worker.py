from typing import List, Optional
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

        resume_checkpoint_id = None
        # Check if this is a forked thread that needs a checkpoint to resume from
        fork_event = next((e for e in events if e.event_type == "ThreadForked"), None)
        if fork_event:
            # Only use the checkpoint if we are about to process the *first* user message
            is_first_message = not any(e.event_type == "LLMResponseGenerated" for e in events)
            if is_first_message:
                parent_thread_id = fork_event.payload["parent_thread_id"]
                from_event_number = fork_event.payload["from_event_number"]
                
                print(f"  -> Fork detected from parent {parent_thread_id} at event {from_event_number}.")
                parent_events = store.load_thread_events(parent_thread_id)
                
                # The CheckpointCreated event is always the one after the LLMResponseGenerated event
                checkpoint_event = next((e for e in parent_events if e.event_number == from_event_number + 1 and e.event_type == "CheckpointCreated"), None)
                
                if checkpoint_event:
                    resume_checkpoint_id = checkpoint_event.payload["checkpoint_id"]
                    print(f"  -> Found checkpoint to resume from: {resume_checkpoint_id}")


        for user_event in pending:
            # Pass the checkpoint ID, but it will only be used for the first message handled
            self._handle_user_message(store, thread_id, user_event, resume_checkpoint_id)
            # After the first message, don't use the checkpoint again
            resume_checkpoint_id = None


    def _handle_user_message(self, store: EventStore, thread_id: str, user_event: Event, resume_checkpoint_id: Optional[str] = None):
        print(f"    -> Processing message {user_event.event_id} in thread {thread_id} to generate AI response...")
        try:
            # We only need events up to the current user message
            prior_events = [
                e for e in store.load_thread_events(thread_id)
                if e.event_number <= user_event.event_number
            ]

            result = run_langgraph_from_events(
                events=prior_events,
                thread_id=thread_id,
                resume_checkpoint_id=resume_checkpoint_id,
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
