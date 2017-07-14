import json
import psycopg2
from .db_utils import conn as db_conn
from .req_utils import expand_course_options, flatten_relationships
from .course_utils import courses_from_text, courses_for_number_range, course_numbers_for_subject, units_for_course, units_for_course_range, expand_course_number_range
from ...common.tokenizer import match_course_number
from operator import add

def majors_by_id():
  """
  Returns list of tuple for each major (id, name, variant)
  """
  cur = db_conn.cursor()
  cur.execute("SELECT id, name, variant FROM majors ORDER BY name ASC")
  return cur.fetchall()

def expand_major_req_ranges(req_node, parent):
  new_children = list()
  for child in req_node['children']:
    number = child.get('number', None)
    if number:
      number_range = number.split('-')
      if len(number_range) > 1:
        courses = courses_for_number_range(child['subject'], number_range)
        for subject, number in courses:
          course = {
            'subject': child['subject'],
            'number': str(number)
          }
          new_children.append(course)
    else:
      expand_major_req_ranges(child, req_node)

  req_node['children'] += new_children

def compute_major_progress(major_reqs, completed_courses):
  completed_units = 0
  total_major_units = major_reqs['min_units']
  expand_major_req_ranges(major_reqs, None)
  # major reqs fit would well into a max-heap...

  non_override_completions = set()
  def collect_non_override_completions(req_node):
    nonlocal non_override_completions
    try:
      if not req_node['override_units']:
        for child in req_node['children']:
          collect_non_override_completions(child)
    except KeyError:
      course = (req_node['subject'], req_node['number'])
      if course in completed_courses:
        non_override_completions.add(course)

  collect_non_override_completions(major_reqs)

  def calc_node_completion(req_node, is_override):
    try:
      children_by_completed_units = list()
      node_completion = (tuple(), 0, 0)  # ((course, ...), units_completed)
      is_override = is_override or req_node.get('override_units', False)
      for child in req_node['children']:
        if is_override:
          child_completion = calc_node_completion(child, True)
        else:
          child_completion = calc_node_completion(child, False)

        courses, child_units_completed, child_total = child_completion

        if child.get('override_units', False):
          child_total = child['min_units']
          child_completion = (courses, child_units_completed, child_total)

        if req_node['rel'] == 'AND':
          node_completion = (node_completion[0] + courses,
            node_completion[1] + child_units_completed,
            node_completion[2] + child_total)
        else:
          children_by_completed_units.append(child_completion)

      if req_node['rel'] == 'OR' and children_by_completed_units:
        node_completion = max(children_by_completed_units, key=lambda c: (c[1], c[2]))

      return node_completion
    except KeyError:
      course = (req_node['subject'], req_node['number'])
      try:
        course_credit = units_for_course(course[0], course[1])[0]
      except TypeError:
        return (tuple(), 0, 0)

      if course in completed_courses and not (is_override and course in non_override_completions):
        # TODO pull precise count from students_completed_courses table instead of relying on range
        return ((course,),) + (course_credit,) + (course_credit,)
      else:
        return (tuple(), 0, course_credit)

  courses, completion, total = calc_node_completion(major_reqs, False)
  return {
    'courses': courses,
    'units': completion,
    'min': total
  }

def add_major(name, variant):
  cur = db_conn.cursor()
  cur.execute("INSERT INTO majors (name, variant) VALUES (%s, %s)", (name, variant))

def update_major(major_id, name, variant):
  cur = db_conn.cursor()
  cur.execute("UPDATE majors SET name = %s, variant = %s WHERE id = %s", (name, variant, major_id))

def remove_major(major_id):
  cur = db_conn.cursor()
  cur.execute("DELETE FROM majors WHERE id = %s", (major_id,))

def get_major_detail(major_id):
  cur = db_conn.cursor()
  cur.execute("SELECT name, variant, requirements_json FROM majors WHERE id = %s", (major_id,))
  major = cur.fetchone()
  req = flatten_relationships(json.loads(major[2]))

  return major[:2] + (req,)


def get_major_req_json(major_id):
  cur = db_conn.cursor()
  cur.execute("SELECT requirements_json FROM majors WHERE id=%s", (major_id,))
  result = cur.fetchone()[0]
  if not result:
    result = ''
  return result

def floatOrZero(s):
  try:
    return float(s)
  except ValueError:
    return 0.0


def normalize_major_reqs(major_req_json):
  req_tree = json.loads(major_req_json)

    # return True
  expand_course_options(req_tree, None)

  def normalize_node(node, parent):
    try:
      # Group node
      unit_total = (0,0)
      children_unit_range = None
      for child in node['children']:
        child_unit_total = normalize_node(child, node)
        if not child_unit_total:
          continue

        if not children_unit_range:
          children_unit_range = child_unit_total
        else:
          if child_unit_total[0] < children_unit_range[0]:
            children_unit_range = (child_unit_total[0], children_unit_range[1])
          if child_unit_total[1] > children_unit_range[1]:
            children_unit_range = (children_unit_range[0], child_unit_total[1])

        if node['rel'] == 'AND':
          unit_total = tuple(map(add, unit_total, child_unit_total))
      if children_unit_range and unit_total == (0, 0):
        unit_total = children_unit_range

      # If not provided, compute node units
      node['min_units'] = floatOrZero(node['min_units'])
      node['max_units'] = floatOrZero(node['max_units'])
      stored_range = (node['min_units'], node['max_units'])
      if not node['override_units']:
        node['min_units'], node['max_units'] = unit_total
      else:
        unit_total = (node['min_units'], node['max_units'])
      return unit_total
    except KeyError:
      units_for_node = normalize_course_node(node, parent)
      return units_for_node

  normalize_node(req_tree, None)

  return json.dumps(req_tree)

def store_major_req_courses(major_id, normalized_reqs):
  """
  Ensures majors_required_courses corresponds to courses in
  json-serialized 'normalized_reqs' for major under 'major_id'
  """
  course_requirements = set()
  def extract_courses(node, is_hard_requirement):
    nonlocal course_requirements
    try:
      # Group node
      if node['rel'] == 'OR':
        is_hard_requirement = False
      for child in node['children']:
        extract_courses(child, is_hard_requirement)
    except KeyError:
      # Course node
      for number in expand_course_number_range(node['subject'], node['number']):
        course_req = (node['subject'], str(number), is_hard_requirement)
        course_requirements.add(course_req)

  extract_courses(json.loads(normalized_reqs), True)

  cur = db_conn.cursor()
  cur.execute("DELETE FROM majors_required_courses WHERE major_id = %s", (major_id,))

  for course in course_requirements:
    subject, number, is_hard_req = course
    cur.execute("""INSERT INTO majors_required_courses
      (major_id, subject, number, is_hard_requirement)
      VALUES (%s, %s, %s, %s);""", (major_id, subject, number, is_hard_req))

def store_major_reqs(major_id, req_json):
  cur = db_conn.cursor()
  req_json_nrml = normalize_major_reqs(req_json)
  cur.execute("UPDATE majors SET requirements_json = %s WHERE id = %s", (req_json_nrml, major_id))
  store_major_req_courses(major_id, req_json_nrml)
