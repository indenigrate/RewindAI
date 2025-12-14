import psycopg
from psycopg.rows import dict_row
from app.config.settings import POSTGRES_CONN_STRING

def get_app_db():
    return psycopg.connect(
        POSTGRES_CONN_STRING,
        row_factory=dict_row
    )
