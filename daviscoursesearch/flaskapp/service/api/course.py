from ...utils.db_utils import conn
from ...utils import course_utils as course
import psycopg2
import json
from ...utils import SchemaEncoder
def update_note(user_id, subject, number, note_json, note_plain):
    cur = conn.cursor()
    cur.execute("""INSERT INTO courses_notes
        (user_id, subject, number, note_json, note_plain)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING
            (select row_to_json(t) from
                (select subject, number, note_json, note_plain)
                as t)
        """, (user_id, subject, number, note_json, note_plain))

    return json.dumps(cur.fetchone()[0], cls=SchemaEncoder)

def get_note(subject, number):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""SELECT note_json FROM courses_notes
        WHERE subject = %s AND number = %s
        ORDER BY timestamp DESC
        LIMIT 1""", (subject, number))

    row = cur.fetchone()
    if row:
        return row[0]
    else:
        return 'null'

def get_grades(subject, number):
    grades = course.grade_stats_for_course(subject, number)
    return sorted(grades, key=lambda grade: (grade['term_year'], grade['term_month']))