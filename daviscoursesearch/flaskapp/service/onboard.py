from ..utils import student_utils, user
from ..utils.db_utils import conn
import psycopg2

def is_user_onboarded(user_id):
    cur = conn.cursor()
    cur.execute("SELECT role IS NOT NULL FROM users WHERE id = %s", (user_id,))
    return cur.fetchone()[0]

def process_student_onboard(user_id, transcript, program_ids):
    student_utils.handle_transcript(user_id, transcript)
    try:
        student_utils.add_student_meta(user_id, program_ids)
    except psycopg2.IntegrityError:
        # Student already onboarded; update instead of insert
        student_utils.set_student_programs(user_id, program_ids)

    user.set_role(user_id, 'student')

def process_instructor_onboard(user_id, instructor_id):
    user.set_role(user_id, 'instructor')
    cur = conn.cursor()
    cur.execute("""INSERT INTO courses_instructors
        (user_id, instructor_id)
        VALUES (%s, %s)""", (user_id, instructor_id))

def process_general_onboard(user_id, interested_subjects):
    # TODO setup interested subjects in DB. Every campus affiliated member is welcome
    # to sign up under this
    pass
