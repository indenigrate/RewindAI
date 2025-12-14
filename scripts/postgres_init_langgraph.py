from langgraph.checkpoint.postgres import PostgresSaver
import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_CONN_STRING = (
    f"postgresql://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}"
    f"?sslmode={os.getenv('DB_SSLMODE', 'disable')}"
)

with PostgresSaver.from_conn_string(POSTGRES_CONN_STRING) as saver:
    saver.setup()

print("✅ LangGraph Postgres tables created")
