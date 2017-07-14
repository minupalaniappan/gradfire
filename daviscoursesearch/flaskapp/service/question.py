from ..utils import discussion_utils as discussion

def question_thread_for_question(subject, number, question_id, user_id=None):
    questions = discussion.questions_and_answers_for_course(subject, number, user_id)

    return next(question for question in questions if question['id'] == question_id)

RELATED_QUESTION_COUNT = 10
def related_questions(subject, number, user_id=None):
    return discussion.questions_and_answers_for_subject(subject, user_id, limit=RELATED_QUESTION_COUNT)