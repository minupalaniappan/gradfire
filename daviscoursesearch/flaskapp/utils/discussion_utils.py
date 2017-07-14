from . import notif_utils as notif
from .db_utils import conn as db_conn
from .student_utils import is_user_verified
from .utils import _subjectNumberPairsForCourses
import html
import json
import psycopg2
import timeago
from datetime import datetime
from flask import url_for
#import dateutil.parser

class DuplicateSubmissionError(Exception):
    pass

class LimitOneError(Exception):
    pass

class UnverifiedUserError(Exception):
    pass

def discourseTeamUserId():
    cur = db_conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = 'team@gradfire.com'")

    return cur.fetchone()[0]

def convert_timestamps(question):
    # str->datetime on timestamps for questions and answers
    # 2016-05-09 16:33:56.096404
    question['timestamp'] = datetime.strptime(question['timestamp'], '%Y-%m-%dT%H:%M:%S.%f')
    #question['timestamp'] = dateutil.parser.parse(question['timestamp']) # fix to avoid using the T in the format
    for answer in question.get('answers', []):
        answer['timestamp'] = datetime.strptime(answer['timestamp'], '%Y-%m-%dT%H:%M:%S.%f')

    return question

def escape_user_content(question):
    if not isinstance(question, dict):
        return question

    for k, v in question.items():
        if isinstance(v, str):
            question[k] = html.escape(v)
        elif isinstance(v, list):
            for item in v:
                escape_user_content(item)

    return question

def add_user_answered(question, user_id):
    if any(answer['user_id'] == user_id for answer in question['answers']):
        question['userAnswered'] = True
    else:
        question['userAnswered'] = False

    return question

def url_for_question(question):
  return url_for('question_thread',
                  subject=question['subject'],
                  number=question['number'],
                  question_id=question['id'])

def url_for_answer(answer, subject, number):
  return url_for('answer',
                  subject=subject,
                  number=number,
                  question_id=answer['question_id'],
                  answer_id=answer['id'])

def add_url_to_question(question):
    question['url'] = url_for_question(question)
    for answer in question.get('answers', []):
        answer['url'] = url_for_answer(answer, question['subject'], question['number'])
    return question

def questions_from_completed_courses(courses, user_id):
    cur = db_conn.cursor()
    questions = list()
    for course in courses:
        if not course.get('subject'):
            continue
        questions += questions_and_answers_for_course(course['subject'], course['number'], user_id)

    return questions


def questionsAskedByUser(user_id):
    return (question_query_for_user_id(user_id, ('q.user_id = %s', user_id)))

def sortAnswersByIsOwner(question):
    question['answers'] = sorted(question['answers'], key=lambda answer: answer['is_owner'])
    return question
def answersGivenByUser(user_id):
    questionsAnswered = question_query_for_user_id(user_id, ('EXISTS (SELECT 1 FROM course_answers a WHERE a.question_id = q.id AND a.user_id = %s AND NOT a.deleted)', user_id))
    return list(map(sortAnswersByIsOwner, questionsAnswered))

def add_answer_count(question):
    question['answer_count'] = len(question['answers'])

    return question

def question_query_for_user_id(user_id, filter_sql_and_values, sort='recent', limit='ALL', offset=0):
    """
    Parameters
    user_id
    filter_sql_and_values tuple of (sql (str), values (list))
    """
    try:
        filter_sql = filter_sql_and_values[0]
        values = filter_sql_and_values[1:]
    except ValueError:
        filter_sql = filter_sql_and_values
        values = []

    sortFields = SORT_FIELDS_BY_TYPE[sort]
    query = """select row_to_json(question_and_answers) as questions from
        (select q.*, coalesce(sum(vote), 0) votes,  (%s = ANY(array_agg(votes.user_id))) user_voted, users.name asker, users.role as role_desc,
        (%s = q.user_id) is_owner,
        (EXISTS (SELECT 1 FROM users_saved_questions saved WHERE saved.user_id = %s AND saved.question_id = q.id)) is_saved,
        (select coalesce(json_agg(ans), '[ ]') from (select a.*, users.name answerer, users.role, users.role as role_desc,
            (%s = ANY(array_agg(voters.id))) user_voted,
            array_remove(array_agg(CASE WHEN voters.role = 'instructor' AND voters.id != a.user_id THEN voters.name ELSE null END), null) endorsements,
            coalesce(sum(vote), 0) votes,
            (a.user_id = %s) is_owner
            from course_answers a
            join users on users.id = a.user_id
            left join course_votes votes on votes.answer_id = a.id
            left join users voters on voters.id = votes.user_id
            where a.question_id = q.id and NOT a.deleted
            group by a.id, users.id
            ORDER BY users.role = 'student', sum(vote)) as ans) as answers
        from course_questions as q
        left join course_votes votes on votes.question_id = q.id
        left join users on users.id = q.user_id
        WHERE {} AND NOT q.deleted
        group by q.id, users.id
        ORDER BY (q.user_id = %s) DESC, {}) question_and_answers
        LIMIT {} OFFSET {};""".format(filter_sql, sortFields, limit, offset)

    cur = db_conn.cursor()
    cur.execute(query, (user_id, user_id, user_id, user_id, user_id, *values, user_id))
    return transformQuestionRows(cur.fetchall(), user_id)

SORT_FIELDS_BY_TYPE = {
    'recent': 'timestamp DESC',
    'votes': 'votable, votes DESC NULLS LAST, timestamp DESC',
    'answers': 'json_array_length(answers), timestamp DESC'
}

def questions_and_answers_for_courses(courses, user_id, sort='recent', limit='ALL', offset=0):
    # TODO add title as another dimension here to allow PE courses...

    subjectNumberPairs = _subjectNumberPairsForCourses(courses)
    return question_query_for_user_id(user_id,
        ("(q.subject || ' ' || q.number) = ANY(%s)", subjectNumberPairs),
        sort=sort,
        limit=limit,
        offset=offset)


def questions_and_answers_for_subject(subject, user_id, sort='recent', limit='ALL', offset=0):
    return question_query_for_user_id(user_id, ('q.subject = %s', subject), sort=sort, limit=limit, offset=offset)

def add_timestamp_ago(timestamped_dict):
    now = datetime.now()
    timestamped_dict['timestamp_ago'] = timeago.format(timestamped_dict['timestamp'], now)
    return timestamped_dict

def add_timestamp_ago_answers(question):
    for answer in question['answers']:
        add_timestamp_ago(answer)
    return question

def transformQuestionRows(questions, userId):
    questions = [convert_timestamps(question[0]) for question in questions]
    questions = [escape_user_content(question) for question in questions]
    questions = [add_user_answered(question, userId) for question in questions]
    questions = [add_url_to_question(question) for question in questions]
    questions = map(add_answer_count, questions)
    questions = map(add_timestamp_ago, questions)
    questions = map(add_timestamp_ago_answers, questions)
    return list(questions)

def answers_for_courses(courses, user_id):
    q = """select coalesce(json_agg(ans), '[ ]') from (select a.*, users.name answerer, users.role, users.role as role_desc,
            (%s = ANY(array_agg(voters.id))) user_voted,
                array_remove(array_agg(CASE WHEN
                    voters.role = 'instructor' AND voters.id != a.user_id
                    THEN voters.name
                    ELSE null END), null) endorsements,
                coalesce(sum(vote), 0) votes,
                q.question question,
                q.subject subject,
                q.number number,
                (a.user_id = %s) is_owner
            from course_answers a
            join users on users.id = a.user_id
            join course_votes votes on votes.answer_id = a.id
            left join users voters on voters.id = votes.user_id
            left join course_questions q on q.id = a.question_id
            where (q.subject || ' ' || q.number) = ANY(%s)
                AND NOT a.deleted
            group by a.id, users.id, q.id
            ORDER BY users.role = 'student', sum(vote)) as ans"""
    cur = db_conn.cursor()
    subjectNumberPairs = _subjectNumberPairsForCourses(courses)
    cur.execute(q, (user_id, user_id, subjectNumberPairs))
    answers = cur.fetchone()[0]
    answers = map(add_timestamp_ago, answers)
    return list(answers)

def questions_and_answers_for_course(subject, number, user_id):
    return questions_and_answers_for_courses([{'subject': subject, 'number': number}], user_id)

def saved_questions_for_user(user_id):
    cur = db_conn.cursor()
    cur.execute("SELECT question_id FROM users_saved_questions WHERE user_id = %s", (user_id,))
    question_ids = [row[0] for row in cur.fetchall()]

    return (question_query_for_user_id(user_id, ('q.id = ANY(%s)', question_ids)))

def store_question(subject, number, term_year, term_month, question, user_id):
    if not is_user_verified(user_id):
        raise UnverifiedUserError()

    cur = db_conn.cursor()
    try:
        cur.execute("""INSERT INTO course_questions AS q (user_id, question, question_escaped, subject, number, term_year, term_month)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING
            (select row_to_json(t) from (
                select
                q.*,
                1 votes,
                true user_voted,
                true is_owner,
                '[]'::json  answers,
                'Just now' timestamp_ago) as t)
            """, (user_id, question.strip(), html.escape(question.strip()), subject, number, term_year, term_month))

    except psycopg2.IntegrityError as e:
        return {'type': 'api_error', 'message': 'You already asked this question'}

    question = cur.fetchone()[0]
    cur.execute("INSERT INTO course_votes (user_id, question_id, vote) VALUES (%s, %s, %s)",
        (user_id, question['id'], 1))

    return question

def userIdOfAsker(questionId):
    # TODO
    pass
def store_answer(question_id, user_id, answer):
    if not is_user_verified(user_id):
        raise UnverifiedUserError()

    cur = db_conn.cursor()
    try:
        cur.execute("""INSERT INTO course_answers (user_id, question_id, answer)
            VALUES (%s, %s, %s)
            RETURNING (select row_to_json(t) from (
                select
                course_answers.*,
                true user_voted,
                1 votes,
                true is_owner,
                'Just now' timestamp_ago) as t)""",
            (user_id, question_id, html.escape(answer.strip())))
    except psycopg2.IntegrityError:
        return {'type': 'api_error', 'message': 'You already answered this question'}

    answer = cur.fetchone()[0]

    questionAskerId = userIdOfAsker(question_id)
    notif.push_notification(questionAskerId,
        notif.NotificationType.answerSaved,
        {'question_id': question_id, 'answer_id': answer['id']})

    cur.execute("INSERT INTO course_votes (user_id, answer_id, vote) VALUES (%s, %s, %s)",
        (user_id, answer['id'], 1))

    return answer

def add_vote(user_id, item_id, item_type):
    cur = db_conn.cursor()
    question_id, answer_id, advice_id = (None, None, None)
    if item_type == 'question':
        question_id = item_id
    elif item_type == 'answer':
        answer_id = item_id
    elif item_type == 'advice':
        advice_id = item_id

    if not (question_id or answer_id or advice_id):
        raise ValueError('Invalid item type')

    data_id_column = item_type + '_id'
    cur.execute("""INSERT INTO course_votes (user_id, question_id, answer_id, advice_id, vote)
        VALUES (%s, %s, %s, %s, %s)""",
        (user_id, question_id, answer_id, advice_id, 1))

def saveQuestion(user_id, question_id):
    cur = db_conn.cursor()
    cur.execute("INSERT INTO users_saved_questions (user_id, question_id) VALUES (%s, %s)",
        (user_id, question_id))

def unsaveQuestion(user_id, question_id):
    cur = db_conn.cursor()
    cur.execute("DELETE FROM users_saved_questions WHERE user_id = %s AND question_id = %s",
        (user_id, question_id))

def deleteQuestion(user_id, question_id):
    cur = db_conn.cursor()
    try:
        cur.execute("UPDATE course_questions SET deleted = true WHERE user_id = %s AND id = %s", (user_id, question_id))
    except psycopg2.IntegrityError:
        cur.execute("DELETE FROM course_questions WHERE id = %s AND user_id = %s", (question_id, user_id))

def deleteAnswer(user_id, answer_id):
    cur = db_conn.cursor()
    try:
        cur.execute("UPDATE course_answers SET deleted = true WHERE user_id = %s AND id = %s", (user_id, answer_id))
    except psycopg2.IntegrityError:
        cur.execute("DELETE FROM course_answers WHERE id = %s AND user_id = %s", (answer_id, user_id))
