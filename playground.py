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
    config = {"configurable": {"thread_id": "1"}}

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
        
    print(graph.get_state(config=config))
    

def get_thread_config():
    thread_id = input("Thread ID (press Enter for default): ").strip()
    if not thread_id:
        thread_id = "default"

    print(f"\n🧵 Using thread_id: {thread_id}\n")
    return {"configurable": {"thread_id": thread_id}}


if __name__ == "__main__":
    repl()

