import json
import psycopg2
from daviscoursesearch.flaskapp.utils.db_utils import conn
import daviscoursesearch.common.environment as env

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

def main():
  cur = conn.cursor()
  cur.execute("SELECT id, subject, prerequisite_tree FROM courses WHERE prerequisite_tree IS NOT NULL AND NOT EXISTS (SELECT 1 FROM courses_prerequisites WHERE course_id = courses.id)")
  for record in cur:
    course_id, subject, prereq_json = record
    prereq_tree = json.loads(prereq_json)
    populate_course_prerequisites(prereq_tree, subject, course_id, None, conn.cursor())

if __name__ == '__main__':
  main()