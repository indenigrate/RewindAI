import os
import sqlite3
from dotenv import load_dotenv
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
import uuid
load_dotenv()

# ---- SQLite (ONE connection per process) ----
conn = sqlite3.connect(
    "checkpoints.sqlite",
    check_same_thread=False
)
checkpointer = SqliteSaver(conn)

# ---- Model ----
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    api_key=os.getenv("GOOGLE_API_KEY"),
)

# ---- Node ----
def call_google_node(state: MessagesState):
    messages = state["messages"]
    response = model.invoke(messages)
    return {"messages": messages + [response]}

# ---- Graph ----
def build_graph():
    g = StateGraph(MessagesState)
    g.add_node("google_model", call_google_node)
    g.add_edge(START, "google_model")
    g.add_edge("google_model", END)
    return g.compile(checkpointer=checkpointer)

# ---- REPL ----
def repl():
    graph = build_graph()

    source_thread = input(
        "Source thread_id (press Enter for default): "
    ).strip() or "default"

    checkpoint_id = input(
        "Checkpoint ID (press Enter for latest): "
    ).strip()

    if checkpoint_id:
        print(
            f"\n🌱 Forking from thread '{source_thread}' "
            f"at checkpoint '{checkpoint_id}'"
        )
        active_thread = fork_from_checkpoint(
            graph,
            source_thread,
            checkpoint_id
        )
        print(f"🧵 New thread created: {active_thread}\n")
    else:
        active_thread = source_thread
        print(f"\n▶️ Continuing thread: {active_thread}\n")

    config = {"configurable": {"thread_id": active_thread}}

    print("Type 'exit' or 'quit' to stop.")
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
        print(
            "🧩 checkpoint_id:",
            state.config["configurable"]["checkpoint_id"],
            "\n"
        )

            

def get_checkpoint_config(thread_id: str):
    checkpoint_id = input(
        "Checkpoint ID (press Enter for latest): "
    ).strip()

    cfg = {"thread_id": thread_id}

    if checkpoint_id:
        cfg["checkpoint_id"] = checkpoint_id
        print(f"\nResuming from checkpoint_id: {checkpoint_id}\n")
    else:
        print("\nResuming from latest checkpoint\n")

    return {"configurable": cfg}

def new_thread_id():
    return f"branch-{uuid.uuid4().hex[:8]}"

def fork_from_checkpoint(graph, source_thread_id, checkpoint_id):
    """
    Load state from (source_thread_id, checkpoint_id),
    create a new thread with that state,
    return new thread_id
    """
    # Load checkpoint state
    source_config = {
        "configurable": {
            "thread_id": source_thread_id,
            "checkpoint_id": checkpoint_id,
        }
    }

    state = graph.get_state(source_config)

    # Generate new thread
    branched_thread_id = new_thread_id()

    # Seed new thread with copied state
    graph.invoke(
        state.values,
        {"configurable": {"thread_id": branched_thread_id}}
    )

    return branched_thread_id

if __name__ == "__main__":
    repl()

