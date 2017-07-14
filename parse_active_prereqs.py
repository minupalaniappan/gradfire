from daviscoursesearch.common.environment import config
import json
from daviscoursesearch.flaskapp.utils.db_utils import conn as db_conn
from daviscoursesearch.common.constants import ACTIVE_TERM
from daviscoursesearch.scripts.prereq_parser import parse_prereq_text

def populate_course_prerequisites(node, course_subject, course_id, parent_req_id, cur):
  try:
    cur.execute("""INSERT INTO courses_prerequisites
        (course_id, parent_req, rel)
        VALUES (%s, %s, %s)
        RETURNING id""", (course_id, parent_req_id, node['relationship'].upper()))
    req_id = cur.fetchone()[0]

    for child in node['children']:
      populate_course_prerequisites(child, course_subject, course_id, req_id, cur)
  except TypeError as e:
    subject, number = node
    if subject == 'course':
      subject = course_subject
    cur.execute("""INSERT INTO courses_prerequisites
      (course_id, parent_req, subject, number)
      VALUES (%s, %s, %s, %s)""", (course_id, parent_req_id, subject, number))

def active_courses_lacking_parsed_prereq():
  """
  Returns list of tuple (term_year, term_month, subject, number, prerequisites)
  for all undergraduate courses with term >= ACTIVE_TERM and lacking a stored prerequisite_tree
  """
  cur = db_conn.cursor()
  active_term_year, active_term_month = ACTIVE_TERM
  cur.execute("""SELECT DISTINCT ON (term_year, term_month, subject, number) term_year, term_month, subject, number, prerequisites
    FROM courses
    WHERE term_year >= %s AND term_month >= %s
    AND substring(number, 0, 4)::integer < 200
    AND prerequisites IS NOT NULL AND prerequisite_tree is null""",
    (active_term_year, active_term_month))

  return cur.fetchall()

def main():
  courses_prereqs = active_courses_lacking_parsed_prereq()
  for term_year, term_month, subject, number, prerequisites in courses_prereqs:
    try:
      prereq_tree = parse_prereq_text(prerequisites)
    except Exception as e:
      print('exception', repr(e), flush=True)
      continue

    if not prereq_tree:
      continue

    prereq_serialized = json.dumps(prereq_tree)
    cur = db_conn.cursor()
    cur.execute("""UPDATE courses
      SET prerequisite_tree = %s
      WHERE subject = %s AND number = %s AND term_year = %s AND term_month = %s""",
      (prereq_serialized, subject, number, term_year, term_month))

if __name__ == '__main__':
  main()