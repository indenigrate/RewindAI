from langchain_core.messages import HumanMessage
from app.graph.builder import build_graph
from app.db.langgraph import langgraph_saver


def run_langgraph_from_events(
    *,
    events,
    thread_id: str,
    resume_checkpoint_id: str | None,
):
    """
    Runs the existing LangGraph EXACTLY like repl does,
    but headlessly from the worker.
    """

    # Extract messages from prior events
    messages = []
    for event in events:
        if event.event_type == "UserMessageAdded":
            messages.append(
                HumanMessage(content=event.payload["content"])
            )

    with langgraph_saver() as saver:
        graph = build_graph(saver)

        config = {"configurable": {"thread_id": thread_id}}

        if resume_checkpoint_id:
            config["configurable"]["checkpoint_id"] = resume_checkpoint_id

        result = graph.invoke(
            {"messages": messages},
            config=config
        )

        state = graph.get_state(config)

        last_ai_message = state.values["messages"][-1]
        checkpoint_id = state.config["configurable"]["checkpoint_id"]

        return {
            "ai_message_id": last_ai_message.id,
            "content": last_ai_message.content,
            "checkpoint_id": checkpoint_id,
        }
