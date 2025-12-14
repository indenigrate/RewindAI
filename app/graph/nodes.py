from app.models.llm import get_llm
from app.graph.state import State

llm = get_llm()

def call_google_node(state: State):
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": messages + [response]}
