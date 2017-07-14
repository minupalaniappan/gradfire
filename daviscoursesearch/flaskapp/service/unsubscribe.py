from ..utils.db_utils import conn
def unsub(email):
    cur = conn.cursor()
    cur.execute("INSERT INTO unsubscribe (email) VALUES (%s)", (email,))