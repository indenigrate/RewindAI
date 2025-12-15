### API Endpoint Descriptions and Examples

#### 1. `POST /commands/create-thread`

*   **Description:** Creates a new conversation thread.
*   **Request Body (`CreateThreadRequest`):**
    ```json
    {
      "thread_id": "string"  // Optional client-provided thread ID. If not provided, a unique ID will be generated.
    }
    ```
*   **Response Body (`CreateThreadResponse`):**
    ```json
    {
      "thread_id": "string",  // The ID of the newly created thread.
      "event_id": "string"    // The ID of the ThreadCreated event.
    }
    ```
*   **Example `curl` command:**
    ```bash
    curl -X POST http://localhost:8000/commands/create-thread \
    -H "Content-Type: application/json" \
    -d '{"thread_id": "my-new-thread"}'
    ```
    *(Alternatively, omit `thread_id` to have one generated automatically: `curl -X POST http://localhost:8000/commands/create-thread -H "Content-Type: application/json" -d '{}'`)*

#### 2. `POST /commands/send-message`

*   **Description:** Sends a user message to a specified thread.
*   **Request Body (`SendMessageRequest`):**
    ```json
    {
      "thread_id": "string", // The ID of the thread to send the message to.
      "content": "string"    // The content of the user's message. (Must not be empty)
    }
    ```
*   **Response Body (`SendMessageResponse`):**
    ```json
    {
      "thread_id": "string", // The ID of the thread the message was sent to.
      "event_id": "string"   // The ID of the UserMessageAdded event.
    }
    ```
*   **Example `curl` command:**
    ```bash
    curl -X POST http://localhost:8000/commands/send-message \
    -H "Content-Type: application/json" \
    -d '{"thread_id": "my-new-thread", "content": "Hello AI!"}'
    ```

#### 3. `POST /commands/fork-thread`

*   **Description:** Forks an existing conversation thread from a specific event number, creating a new independent branch.
*   **Request Body (`ForkThreadRequest`):**
    ```json
    {
      "source_thread_id": "string", // The ID of the thread to fork from.
      "event_number": "integer"     // The event number in the source thread from which to fork.
    }
    ```
*   **Response Body (`ForkThreadResponse`):**
    ```json
    {
      "new_thread_id": "string" // The ID of the newly created forked thread.
    }
    ```
*   **Example `curl` command:**
    ```bash
    curl -X POST http://localhost:8000/commands/fork-thread \
    -H "Content-Type: application/json" \
    -d '{"source_thread_id": "my-new-thread", "event_number": 1}'
    ```

#### 4. `GET /threads`

*   **Description:** Retrieves a list of all existing conversation threads.
*   **Request Body:** None
*   **Response Body:** An array of thread objects. Each object contains:
    ```json
    [
      {
        "thread_id": "string",            // The ID of the thread.
        "latest_checkpoint_id": "string", // The ID of the latest LangGraph checkpoint for this thread.
        "latest_ai_message_id": "string", // The ID of the latest AI message in this thread.
        "event_number": "integer"         // The event number of the latest event in this thread.
      }
    ]
    ```
*   **Example `curl` command:**
    ```bash
    curl http://localhost:8000/threads
    ```

#### 5. `GET /threads/{thread_id}/messages`

*   **Description:** Retrieves all messages for a specific thread, optionally filtered by a checkpoint.
*   **Path Parameters:**
    *   `thread_id`: `string` - The ID of the thread.
*   **Query Parameters:**
    *   `checkpoint_id`: `string` (Optional) - If provided, messages will be filtered up to and including this checkpoint.
*   **Response Body:** An array of message objects. Each object contains:
    ```json
    [
      {
        "role": "string",         // The role of the message sender (e.g., "user", "assistant").
        "content": "string",      // The content of the message.
        "message_id": "string",   // The ID of the message.
        "event_number": "integer",// The event number when this message was added.
        "created_at": "string"    // ISO 8601 timestamp of when the message was created.
      }
    ]
    ```
*   **Example `curl` command (all messages):**
    ```bash
    curl http://localhost:8000/threads/my-new-thread/messages
    ```
*   **Example `curl` command (messages up to a checkpoint):**
    ```bash
    curl http://localhost:8000/threads/my-new-thread/messages?checkpoint_id=some_checkpoint_uuid
    ```

#### 6. `GET /threads/{thread_id}/branches`

*   **Description:** Retrieves a list of all threads that were forked from the specified parent thread.
*   **Path Parameters:**
    *   `thread_id`: `string` - The ID of the parent thread.
*   **Request Body:** None
*   **Response Body:** An array of branch objects. Each object contains:
    ```json
    [
      {
        "thread_id": "string",           // The ID of the forked thread (the new branch).
        "parent_thread_id": "string",    // The ID of the parent thread from which this branch was created.
        "from_event_number": "integer",  // The event number in the parent thread where the fork occurred.
        "created_at": "string"           // ISO 8601 timestamp of when the branch was created.
      }
    ]
    ```
*   **Example `curl` command:**
    ```bash
    curl http://localhost:8000/threads/my-new-thread/branches
    ```

#### 7. `GET /threads/{thread_id}/head`

*   **Description:** Retrieves the latest state (head) of a specific conversation thread.
*   **Path Parameters:**
    *   `thread_id`: `string` - The ID of the thread.
*   **Request Body:** None
*   **Response Body:** A thread head object. Contains:
    ```json
    {
      "thread_id": "string",            // The ID of the thread.
      "latest_checkpoint_id": "string", // The ID of the latest LangGraph checkpoint for this thread.
      "latest_ai_message_id": "string", // The ID of the latest AI message in this thread.
      "event_number": "integer"         // The event number of the latest event in this thread.
    }
    ```
*   **Example `curl` command:**
    ```bash
    curl http://localhost:8000/threads/my-new-thread/head
    ```
