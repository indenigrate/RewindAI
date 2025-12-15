import psycopg
from psycopg.rows import dict_row
from app.config.settings import POSTGRES_CONN_STRING

def get_db():
    conn = psycopg.connect(
        POSTGRES_CONN_STRING,
        row_factory=dict_row,
    )
    try:
        yield conn
    finally:
        conn.close()
