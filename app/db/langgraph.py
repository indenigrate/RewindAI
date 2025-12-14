from contextlib import contextmanager
from langgraph.checkpoint.postgres import PostgresSaver
from app.config.settings import POSTGRES_CONN_STRING

@contextmanager
def langgraph_saver():
    with PostgresSaver.from_conn_string(POSTGRES_CONN_STRING) as saver:
        yield saver
