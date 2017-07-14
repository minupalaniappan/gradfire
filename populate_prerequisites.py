"""
Populates courses.prerequisite_tree with json-serialized representation of courses.prerequisites
Isolated to Winter 2016 courses numbered 0 < number < 200 (lower-div, upper-div)
"""
from daviscoursesearch.common.environment import config
import json
import psycopg2
from daviscoursesearch.scripts.prereq_parser import parse_prereq_text
from daviscoursesearch.flaskapp.utils.db_utils import conn


def main():
  reading_cur = conn.cursor()
  reading_cur.execute("""SELECT DISTINCT ON (subject, number) subject, number, prerequisites FROM courses WHERE term_year = 2016 and term_month = 1 and substring(number, 0, 4)::integer < 200 and prerequisites is not null AND prerequisite_tree is null""")

  for record in reading_cur:
    subject, number, prerequisites = record
    print(subject, number, flush=True)
    try:
      prereq_tree = parse_prereq_text(prerequisites)
    except Exception as e:
      print('exception', repr(e), flush=True)
      continue
    prereq_serialized = ''
    if prereq_tree:
      prereq_serialized = json.dumps(prereq_tree)
    writing_cur = conn.cursor()
    writing_cur.execute("UPDATE courses SET prerequisite_tree = %s WHERE subject = %s AND number = %s AND term_year = 2016 AND term_month = 1", (prereq_serialized, subject, number))
    conn.commit()

if __name__ == '__main__':
  main()
