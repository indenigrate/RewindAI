import time
from app.db.postgres import get_app_db
from app.workers.conversation_worker import ConversationWorker


def run():
    worker = ConversationWorker()
    print("Conversation worker started")

    while True:
        print("Scanning for threads with new messages...")
        
        try:
            with get_app_db() as conn:
                # In v1, we scan all threads (safe but naive)
                with conn.cursor() as cur:
                    cur.execute("SELECT DISTINCT thread_id FROM events")
                    threads = [r["thread_id"] for r in cur.fetchall()]
                
                print(f"Found {len(threads)} active threads.")
                for thread_id in threads:
                    worker.process_thread(conn, thread_id)
        except Exception as e:
            print(f"❌ Error in conversation worker run loop: {e}")


        time.sleep(1)

if __name__ == "__main__":
    run()
