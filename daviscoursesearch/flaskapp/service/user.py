from ...flaskapp.utils.db_utils import conn
from ...common.constants import CURRENT_TERM
from ...flaskapp.utils.utils import previous_term
from ..utils import student_utils as student

def transcript_is_outdated(user_id):
    cur.execute("""SELECT term_year, term_month
        FROM students_completed_courses scc
        JOIN courses ON courses.id = scc.course_id
        WHERE student_id = %s
        ORDER BY term_year DESC, term_month DESC
        LIMIT 1""",
        (user_id,))

    latest_transcript_term = cur.fetchone()

    return ((not latest_transcript_term)
            or
            (latest_transcript_term < previous_term(*CURRENT_TERM)))


# add flag transcript_outdated to students table
# on new quarter start, reset all students to False
# prompt student "Did you take classes in the Spring? Yes/No"
# No -> transcript_outdated = False
# Yes -> Transcript upload -> transcript_outdated = True

from ..utils import student_utils as student

def update_student(user_id, transcript, programs):
    student.set_student_programs(user_id, programs)
    student.handle_transcript(user_id, transcript)