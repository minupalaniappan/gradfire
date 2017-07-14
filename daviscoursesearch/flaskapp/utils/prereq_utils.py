from .db_utils import conn as db_conn
from .req_utils import expand_course_options, flatten_relationships, normalize_course_node
from .course_utils import get_serialized_prereqs, get_courses
import json
from ...common.logging import exception_logger

def deletePrereqs(subject, number, term_year, term_month):
    cur = db_conn.cursor()
    cur.execute("""DELETE FROM courses_prerequisites WHERE subject = %s AND
        number = %s and term_year = %s and term_month = %s""", (subject, number, term_year, term_month))

def normalizeCourses(node, parent=None):
    try:
        for child in node['children']:
            normalizeCourses(child, node)
    except KeyError:
        normalize_course_node(node, parent)

def reqDictFromJson(req_json):
    reqs = json.loads(req_json)
    expand_course_options(reqs)
    flatten_relationships(reqs)
    normalizeCourses(reqs)

    return reqs

def store_prereq_json(subject, number, term_year, term_month, req_json):
    old_req_json = get_serialized_prereqs(subject, number, term_year, term_month)
    cur = db_conn.cursor()
    deletePrereqs(subject, number, term_year, term_month)
    course_ids = [section['id'] for section in get_courses(subject=subject, number=number,
        term_year=term_year, term_month=term_month)]
    try:
        normalizedReqs = reqDictFromJson(req_json)
        if not normalizedReqs['children']:
            return
        for course_id in course_ids:
            store_prerequisites(normalizedReqs, course_id, subject, number, term_year, term_month, None, cur)
        return json.dumps(normalizedReqs) # for frontend update
    except Exception as e:
        # Restore prereqs on exception so old data is not lost
        deletePrereqs(subject, number, term_year, term_month)
        if old_req_json:
            for course_id in course_ids:
                store_prerequisites(reqDictFromJson(old_req_json), course_id, subject, number, term_year, term_month, None, cur)
        raise e

def store_prerequisites(node, course_id, subject, number, term_year, term_month, parent_req_id, cur):
  try:
    cur.execute("""INSERT INTO courses_prerequisites
        (course_id, subject, number, term_year, term_month, parent_req, rel)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id""", (course_id, subject, number, term_year, term_month, parent_req_id, node['rel'].upper()))
    req_id = cur.fetchone()[0]

    for child in node['children']:
      store_prerequisites(child, course_id, subject, number, term_year, term_month, req_id, cur)

  except KeyError:
    if node['subject'] == 'course':
      node['subject'] = subject # 'course' is used when the prerequisite is the
                            # same subject as requiring course
    cur.execute("""INSERT INTO courses_prerequisites
      (course_id, subject, number, term_year, term_month, parent_req, req_subject, req_number)
      VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", (course_id, subject, number, term_year, term_month, parent_req_id,
        node['subject'], node['number']))
