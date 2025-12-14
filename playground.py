import os
import uuid
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver

# Load env vars
load_dotenv()

# Build Postgres connection string
POSTGRES_CONN_STRING = (
    f"postgresql://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}"
    f"?sslmode={os.getenv('DB_SSLMODE', 'disable')}"
)

# ---------------------------
# App DB connection
# ---------------------------
app_db = psycopg.connect(
    POSTGRES_CONN_STRING,
    row_factory=dict_row
)

# ---------------------------
# Model
# ---------------------------
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    api_key=os.getenv("GOOGLE_API_KEY"),
    request_timeout=30,
)

# ---------------------------
# Graph node
# ---------------------------
def call_google_node(state: MessagesState):
    messages = state["messages"]
    response = model.invoke(messages)
    return {"messages": messages + [response]}

# ---------------------------
# Graph
# ---------------------------
def build_graph(checkpointer):
    g = StateGraph(MessagesState)
    g.add_node("google_model", call_google_node)
    g.add_edge(START, "google_model")
    g.add_edge("google_model", END)
    return g.compile(checkpointer=checkpointer)



# ---------------------------
# Helpers
# ---------------------------
def new_thread_id():
    return f"branch-{uuid.uuid4().hex[:8]}"

def get_next_turn_index(conn, thread_id: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COALESCE(MAX(turn_index), 0) + 1 AS next_turn
            FROM ai_message_checkpoints
            WHERE thread_id = %s
            """,
            (thread_id,)
        )
        return cur.fetchone()["next_turn"]

def store_ai_message_checkpoint(
    conn,
    *,
    thread_id: str,
    ai_message_id: str,
    checkpoint_id: str,
    turn_index: int,
    model_name: str | None = None,
    parent_thread_id: str | None = None,
    parent_ai_message_id: str | None = None,
):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ai_message_checkpoints (
                thread_id,
                ai_message_id,
                checkpoint_id,
                parent_thread_id,
                parent_ai_message_id,
                turn_index,
                model_name
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                thread_id,
                ai_message_id,
                checkpoint_id,
                parent_thread_id,
                parent_ai_message_id,
                turn_index,
                model_name,
            )
        )
    conn.commit()

# ---------------------------
# Fork logic
# ---------------------------
def fork_from_checkpoint(graph, source_thread_id, checkpoint_id):
    state = graph.get_state({
        "configurable": {
            "thread_id": source_thread_id,
            "checkpoint_id": checkpoint_id,
        }
    })

    new_thread = new_thread_id()

    # Seed state ONLY (no lineage written here)
    graph.invoke(
        state.values,
        {"configurable": {"thread_id": new_thread}}
    )

    return new_thread

# ---------------------------
# REPL
# ---------------------------
def repl():
    with PostgresSaver.from_conn_string(POSTGRES_CONN_STRING) as checkpointer:
        graph = build_graph(checkpointer)

        source_thread = input("Source thread_id (Enter for default): ").strip() or "default"
        checkpoint_id = input("Checkpoint ID (Enter for latest): ").strip()

        parent_thread_id = None
        parent_ai_message_id = None

        if checkpoint_id:
            print(f"\nForking from {source_thread} @ {checkpoint_id}")
            active_thread = fork_from_checkpoint(graph, source_thread, checkpoint_id)

            with app_db.cursor() as cur:
                cur.execute(
                    """
                    SELECT ai_message_id
                    FROM ai_message_checkpoints
                    WHERE thread_id = %s AND checkpoint_id = %s
                    """,
                    (source_thread, checkpoint_id)
                )
                parent_ai_message_id = cur.fetchone()["ai_message_id"]

            parent_thread_id = source_thread
        else:
            active_thread = source_thread

        print(f"Active thread: {active_thread}\n")

        config = {"configurable": {"thread_id": active_thread}}

        while True:
            u = input("You: ").strip()
            if u.lower() in ("exit", "quit", "stop"):
                break

            result = graph.invoke(
                {"messages": [HumanMessage(content=u)]},
                config=config
            )

            print("Bot:", result["messages"][-1].content)

            state = graph.get_state(config)
            checkpoint_id = state.config["configurable"]["checkpoint_id"]

            last_ai = state.values["messages"][-1]

            turn_index = get_next_turn_index(app_db, active_thread)

            store_ai_message_checkpoint(
                app_db,
                thread_id=active_thread,
                ai_message_id=last_ai.id,
                checkpoint_id=checkpoint_id,
                turn_index=turn_index,
                model_name="gemini-2.5-flash-lite",
                parent_thread_id=parent_thread_id if turn_index == 1 else None,
                parent_ai_message_id=parent_ai_message_id if turn_index == 1 else None,
            )

if __name__ == "__main__":
    repl()
