from ...utils.db_utils import conn
from ...utils import advice
def advice_is_owned_by_user(user_id, advice_id):
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM course_advice WHERE id = %s", (advice_id,))

    return cur.fetchone()[0] == user_id

def delete_advice(user_id, advice_id):
    advice.deleteAdvice(user_id, advice_id)