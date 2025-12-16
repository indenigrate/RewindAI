### **Flow Explanation: Forking a Branch & Sending a New Message**

This explanation will trace the data flow and file interactions for two distinct operations: first, when a conversation thread is forked, and second, when a new message is sent to that newly forked branch.

---

#### **Part 1: Forking a Branch**

This process initiates a new independent conversation thread, inheriting the history of a parent thread up to a specified point.

**1. User Action: Call to `POST /commands/fork-thread`**

*   **File:** `app/api/commands.py`
*   **Function:** `fork_thread`
*   **Description:**
    *   The user sends a `POST` request to the `/commands/fork-thread` endpoint, providing the `source_thread_id` (the ID of the thread to fork from) and the `event_number` (the point in the parent thread's history where the fork occurs).
    *   A new `thread_id` is generated for the branch (e.g., `branch-xxxx`).
    *   This function **does not interact with LangGraph or directly update projections.** It focuses solely on appending events to the event store.

**2. Event Store Interaction: Appending Events**

*   **File:** `app/api/commands.py` (calls `EventStore` methods) -> `app/core/event_store.py`
*   **Function:** `EventStore.append_events`
*   **Description:**
    *   The `fork_thread` function instructs the `EventStore` to append two new events for the `new_thread_id`:
        *   `ThreadCreated`: Indicates the creation of the new branch. Its payload contains the `new_thread_id`.
        *   `ThreadForked`: Crucial for establishing lineage. Its payload contains `parent_thread_id` and `from_event_number` (the original event number from the parent).
    *   These events are written to the `events` table in the PostgreSQL database. This is the **immutable source of truth**.

**3. Projection Worker: Updating `branches_projection`**

*   **File:** `app/projections/worker.py` -> `app/projections/projector.py` -> `app/projections/handlers.py`
*   **Functions:** `ProjectionWorker.run_once`, `Projector.project_event`, `handle_thread_forked`
*   **Description:**
    *   The `ProjectionWorker` (running continuously in the background) periodically checks for new events in the `events` table by consulting `projection_offsets`.
    *   When it finds the `ThreadForked` event:
        *   `ProjectionWorker.run_once` fetches the event.
        *   `Projector.project_event` dispatches the event to the appropriate handler based on `EVENT_HANDLER_MAP`.
        *   `handle_thread_forked` (in `app/projections/handlers.py`) is invoked.
        *   This handler inserts a new record into the `branches_projection` table. This record contains the `thread_id` of the new branch, the `parent_thread_id`, the `from_event_number`, and the `created_at` timestamp.
    *   The `branches_projection` table is a **read model** that allows the API to quickly list branches of a given parent thread without querying the entire event log.

---

#### **Part 2: Sending a New Message to the Forked Branch**

This process involves adding a new user input to the forked conversation and generating an AI response, ensuring the inherited context is maintained.

**1. User Action: Call to `POST /commands/send-message`**

*   **File:** `app/api/commands.py`
*   **Function:** `send_message`
*   **Description:**
    *   The user sends a `POST` request to the `/commands/send-message` endpoint, providing the `thread_id` of the forked branch (e.g., `branch-xxxx`) and the `content` of the new message.
    *   Like `fork_thread`, this function **does not interact with LangGraph or directly update projections.**

**2. Event Store Interaction: Appending `UserMessageAdded` Event**

*   **File:** `app/api/commands.py` (calls `EventStore` methods) -> `app/core/event_store.py`
*   **Function:** `EventStore.append_event`
*   **Description:**
    *   The `send_message` function appends a `UserMessageAdded` event to the event store for the forked branch's `thread_id`. The payload contains the message `content` and `role` ("user").
    *   This event is written to the `events` table, becoming part of the forked branch's event history.

**3. Conversation Worker: Processing the New Message (Crucial for Context)**

*   **File:** `app/workers/conversation_worker.py` -> `app/core/langgraph_runner.py`
*   **Functions:** `ConversationWorker.process_thread`, `_handle_user_message`, `run_langgraph_from_events`
*   **Description:**
    *   The `ConversationWorker` (running continuously in the background) monitors for new `UserMessageAdded` events that haven't received an AI response.
    *   When it finds the `UserMessageAdded` event for the forked branch:
        *   `ConversationWorker.process_thread` loads all events for the current forked `thread_id`.
        *   **Context Reconstruction (inside `_handle_user_message`):**
            *   It identifies the `ThreadForked` event within the forked branch's history.
            *   It then loads the events from the `parent_thread_id` up to the `from_event_number` (which was `9` in the user's example).
            *   It combines these parent events with all events from the current forked branch. This combined list represents the *full historical context* for LangGraph.
            *   This combined list is then filtered to include only events up to the *current* `UserMessageAdded` event, creating `prior_events`.
        *   **Checkpoint Resumption (inside `process_thread`):**
            *   Before processing the `user_event`, `process_thread` determines the `initial_resume_checkpoint_id`. It first looks for the latest `CheckpointCreated` event within the forked branch's own history.
            *   If no such checkpoint exists in the forked branch (which would be the case for the very first message sent to a fresh fork), it then looks for the `CheckpointCreated` event in the *parent thread* at the fork point (`from_event_number + 1`). This is critical for inheriting the parent's AI state.
        *   `run_langgraph_from_events` is called, feeding it:
            *   The `prior_events` (the full combined historical context).
            *   The `thread_id` of the forked branch.
            *   The `resume_checkpoint_id` (either from the forked branch's own history or the inherited parent checkpoint).
        *   LangGraph, seeded with the correct checkpoint and the full historical context, processes the `UserMessageAdded` event and generates an AI response. Because it receives the full history, it *remembers* information like "I am devansh".
    *   **Emitting AI Events:** LangGraph's result (AI response and new checkpoint ID) is then used to append two more events to the event store for the forked branch:
        *   `LLMResponseGenerated`: Contains the AI's response content and `ai_message_id`.
        *   `CheckpointCreated`: Contains the new `checkpoint_id` (representing the state after this AI response) and the associated `ai_message_id`.

**4. Projection Worker: Updating Read Models**

*   **File:** `app/projections/worker.py` -> `app/projections/projector.py` -> `app/projections/handlers.py`
*   **Functions:** `ProjectionWorker.run_once`, `Projector.project_event`, `handle_llm_response_generated`, `handle_checkpoint_created`
*   **Description:**
    *   The `ProjectionWorker` identifies the newly appended `LLMResponseGenerated` and `CheckpointCreated` events.
    *   `handle_llm_response_generated` inserts the AI message into the `thread_timeline` table for the forked branch.
    *   `handle_checkpoint_created` inserts the mapping into `message_checkpoints` and updates the `thread_timeline` entry with the `checkpoint_id`, and updates `thread_heads` with the latest state for the forked branch.

**5. User Action: Call to `GET /threads/{forked_thread_id}/messages`**

*   **File:** `app/api/reads.py`
*   **Function:** `get_messages`
*   **Description:**
    *   When the user retrieves messages for the forked branch:
        *   The `get_messages` function identifies the `ThreadForked` event in the branch's history.
        *   It loads messages from the `parent_thread_id` up to the `from_event_number`.
        *   It then loads *all* messages from the forked `thread_id`.
        *   It combines these two sets of messages.
        *   Finally, it **sorts all combined messages by their `event_number`**, presenting a single, chronologically ordered conversation history to the user. This is why the user message sent to the forked branch (`"what is my name"`) now appears correctly interspersed with the inherited history.

---

**Summary of Fixes Addressing the User's Issue:**

1.  **Context for LangGraph (`app/workers/conversation_worker.py`):** The modification ensures that `_handle_user_message` now correctly assembles the `prior_events` list for LangGraph, providing the full historical context (parent's history + forked branch's history) up to the current user message. This should allow the AI to "remember" previous interactions like the user's name.
2.  **Message Retrieval Order (`app/api/reads.py`):** The modification to `get_messages` ensures that messages from the forked branch are properly included in the combined history displayed by the API, and sorted correctly.

By implementing these changes, the system now adheres to the "Git for LLM conversations" model, where forked branches correctly inherit and build upon their parent's context.
