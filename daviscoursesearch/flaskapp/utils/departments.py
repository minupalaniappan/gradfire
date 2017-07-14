from .db_utils import conn
import psycopg2
def list_all():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT code, name FROM subjects")

    return cur.fetchall()
