from langchain_core.messages import HumanMessage
from app.db.postgres import get_app_db
from app.db.langgraph import langgraph_saver
from app.graph.builder import build_graph
from app.services.checkpoints import (
    get_next_turn_index,
    store_ai_message_checkpoint,
)
from app.services.branching import fork_from_checkpoint
from app.config.settings import MODEL_NAME

def repl():
    app_db = get_app_db()

    with langgraph_saver() as saver:
        graph = build_graph(saver)

        source_thread = input("Source thread_id (Enter for default): ").strip() or "default"
        checkpoint_id = input("Checkpoint ID (Enter for latest): ").strip()

        parent_thread_id = None
        parent_ai_message_id = None

        if checkpoint_id:
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

        config = {"configurable": {"thread_id": active_thread}}

        print(f"\nActive thread: {active_thread}\n")

        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ("exit", "quit", "stop"):
                break

            result = graph.invoke(
                {"messages": [HumanMessage(content=user_input)]},
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
                model_name=MODEL_NAME,
                parent_thread_id=parent_thread_id if turn_index == 1 else None,
                parent_ai_message_id=parent_ai_message_id if turn_index == 1 else None,
            )
