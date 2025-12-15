import time
from app.db import get_db
from app.workers.conversation_worker import ConversationWorker


def run():
    conn = get_db()
    worker = ConversationWorker(conn)

    print("Conversation worker started")

    while True:
        # In v1, we scan all threads (safe but naive)
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT thread_id FROM events")
            threads = [r["thread_id"] for r in cur.fetchall()]

        for thread_id in threads:
            worker.process_thread(thread_id)

        time.sleep(1)
