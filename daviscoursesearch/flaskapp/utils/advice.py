from .db_utils import conn
from .discussion_utils import escape_user_content, add_timestamp_ago, convert_timestamps
from . import utils
from psycopg2 import IntegrityError

def addAdvice(user_id, subject, number, title, advice):
    cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO course_advice (user_id, subject, number, title, advice)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING (
            select row_to_json(t) from
                (select course_advice.*,
                    1 votes,
                    true user_voted,
                    true is_owner,
                    'Just now' timestamp_ago) as t)""", (user_id, subject, number, title, advice))
        return cur.fetchone()[0]
    except IntegrityError:
        return {'type': 'api_error', 'message': 'You already contributed this advice'}


def deleteAdvice(user_id, advice_id):
    cur = conn.cursor()
    cur.execute("DELETE FROM course_advice WHERE user_id = %s AND id = %s",
        (user_id, advice_id))

def saveAdvice(user_id, advice_id):
    cur = conn.cursor()
    cur.execute("INSERT INTO users_saved_advice (user_id, advice_id)", (user_id, advice_id))

def adviceForCourse(user_id, subject, number, title, sort='recent', limit='ALL', offset=0):
    return _adviceQueryForUserId(user_id,
        ('subject = %s AND number = %s AND title = %s', subject, number, title),
        sort='recent',
        limit=limit,
        offset=offset)

def advice_for_courses(user_id, courses, sort='recent', limit='ALL', offset=0):
    # TODO add title as another dimension here to allow PE courses...

    subjectNumberPairs = utils._subjectNumberPairsForCourses(courses)
    print(subjectNumberPairs)
    return _adviceQueryForUserId(user_id,
        ("(a.subject || ' ' || a.number) = ANY(%s)", subjectNumberPairs),
        sort=sort,
        limit=limit,
        offset=offset)

def advice_given_by_user(user_id, sort='recent', limit='ALL', offset=0):
    return _adviceQueryForUserId(user_id,
        ('user_id = %s', user_id),
        sort=sort,
        limit=limit,
        offset=offset)

def _urlForAdvice(advice):
    pass

def _adviceQueryForUserId(user_id, whereConditions=('true',), sort='recent', limit='ALL', offset=0):
    try:
        filterSql = whereConditions[0]
        values = list(whereConditions[1:])
    except ValueError:
        filter_sql = whereConditions
        values = []

    values = [user_id] + values
    query = """
        SELECT row_to_json(a) advice FROM
        (SELECT id, subject, number, title, advice, timestamp, (%s = user_id) is_owner
        FROM
        course_advice a
        WHERE
        NOT deleted AND {}
        LIMIT {}
        OFFSET {}) as a
        """.format(filterSql, limit, offset)

    cur = conn.cursor()
    cur.execute(query, values)
    print(cur.query)
    advice = [row[0] for row in cur.fetchall()]
    advice = map(convert_timestamps, advice)
    return list(map(add_timestamp_ago, advice))
