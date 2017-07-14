from .db_utils import conn
def set_role(user_id, role):
    cur = conn.cursor()
    cur.execute("UPDATE users SET role = %s WHERE id = %s",
        (role, user_id))