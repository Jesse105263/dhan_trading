import psycopg
from psycopg import Connection

from services.config import POSTGRES


def get_connection() -> Connection:
    return psycopg.connect(**POSTGRES)