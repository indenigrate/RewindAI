from langgraph.graph import StateGraph, START, END
from app.graph.nodes import call_google_node
from app.graph.state import State

def build_graph(checkpointer):
    g = StateGraph(State)
    g.add_node("google_model", call_google_node)
    g.add_edge(START, "google_model")
    g.add_edge("google_model", END)
    return g.compile(checkpointer=checkpointer)
