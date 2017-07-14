from ..common import environment
from ..common.constants import CURRENT_TERM
from ..flaskapp.utils.utils import previous_term, next_term
from ..flaskapp.utils.db_utils import conn
from ..flaskapp.utils.search_utils import instructors_for_query, courses_and_sections_for_search
from ..flaskapp.utils.course_utils import get_course_detail, latest_term_course_offered
from itertools import chain

def populate_instructor_query_cache():
    cur = conn.cursor()
    cur.execute("""SELECT name FROM instructors
        JOIN courses ON courses.instructor_id = instructors.id
            AND term_year = %s AND term_month = %s
        GROUP BY name""", CURRENT_TERM)
    names = cur.fetchall()
    for name in names:
        name = name[0].lower()
        instructors_for_query(name) # full name
        instructors_for_query(name.split()[-1]) # last name

def courses_for_current_term():
    cur = conn.cursor()
    cur.execute("""SELECT subject, number FROM courses
        WHERE term_year = %s and
         term_month = %s
        GROUP BY subject, number""", CURRENT_TERM)
    courses = cur.fetchall()
    return [{'subject': subject, 'number': number} for subject, number in courses]

def populate_course_query_cache(courses):
    for course in courses:
        subj_lower = course['subject'].lower()
        num_lower = course['number'].lower()
        courses_and_sections_for_search({'q': '{}+{}'.format(subj_lower,
            num_lower)}, None, None)
        courses_and_sections_for_search({'q': '{}{}'.format(subj_lower,
            num_lower)}, None, None)


def populate_course_detail_cache(courses):
    for course in courses:
        term = latest_term_course_offered(course['subject'], course['number'])
        get_course_detail(*term, course['subject'], course['number'])

def populate_caches():
    # populate_instructor_query_cache()

    courses = courses_for_current_term()
    populate_course_query_cache(courses)
    populate_course_detail_cache(courses)

if __name__ == '__main__':
    populate_caches()