from ..utils.db_utils import conn as db_conn
import json
import psycopg2.extras

NOTIFICATIONS_PER_PAGE = 10
def notifications_for_user(user_id, page=1):
    """
    Returns list of notifications. Dict with two keys, "type" and "data"

     [{"type": "answered",
       "data": {"name": "Sean Davis", "question_id": 1, "answer_id": 1},
       "read": False
       }]
    """
    cur = db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    offset = (page - 1) * NOTIFICATIONS_PER_PAGE
    cur.execute("""SELECT row_to_json(notifications)
        FROM notifications
        WHERE user_id = %s
        ORDER BY read DESC
        LIMIT %s
        OFFSET %s""", (user_id, NOTIFICATIONS_PER_PAGE, offset))
    notif_rows = cur.fetchall()
    return [row[0] for row in notif_rows]
