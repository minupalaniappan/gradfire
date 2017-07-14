from .db_utils import conn as db_conn
from .utils import unique_everseen, redis_lru, timeit
from itertools import groupby
from ...common import constants as const

def instructor_name_for_id(id):
  cur = db_conn.cursor()
  cur.execute("SELECT name FROM instructors WHERE id=%s", (id,))
  try:
    return cur.fetchone()[0]
  except TypeError:
    return 'TBA'

from .course_utils import get_courses_by_instructor_id

def sort_by_term(courses):
  return sorted(courses, key=lambda course: (course['term_year'], course['term_month']), reverse=True)

def add_is_current_term(courses):
  return [dict(course,
               is_current=(course['term_year'], course['term_month']) == const.CURRENT_TERM)
          for course in courses]

def add_pretty_term(courses):
  return [dict(course,
               pretty_term_month=const.PRETTY_SESSION_BY_MONTH[course['term_month']])
          for course in courses]

def addSugarToCourseList(courses):
  courses = add_is_current_term(courses)
  courses = add_pretty_term(courses)
  return sort_by_term(courses)

@redis_lru()
def courses_taught_by_term(instructor_id):
  courses = get_courses_by_instructor_id(instructor_id)
  courses = sorted(courses, key=lambda course: (course['subject'], course['number'], course['title']))
  course_offerings_by_name = groupby(courses, lambda course: (course['subject'], course['number'], course['title']))
  course_offerings_by_name = map(lambda course_by_name: (course_by_name[0], addSugarToCourseList(course_by_name[1])), course_offerings_by_name)

  return sorted(course_offerings_by_name, key=lambda course_by_name: course_by_name[0])

def most_taught_subject(instructor_id):
  cur = db_conn.cursor()
  cur.execute("""SELECT subject FROM courses
    WHERE instructor_id = %s
    GROUP BY subject
    ORDER BY COUNT(subject) DESC
    LIMIT 1""", (instructor_id,))

  return cur.fetchone()[0]

def teaching_since(instructor_id):
  cur = db_conn.cursor()
  cur.execute("""SELECT term_year, term_month FROM courses
    WHERE instructor_id = %s
    ORDER BY term_year, term_month LIMIT 1""", (instructor_id,))

  return cur.fetchone()
