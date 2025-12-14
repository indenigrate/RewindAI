import os
import sqlite3
from dotenv import load_dotenv
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver

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
    thread_id = "default"
    config = get_checkpoint_config(thread_id)
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
        checkpoint_id = state.config["configurable"]["checkpoint_id"]
        print(f"🧩 Current checkpoint_id: {checkpoint_id}")
            

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



if __name__ == "__main__":
    repl()

