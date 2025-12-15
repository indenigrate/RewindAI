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

        initial_resume_checkpoint_id = None

        # 1. Try to find the latest checkpoint in the current thread's history
        for event in reversed(events):
            if event.event_type == "CheckpointCreated":
                initial_resume_checkpoint_id = event.payload["checkpoint_id"]
                print(f"  -> Found latest checkpoint in current thread: {initial_resume_checkpoint_id}")
                break
        
        # 2. If no local checkpoint, and it's a forked thread, use the parent's checkpoint at the fork point
        if initial_resume_checkpoint_id is None:
            fork_event = next((e for e in events if e.event_type == "ThreadForked"), None)
            if fork_event:
                parent_thread_id = fork_event.payload["parent_thread_id"]
                from_event_number = fork_event.payload["from_event_number"]
                
                print(f"  -> Fork detected from parent {parent_thread_id} at event {from_event_number}.")
                parent_events = store.load_thread_events(parent_thread_id)
                
                # The CheckpointCreated event is always the one after the LLMResponseGenerated event
                checkpoint_event = next((e for e in parent_events if e.event_number == from_event_number + 1 and e.event_type == "CheckpointCreated"), None)
                
                if checkpoint_event:
                    initial_resume_checkpoint_id = checkpoint_event.payload["checkpoint_id"]
                    print(f"  -> Found parent checkpoint to resume from: {initial_resume_checkpoint_id}")

        
        # Process pending messages, passing the appropriate resume_checkpoint_id
        current_resume_checkpoint_id = initial_resume_checkpoint_id
        for user_event in pending:
            self._handle_user_message(store, thread_id, user_event, current_resume_checkpoint_id)
            # After processing, the next message should resume from the newly created checkpoint (if any)
            # This logic will be handled by run_langgraph_from_events internally
            # For simplicity here, we assume subsequent calls will fetch the latest
            # This 'current_resume_checkpoint_id' only really applies to the first message in this batch.
            # Subsequent messages in the 'pending' list should just build on the graph state.
            current_resume_checkpoint_id = None # Reset so only the first in batch uses the explicit resume_checkpoint_id

    def _handle_user_message(self, store: EventStore, thread_id: str, user_event: Event, resume_checkpoint_id: Optional[str] = None):
        print(f"    -> Processing message {user_event.event_id} in thread {thread_id} to generate AI response...")
        try:
            # Construct the full history for LangGraph, including parent thread messages if forked
            full_thread_events = []

            # Load all events for the current thread
            current_thread_events = store.load_thread_events(thread_id)

            # Check if this is a forked thread
            fork_event = next((e for e in current_thread_events if e.event_type == "ThreadForked"), None)

            if fork_event:
                parent_thread_id = fork_event.payload["parent_thread_id"]
                from_event_number = fork_event.payload["from_event_number"]

                # Load parent thread's messages up to the fork point
                parent_events = store.load_thread_events(parent_thread_id)
                full_thread_events.extend([
                    e for e in parent_events
                    if e.event_number <= from_event_number
                ])
            
            # Add all events from the current thread (forked or not)
            full_thread_events.extend(current_thread_events)

            # Filter to include only events up to the current user message, and sort by event_number
            prior_events = [
                e for e in full_thread_events
                if e.event_number <= user_event.event_number
            ]
            prior_events.sort(key=lambda e: e.event_number) # Ensure chronological order for LangGraph

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
