import uuid

def new_thread_id():
    return f"branch-{uuid.uuid4().hex[:8]}"

def fork_from_checkpoint(graph, source_thread_id, checkpoint_id):
    state = graph.get_state({
        "configurable": {
            "thread_id": source_thread_id,
            "checkpoint_id": checkpoint_id,
        }
    })

    new_thread = new_thread_id()

    graph.invoke(
        state.values,
        {"configurable": {"thread_id": new_thread}}
    )

    return new_thread
