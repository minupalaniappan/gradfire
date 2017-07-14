import json
from .db_utils import conn as db_conn
from enum import Enum

class NotificationType(Enum):
    questionEndorse = 'question_endorsed'
    answerEndorse = 'answer_endorsed'
    answerUser = 'answer_user'
    answerSaved = 'answer_saved'

NOTIFICATION_TEXT_BY_TYPE = {
    NotificationType.questionEndorse: "endorsed your question",
    NotificationType.answerEndorse: "endorsed your answer",
    NotificationType.answerUser: "answered your question",
    NotificationType.answerSaved: "answered a question you saved"
}

DATA_FIELDS_BY_TYPE = {
    NotificationType.questionEndorse: set(['question_id']),
    NotificationType.answerEndorse: set(['question_id', 'answer_id']),
    NotificationType.answerUser: set(['question_id', 'answer_id']),
    NotificationType.answerSaved: set(['question_id', 'answer_id'])
}

def push_notification(user_id, notif_type, data):
    cur = db_conn.cursor()
    if set(data.keys()) != DATA_FIELDS_BY_TYPE[notif_type]:
        raise ArgumentError("Invalid data fields for notification type {}; expected {}".format(data.keys(), DATA_FIELDS_BY_TYPE[notif_type]))
    cur.execute("INSERT INTO notifications (user_id, type, data) VALUES (%s, %s, %s)", (user_id, notif_type.value, json.dumps(data)))


