import base64
from collections import OrderedDict
from datetime import datetime
from email.utils import parseaddr
from itertools import groupby
import hmac, hashlib
import json
import os
import psycopg2
import psycopg2.extras
from .calendar_utils import add_course_to_calendar
from icalendar import Calendar
import re
import sendgrid
from ...common import config, constants as const
from ...common.logging import exception_logger
from davislib import Term
from ..models.models import CourseQuery, completed_courses_join_tuple
from .utils import window, previous_term, stringify_obj_for_json
from .auth_utils import salt_and_checksum_text, session_token_checksum, random_base64_string
from .db_utils import conn as db_conn
from .course_utils import get_courses, sections_for_query, meetings_course_query, normalize_section_meetings, add_course_from_transcript, url_for_section
from .major_utils import compute_major_progress, get_major_req_json
from itertools import chain
from urllib.parse import quote_plus

class SignupError(Exception):
  pass

class InvalidEmailError(SignupError):
  pass

class InvalidPasswordError(SignupError):
  pass

class InvalidNameError(SignupError):
  pass

class DuplicateUserError(SignupError):
  pass

def set_user_is_verified(user_id):
  cur = db_conn.cursor()
  cur.execute("UPDATE users SET verified = true WHERE id = %s", (user_id,))

def is_user_verified(user_id):
  cur = db_conn.cursor()
  cur.execute("SELECT verified FROM users WHERE id = %s", (user_id,))
  return cur.fetchone()[0]

def verification_code_for_user(user_id):
  cur = db_conn.cursor()
  cur.execute("SELECT verification_code FROM users WHERE id = %s", (user_id,))
  return cur.fetchone()[0]

def send_verification_email(email, name, user_id, code):
  sg = sendgrid.SendGridClient(config.sendgrid_api_key)
  message = sendgrid.Mail()
  message.add_to('{} <{}>'.format(name, email))
  message.set_subject('Verify your account')
  message.set_html(
    """
    {},
    Thank you for signing up for Discourse. Please <a href="https://www.gradfire.com/verify_email?user_id={}&code={}">click here to verify your email</a>.
    """.format(name, user_id, quote_plus(code)))
  message.set_from(config.from_header)
  status, msg = sg.send(message)

def resend_verification_email(user_id):
  user_meta = user_meta_by_id(user_id)
  verification_code = random_base64_string()

  cur = db_conn.cursor()
  cur.execute("UPDATE users SET verification_code = %s WHERE id = %s", (verification_code, user_id))
  send_verification_email(user_meta['email'], user_meta['name'], user_id, verification_code)

def verify_reset_code(user_id, reset_code):
  cur = db_conn.cursor()
  cur.execute("SELECT password_reset_token FROM users WHERE id = %s AND password_reset_token IS NOT NULL", (user_id,))

  return cur.fetchone()[0] == reset_code

def reset_password(user_id, password, password_confirm):
  cur = db_conn.cursor()
  if password != password_confirm:
    raise InvalidPasswordError('Passwords do not match.')
  verify_password(password)
  salt, checksum = salt_and_checksum_text(password)
  cur.execute("UPDATE users SET password_reset_token = null, salt = %s, password_checksum = %s WHERE id = %s", (salt, checksum, user_id))

def send_reset_email(email):
  user_id = user_id_by_email(email)
  user_meta = user_meta_by_id(user_id)
  if not user_meta:
    return

  reset_code = random_base64_string()
  cur = db_conn.cursor()
  cur.execute("UPDATE users SET password_reset_token = %s WHERE id = %s", (reset_code, user_id))

  sg = sendgrid.SendGridClient(config.sendgrid_api_key)
  message = sendgrid.Mail()
  message.add_to('{} <{}>'.format(user_meta['name'], email))
  message.set_subject('Reset your password')
  message.set_html("""
    Someone has requested a password reset on Discourse for {}. If you did not do so, please ignore this email.

    <a href="https://gradfire.com/reset_password?id={}&c={}">Click here to reset your password</a>
    """.format(email, user_id, quote_plus(reset_code)))
  message.set_from(config.from_header)
  status, msg = sg.send(message)

def verify_password(password):
  if len(password) < 8:
    raise InvalidPasswordError('Password length must be at least 8 characters')

  if len(password) > 128:
    raise InvalidPasswordError('Password length must be less than 128 characters')

def add_user_google(token_info):
  cur = db_conn.cursor()
  cur.execute("""INSERT INTO users
    (name, email,  google_id_sub, given_name, family_name, locale, verified)
    VALUES (%(name)s,
      %(email)s,
      %(sub)s,
      %(given_name)s,
      %(family_name)s,
      %(locale)s,
      true)
    RETURNING id;""", token_info)

  return cur.fetchone()[0]

def get_user_role(user_id):
  cur = db_conn.cursor()
  cur.execute("SELECT role FROM users WHERE id = %s", (user_id,))
  return cur.fetchone()[0]

def add_user_email(email, password, name, role, major_ids=None):
  # TODO update for new schema

  parsed_email = parseaddr(email)
  if not parsed_email[1].endswith('@ucdavis.edu'):
    raise InvalidEmailError('Email must end with @ucdavis.edu')

  verify_password(password)

  if not name:
    raise InvalidNameError('Name field is required')

  if role not in const.USER_ROLES:
    raise SignupError('Unknown error')

  salt, checksum = salt_and_checksum_text(password)
  verification_code = random_base64_string()
  cur = db_conn.cursor()
  try:
    cur.execute("""INSERT INTO students
      (name, salt, password_checksum, email, major_ids, verification_code, signup_time, role)
      VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
      RETURNING id""", (name, salt, checksum, email, major_ids, verification_code, datetime.now(), role))
  except psycopg2.IntegrityError:
    raise DuplicateUserError('{} is already registered'.format(email))

  user_id = cur.fetchone()[0]
  send_verification_email(email, name, user_id, verification_code)
  return user_id

def verify_session(user_id, token):
  return token and session_token_checksum(token) in session_token_checksums_for_user(user_id)

def remove_session_token(user_id, token):
  cur = db_conn.cursor()
  cur.execute("UPDATE users SET session_token_checksums = array_remove(session_token_checksums, %s) WHERE id = %s",
    (session_token_checksum(token), user_id))

MAX_SESSION_COUNT = 3
def update_session_token(user_id):
  new_token = random_base64_string()
  token_checksum = session_token_checksum(new_token)

  existing_checksums = session_token_checksums_for_user(user_id)

  if len(existing_checksums) > MAX_SESSION_COUNT:
    # pop last checksum
    token_checksums = [token_checksum] + existing_checksums[:2]
  else:
    token_checksums = [token_checksum] + existing_checksums
  cur = db_conn.cursor()
  cur.execute("UPDATE users SET session_token_checksums = %s WHERE id = %s", (token_checksums, user_id))

  return new_token

def session_token_checksums_for_user(user_id):
  cur = db_conn.cursor()
  cur.execute("SELECT session_token_checksums FROM users WHERE id = %s", (user_id,))
  try:
    return cur.fetchone()[0]
  except TypeError:
    return []

def salt_and_checksum_for_user(user_id):
  cur = db_conn.cursor()
  cur.execute("SELECT salt, password_checksum FROM users WHERE id = %s", (user_id,))
  return cur.fetchone()

def verify_login_with_id(user_id, password):
  stored_salt, stored_checksum = salt_and_checksum_for_user(user_id)
  _, checksum = salt_and_checksum_text(password, salt_text=stored_salt)

  if checksum == stored_checksum:
    return True
  else:
    return False

def verify_login(email, password):
  user_id = user_id_by_email(email)
  if not user_id:
    return False
  return verify_login_with_id(user_id, password)

from .course_utils import get_courses, course_query, add_enrollment_aggregates,  sections_for_query, meetings_course_query, normalize_section_meetings, add_course_from_transcript, url_for_section

def added_courses_for_student(user_id):
  query = CourseQuery(joins=(('JOIN', """students_added_courses sac ON
  sac.subject = courses.subject AND
  sac.number = courses.number AND
  sac.term_year = courses.term_year AND
  sac.term_month = courses.term_month AND
  sac.title = courses.title AND
  sac.student_id = %s""", (user_id, )),))

  query = query.merge(meetings_course_query())
  add_enrollment_aggregates(query)
  sections = course_query(*query.sql_and_values(), omit_sections=True)
  sections = [normalize_section_meetings(section) for section in sections]
  sections_sorted_by_term = sorted(sections, key=lambda section: (section['term_year'], section['term_month']))
  sections_sorted_by_term = [stringify_obj_for_json(section) for section in sections_sorted_by_term]

  return sections_sorted_by_term

def add_course_for_student(user_id, subject, number, title, term_year, term_month):
  cur = db_conn.cursor()
  cur.execute("INSERT INTO students_added_courses (student_id, subject, number, title, term_year, term_month) VALUES (%s, %s, %s, %s, %s, %s)",
    (user_id, subject, number, title, term_year, term_month))

def del_course_for_student(user_id, subject, number, title, term_year, term_month):
  cur = db_conn.cursor()
  cur.execute("DELETE FROM students_added_courses WHERE student_id = %s AND subject = %s AND number = %s AND title = %s AND term_year = %s AND term_month = %s",
    (user_id, subject, number, title, term_year, term_month))

def update_user(user_id, name=None, majors=None, current_password=None, new_password=None):
  cur = db_conn.cursor()
  if majors:
    cur.execute("UPDATE students SET major_ids = %s WHERE user_id = %s", (majors, user_id))

  if new_password:
    if verify_login_with_id(user_id, current_password):
      salt, checksum = salt_and_checksum_text(new_password)
      cur.execute("UPDATE users SET salt = %s, password_checksum = %s WHERE id = %s", (salt, checksum, user_id))
    else:
      raise InvalidPasswordError()

  if name:
    cur.execute("UPDATE users SET name = %s WHERE id = %s", (name, user_id))

def get_all_users():
  cur = db_conn.cursor()
  cur.execute("SELECT id FROM users")
  student_ids = cur.fetchall()
  # TODO use  single query...
  return [user_meta_by_id(uid) for uid in student_ids]

def set_student_programs(user_id, program_ids):
  cur = db_conn.cursor()
  cur.execute("""UPDATE students_programs SET expired = true
    WHERE user_id = %s""", (user_id,))

  for pid in program_ids:
    print(pid)
    try:
      cur.execute("INSERT INTO students_programs (user_id, program_id) VALUES (%s, %s)",
        (user_id, pid))
    except psycopg2.IntegrityError as e:
      cur.execute("""UPDATE students_programs SET expired = false
        WHERE user_id = %s and program_id = %s""", (user_id, pid))

def _add_programs_to_student_meta(student_meta):
  """
  Adds 'majors' field to user_meta dict

  Parameters:
    student_meta:  dict with fields
              'major_ids', 'major_names', 'major_variants'

  Returns: None (student_meta edited in place)
  """
  student_meta['programs'] = [{'id': student_meta['program_ids'][idx],
             'name': student_meta['program_names'][idx],
             'variant': student_meta['program_variants'][idx]}
    for idx in range(len(student_meta['program_ids']))]

  del student_meta['program_ids']
  del student_meta['program_names']
  del student_meta['program_variants']

def add_student_meta(user_id, program_ids, transcript_needs_update=False):
  cur = db_conn.cursor()
  cur.execute("""INSERT INTO students (user_id, transcript_needs_update)
    VALUES (%s, %s)""", (user_id, transcript_needs_update))

  for pid in program_ids:
    cur.execute("INSERT INTO students_programs (user_id, program_id) VALUES (%s, %s)",
      (user_id, pid))


def student_meta_by_user_id(user_id):
  cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
  cur.execute("""
  SELECT
  transcript_needs_update,
  coalesce(
    array_agg(programs.id) FILTER (WHERE programs.id IS NOT NULL),
    ARRAY[]::int[]) program_ids,
  coalesce(
    array_agg(programs.name) FILTER (WHERE programs.name IS NOT NULL),
    ARRAY[]::text[]) program_names,
  coalesce(
    array_agg(programs.variant) FILTER (WHERE programs.variant IS NOT NULL),
    ARRAY[]::text[]) program_variants
  FROM students
  LEFT JOIN students_programs sp ON sp.user_id = students.user_id AND NOT sp.expired
  LEFT JOIN programs ON programs.id = sp.program_id
  WHERE students.user_id = %s
  GROUP BY students.user_id""", (user_id,))

  student_meta = cur.fetchone()
  _add_programs_to_student_meta(student_meta)

  return student_meta

def user_meta_by_id(user_id):
  cur = db_conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
  cur.execute("""SELECT
    users.id,
    users.name,
    role,
    email,
    is_admin,
    verified,
    signup_time,
    (SELECT COUNT(*) FROM course_answers WHERE user_id = %s) answer_count
    FROM users
    WHERE users.id = %s
    GROUP BY users.id""", (user_id, user_id))

  user_meta = cur.fetchone()

  if user_meta:
    user_meta = user_meta._asdict()

    if user_meta['role'] == 'student':
      student_meta = student_meta_by_user_id(user_id)
      user_meta.update(student_meta)

    user_meta['signup_time'] = user_meta['signup_time'].strftime('%s')
    user_meta['intercom_hash'] = hmac.new(config.intercom_secret_key.encode(), str(user_id).encode(), digestmod=hashlib.sha256).hexdigest()

  return user_meta

def user_is_admin(user_id):
  cur = db_conn.cursor()
  cur.execute("SELECT is_admin FROM users WHERE id = %s", (user_id,))
  try:
    return cur.fetchone()[0]
  except TypeError:
    return None

def ge_area_progress(user_id):
  cur = db_conn.cursor()
  cur.execute("""SELECT sgc.ge_area,
      students_ge_progress.units,
      -- For courses:
      array_remove(array_agg(courses.term_year), NULL),
      array_remove(array_agg(courses.term_month), NULL),
      array_remove(array_agg(courses.subject), NULL),
      array_remove(array_agg(courses.number), NULL),
      array_remove(array_agg(courses.title_url_component), NULL),
      -- For course equivalences:
      array_remove(array_agg(sce.term_year), NULL),
      array_remove(array_agg(sce.term_month), NULL),
      array_remove(array_agg(sce.description), NULL)
    FROM students_ge_progress
    JOIN students_ge_courses sgc
      ON sgc.student_id = students_ge_progress.student_id AND sgc.ge_area = students_ge_progress.ge_area
    LEFT JOIN courses ON courses.id = sgc.course_id
    LEFT JOIN students_course_equivalences sce
       ON sce.student_id = students_ge_progress.student_id
       AND sce.id = sgc.course_equivalence_id
    WHERE students_ge_progress.student_id = %s
    GROUP BY sgc.ge_area, students_ge_progress.units""", (user_id,))

  area_totals = {area: {'units': 0, 'courses': []} for area in chain.from_iterable(const.GE_AREAS_BY_CATEGORY.values())}
  for record in cur:
    (area, units,
      course_years, course_months, course_subjects, course_numbers, course_url_components,
      equiv_years, equiv_months, equiv_descriptions) = record
    course_tuples = zip(course_subjects, course_numbers, course_years, course_months,  course_url_components)
    courses = [{'description': '{} {}'.format(subject, number),
      'subject': subject,
      'number': number,
      'term_year': term_year,
      'term_month': term_month,
      'title_url_component': title_url_component}
      for subject, number, term_year, term_month, title_url_component in course_tuples]

    for course in courses:
      try:
        course['url'] = url_for_section(course)
      except KeyError:
        # Course is from transcript and does not have a url
        pass

    courses += [{'description': desc} for desc in equiv_descriptions]
    area_totals[area] = {'units': units, 'courses': courses}

  return area_totals

def impacted_areas_for_course(user_id, course):
  completed_courses, course_equivalences = completed_and_equivalence_courses_for_user(user_id)
  augmented_completed_courses = [(course['id'], course['units_hi'], course['ge_areas'])] + completed_courses

  completed_area_totals = calculate_ge_progress(completed_courses, course_equivalences)
  new_area_totals = calculate_ge_progress(augmented_completed_courses, course_equivalences)
  affected_area_totals = {area: new_area_total for area, new_area_total in new_area_totals.items()
    if new_area_total['units'] != completed_area_totals[area]['units']
      and completed_area_totals[area]['units'] < const.AREA_MINIMUMS[area]}

  return affected_area_totals

def calculate_ge_progress(completed_courses, course_equivalences):
  area_totals, conflicting_records = _ge_completion_initial_sum(completed_courses, course_equivalences)
  _ge_completion_resolve_conflicts(area_totals, conflicting_records)

  return area_totals

def _progress_color(completion):
    if completion < 0.25:
        color = '#bc0000'
    elif completion < 0.5:
        color = '#ffa800'
    elif completion < 0.75:
        color = '#ccff00'
    elif completion < 1:
        color = '#90ff00'
    elif completion == 1:
        color = '#00ab00'
    return color

def ge_completion_by_area(user_id):
  ge_req_progress = ge_area_progress(user_id)

  for area, area_completion in ge_req_progress.items():
    units = area_completion['units']
    courses = area_completion['courses']

    min_units = const.AREA_MINIMUMS[area]
    try:
        min_units = min_units[0]
    except TypeError:
        pass
    completion = float(units) / float(min_units)
    if completion > 1:
        completion = 1

    ge_req_progress[area] = {
      'units': units,
      'min': min_units,
      'completion': completion,
      'color': _progress_color(completion),
      'courses': courses,
      'category': next(cat for cat, areas in const.GE_AREAS_BY_CATEGORY.items() if area in areas)
    }

  return ge_req_progress

def major_completion_by_major_id(user_id):
  major_progress_by_id = student_major_completion(user_id)
  if not major_progress_by_id:
    return None

  for major_id, progress in major_progress_by_id.copy().items():
      completion = 0
      if progress and progress['min'] > 0:
          completion = progress['units'] / progress['min']
          if completion > 1:
              completion = 1
      else:
          completion = 0
      major_progress_by_id[major_id]['completion'] = completion
      major_progress_by_id[major_id]['color'] = _progress_color(completion)

  return major_progress_by_id

def _add_course_to_area_total(course, area_total):
  """
  course: (course_id, units, ge_areas, course_type)
  area_total: {'units': int, 'course_ids': list, 'course_equivalence_ids': list}
  """
  course_id, units, _, course_type = course
  area_total['units'] += units
  if course_type == 'equivalence':
    area_total['course_equivalence_ids'].append(course_id)
  else:
    area_total['course_ids'].append(course_id)

def _ge_area_totals_for_records(records):
  conflicting_records = []
  area_totals = {area: {'units': 0, 'course_ids': [], 'course_equivalence_ids': []}
    for area in const.GE_AREAS}

  for record in records:
    course_id, units, ge_areas, course_type = record
    category_counts = {cat: 0 for cat in const.GE_CATEGORIES}

    for area in ge_areas:
      for category, cat_areas in const.GE_AREAS_BY_CATEGORY.items():
        if area in cat_areas:
          category_counts[category] += 1

    category_conflicts = [cat for cat, count in category_counts.items() if count > 1]
    if category_conflicts:
      conflicting_records.append((category_conflicts, record))

    # Add units for non-conflicting categories
    for clean_category in set(const.GE_CATEGORIES) - set(category_conflicts):
      for area in ge_areas:
        if area in const.GE_AREAS_BY_CATEGORY[clean_category]:
          _add_course_to_area_total(record, area_totals[area])

          if area == 'Domestic Diversity' and 'American Cultures, Governance & History' not in ge_areas:
            _add_course_to_area_total(record, area_totals['American Cultures, Governance & History'])

  return (area_totals, conflicting_records)

def _ge_completion_initial_sum(completed_courses, course_equivalences):
  """
  Returns tuple (
    area_totals: {area: {'units': 0, 'course_ids': [], 'course_equivalence_ids': []}, ...},
    conflicting_records: [(category_conflicts, record), ...]
    )

  by summing GE completion by category and noting conflicts:
    where one course satisfies two GE areas,
    both of which are of the same GE category.

  completed_courses, course_equivalences: List of tuple (id, units, ge_areas)
  """
  completed_courses = [course + ('completed',) for course in completed_courses]
  course_equivalences = [course + ('equivalence',) for course in course_equivalences]

  return _ge_area_totals_for_records(completed_courses + course_equivalences)

def _ge_completion_resolve_conflicts(area_totals, conflicting_records):
  for category_conflicts, record in conflicting_records:
    course_id, units, ge_areas, course_type = record
    for cat in category_conflicts:
      conflicting_areas = list(area for area in ge_areas if area in const.GE_AREAS_BY_CATEGORY[cat])
      min_area = min(conflicting_areas, key=lambda area: area_totals[area]['units'])
      if min_area == 'Domestic Diversity':
        _add_course_to_area_total(record, area_totals['American Cultures, Governance & History'])
      elif min_area == 'American Cultures, Governance & History' and 'Domestic Diversity' in ge_areas:
        _add_course_to_area_total(record, area_totals['Domestic Diversity'])

      _add_course_to_area_total(record, area_totals[min_area])

  return area_totals

def completed_and_equivalence_courses_for_user(user_id):
  """
  Returns tuple (completed_courses, course_equivalences)
  where each element is a list of tuple (id, units, ge_areas)
  """
  cur = db_conn.cursor()
  cur.execute("""SELECT id, scc.units, courses.ge_areas FROM courses
      JOIN students_completed_courses scc ON courses.id = scc.course_id AND
      scc.student_id = %s AND scc.letter_grading WHERE courses.ge_areas IS NOT NULL;""", (user_id,))
  completed_course_units_areas = cur.fetchall()

  cur.execute("""SELECT id, units, ge_areas FROM students_course_equivalences
    WHERE student_id = %s AND ge_areas IS NOT NULL""", (user_id,))
  course_equivalence_units_areas = cur.fetchall()

  return completed_course_units_areas, course_equivalence_units_areas

def store_ge_course(cursor, student_id, ge_area, course_id=None, course_equivalence_id=None):
  try:
    cursor.execute("""INSERT INTO students_ge_courses (student_id, ge_area, course_id, course_equivalence_id)
      VALUES (%s, %s, %s, %s)""",
      (student_id, ge_area, course_id, course_equivalence_id))
  except psycopg2.IntegrityError:
    pass

def store_ge_courses(student_id, ge_area, course_ids, course_equivalence_ids):
  cur = db_conn.cursor()
  course_equivalence_id = None
  for course_id in course_ids:
    store_ge_course(cur, student_id, ge_area, course_id=course_id)
  for course_eqv_id in course_equivalence_ids:
    store_ge_course(cur, student_id, ge_area, course_equivalence_id=course_eqv_id)

def store_ge_progress(user_id):
  completed_courses, equivalence_courses = completed_and_equivalence_courses_for_user(user_id)
  area_totals = calculate_ge_progress(completed_courses, equivalence_courses)

  # completion is marked by individual area minimum met, as well as category minimum met
  cat_totals = {cat: sum(total['units'] for area, total in area_totals.items() if area in cat_areas)
    for cat, cat_areas in const.GE_AREAS_BY_CATEGORY.items()}

  for area, area_total in area_totals.items():

    category = next(category for category, areas in const.GE_AREAS_BY_CATEGORY.items() if area in areas)
    if area_total['units'] >= const.AREA_MINIMUMS[area]:
      if const.CAT_HAS_EXACT_MINIMUM[category] or cat_totals[category] >= const.CAT_MINIMUMS[category]:
        # Topical Breadth category has 52 units required, but its area minimums only sum to 36.
        # So topical breadth does not have an 'exact minimum', and its areas should only be
        # marked as complete if the entire category is complete.
        is_complete = True
    is_complete = False

    cur = db_conn.cursor()
    store_ge_courses(user_id, area, area_total['course_ids'], area_total['course_equivalence_ids'])
    try:
      cur.execute("""
        INSERT INTO students_ge_progress (student_id, ge_area, units, category, is_complete) VALUES (%s, %s, %s, %s, %s)
        """, (user_id, area, area_total['units'], category, is_complete))
    except psycopg2.IntegrityError as e:
      cur.execute("""UPDATE students_ge_progress SET units = %s, is_complete = %s
        WHERE student_id = %s AND ge_area = %s""", (area_total['units'], is_complete, user_id, area))

def user_id_by_email(email):
  cur = db_conn.cursor()
  cur.execute('SELECT id FROM users WHERE email = %s', (email,))
  row = cur.fetchone()
  if row:
    return row[0]

course_fields_and_re = [('term', '^[0-9]{6}$', True),
  ('crn', '^[0-9]{5}$', False),
  ('subject_code', '\(?[A-Z]{3}', True),
  ('number', '(([0-9]{1,3})([A-Za-z]{1,2})?)|TR1\)?', True),
  ('units', '[0-9]\.[0-9]{2}', True),
  ('grade', '[A-Z]([A-Z]|\+|-)?', False)]
# TODO warning for user if missing grade field. it is not a hard requirement but they will need to remove noncompleted courses.

def _parse_transcript_lines(lines):
  """
  Parses provided lines and returns dictionary containing fields parsed from lines.

  Course must be on first line, with an optional GE line provided afterward.
  """
  course = dict()
  token_indices = dict() # indices refer to line_split
  token_idx = 0
  line_split = lines[0].split()

  for field, pattern, is_required in course_fields_and_re:
    for idx in range(token_idx, len(line_split)):
      field_candidate = line_split[idx]
      if re.match(pattern, field_candidate):
        course[field] = field_candidate
        token_indices[field] = idx
        break
    if field in course:
      token_idx = idx
  try:
    course['term'] = Term(course['term'][:4], course['term'][4:])

    if course['subject_code'].startswith('('):
      course['subject_code'] = course['subject_code'][1:]
      course['number'] = course['number'][:-1]
      course['equivalence'] = True
    else:
      course['equivalence'] = False

    title_start_idx = token_indices['number'] + 2
    title_end_idx = token_indices['units']
    course['title'] = ' '.join(line_split[title_start_idx:title_end_idx])
  except KeyError as e:
    return

  for line in lines[1:]:
    line_split = line.split()
    if not line_split[0].startswith('GE'):
      break

    if course and line_split[0] == 'GE3':
      ge_areas_abbrv = line_split[1][1:-1].split(',') # '(AH,QE)'' -> ['AH', 'QE']
      try:
        course['ge_areas'] = [const.GE_AREAS_BY_OASIS_ABBRV[abbrv] for abbrv in ge_areas_abbrv]
      except KeyError:
        print('GE area unknown in {}'.format(ge_areas_abbrv))

  return course


def parse_transcript(transcript_text):
  """
  Returns tuple (completed_courses, tentative_courses, course_equivalences)
  completed_courses: [(course_id int, units int, letter_grading boolean, ), ...]
  tentative_courses: [(course_id int, units int), ...]
  course_equivalences: [
    {
      'term_year': int,
      'term_month': int,
      'subject': code, str,
      'number': str,
      'description': str,
      'units': str,
      'grade': str,
      'course_exists': boolean
    }, ...
  ]
  """
  term = None
  completed_courses = list()
  tentative_courses = list()
  course_equivalences = list()
  transcript_lines = [line.strip() for line in transcript_text.split('\n') if line.strip()]
  for lines in window(transcript_lines, n=3):
    try:
      course = _parse_transcript_lines(lines)
    except Exception as e:
      exception_logger.exception('transcript_line_error')
      continue

    if not course:
      continue
    if 'grade' in course and (course['grade'] == 'NP' or course['grade'] == 'F'): # Don't store non-complete courses
      previous_course_list = None # Ignore GEs for this course
      continue

    if course['equivalence']:
      equivalence = {
        'term_year': course['term'].year,
        'term_month': course['term'].session.value,
        'subject': course['subject_code'],
        'number': course['number'],
        'description': course['title'],
        'units': course['units'],
        'grade': course.get('grade'),
        'ge_areas': course.get('ge_areas')
      }
      try:
        course = next(get_courses(subject=course['subject_code'], number=course['number']))
        equivalence['course_exists'] = True
      except StopIteration:
        equivalence['course_exists'] = False

      course_equivalences.append(equivalence)
    else:
      try:
        course_detail = next(get_courses(term_year=int(course['term'].year),
          term_month=int(course['term'].session.value),
          subject=course['subject_code'],
          number=course['number'],
          title=course['title']))
        course_id = course_detail['id']
      except StopIteration as e:
        try:
          query = CourseQuery(where_conditions=[('subject = %s', course['subject_code']),
            ('number = %s', course['number']),
            ('title = %s', course['title'])],
            order_by=['term_year DESC, term_month DESC'])
          course_detail = sections_for_query(*query.sql_and_values())[0]
          course_id = course_detail['id']
        except IndexError:
          course_id = add_course_from_transcript(course)

      if 'grade' in course and (course['grade'] == 'P' or course['grade'] == 'NP'):
        letter_grading = False
      else:
        letter_grading = True

      record = {'id': course_id,
        'units': re.sub('[^\.0-9]', '', course['units']),
        'letter_grading': letter_grading,
        'letter_grade': course.get('grade'),
        'ge_areas': course.get('ge_areas')}

      if (int(course['term'].year), int(course['term'].session.value)) >= const.CURRENT_TERM:
        tentative_courses.append(record)
      else:
        completed_courses.append(record)

  return (completed_courses, tentative_courses, course_equivalences)

class InvalidTranscriptError(Exception):
  pass

def set_transcript_needs_update(user_id, transcript_needs_update):
  cur = db_conn.cursor()
  cur.execute("UPDATE students SET transcript_needs_update = %s WHERE user_id = %s",
    (transcript_needs_update, user_id))

def handle_transcript(user_id, transcript_text):
  completed_course_ids, tentative_course_ids, course_equivalences = parse_transcript(transcript_text)
  if not (completed_course_ids or tentative_course_ids or course_equivalences):
    raise InvalidTranscriptError(transcript_text)

  cur = db_conn.cursor()
  cur.execute("""
    DELETE FROM students_ge_courses WHERE student_id = %(student_id)s;
    DELETE FROM students_completed_courses WHERE student_id = %(student_id)s AND from_transcript = true;
    DELETE FROM students_tentative_courses  WHERE student_id = %(student_id)s AND from_transcript = true;
    DELETE FROM students_course_equivalences WHERE student_id = %(student_id)s AND from_transcript = true;
    """, {'student_id': user_id})

  for completed_course in completed_course_ids:
    completed_course['student_id'] = user_id
    completed_course['from_transcript'] = True
    try:
      cur.execute("""INSERT INTO students_completed_courses
        (student_id, course_id, letter_grading, letter_grade, units, ge_areas, from_transcript)
        VALUES (%(student_id)s, %(id)s, %(letter_grading)s, %(letter_grade)s, %(units)s, %(ge_areas)s,
        %(from_transcript)s)""", completed_course)
    except psycopg2.IntegrityError as e:
      print(e)
      # Course completion already stored; move along
      pass

  for tentative_course in tentative_course_ids:
    tentative_course['student_id'] = user_id
    tentative_course['from_transcript'] = True
    try:
      cur.execute("""INSERT INTO students_tentative_courses (student_id, course_id, units, ge_areas, from_transcript)
        VALUES (%(student_id)s, %(id)s, %(units)s, %(ge_areas)s, %(from_transcript)s)""", tentative_course)
    except psycopg2.IntegrityError:
      # Duplicate; move on
      pass

  for equivalence in course_equivalences:
    try:
      cur = db_conn.cursor()
      equivalence['student_id'] = user_id
      equivalence['from_transcript'] = True
      cur.execute("""INSERT INTO students_course_equivalences
        (student_id, subject, number, course_exists, description, term_year, term_month, units,
          grade, ge_areas, from_transcript)
        VALUES (%(student_id)s, %(subject)s, %(number)s, %(course_exists)s, %(description)s, %(term_year)s,
          %(term_month)s, %(units)s, %(grade)s, %(ge_areas)s, %(from_transcript)s)""", equivalence)
    except psycopg2.IntegrityError:
      # Equivalence already stored
      pass

  set_transcript_needs_update(user_id, False)

  store_ge_progress(user_id)

def credited_courses_for_user(user_id): # TODO find occurances and change to expect 3-tuple
  """
  Returns list of tuple (subject, number) containing
  all completed and equivalent courses for provided user_id
  """
  cur = db_conn.cursor()
  cur.execute("""SELECT subject, number FROM
    (select subject, number FROM students_course_equivalences WHERE student_id = %s) sce
    UNION
    (SELECT subject, number FROM courses
      JOIN students_completed_courses scc on scc.course_id = courses.id and scc.student_id = %s);
  """, (user_id, user_id))

  return cur.fetchall()

def completed_courses_and_urls(user_id, transfer_courses=True):
  query = CourseQuery(joins=completed_courses_join_tuple(user_id, 'JOIN'))
  query.fields += ('scc.letter_grade',);
  add_enrollment_aggregates(query, user_id=user_id)
  sections = course_query(*query.sql_and_values(), omit_sections=True)
  return sections

# def completed_courses_and_urls(user_id, transfer_courses=True):
#   completed_courses = list()

#   cur = db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
#   cur.execute("""SELECT id, term_year, term_month, subject, number, title, title_url_component, units_hi, courses.ge_areas FROM courses
#     JOIN students_completed_courses scc on scc.course_id = courses.id and scc.student_id = %s
#     ORDER BY term_year DESC, term_month DESC;""", (user_id,))
#   courses = cur.fetchall()
#   for course in courses:
#     completed_courses.append({
#       # 'impacted_areas': list(impacted_areas_for_course(user_id, course).keys()),
#       'course': '{} {}: {}'.format(course['subject'], course['number'], course['title']),
#       'term_year': course['term_year'],
#       'term_month': course['term_month'],
#       'subject': course['subject'],
#       'number': course['number'],
#       'ge_areas': course['ge_areas'],
#       'url': url_for_section(course)
#     })

#   if transfer_courses:
#     cur.execute("SELECT description FROM students_course_equivalences WHERE student_id = %s ORDER BY term_year DESC, term_month DESC", (user_id,))
#     for equivalence in cur.fetchall():
#       completed_courses.append({
#         'course': equivalence['description'],
#         'url': ''
#       })

#   return completed_courses

def url_for_course_if_exists(course, completed_courses):
  try:
    return next(completed['url'] for completed in completed_courses if '{} {}'.format(completed['subject'], completed['number']) == course)
  except StopIteration:
    return ''

def student_major_completion(user_id):
  user_meta = user_meta_by_id(user_id)
  if not user_meta['majors']:
    return None

  major_progress_by_id = dict()
  for major in user_meta['majors']:
    try:
      major_reqs = json.loads(get_major_req_json(major['id']))
      completed_courses = completed_courses_and_urls(user_id)
      progress = compute_major_progress(major_reqs, credited_courses_for_user(user_id))

      progress['courses'] = [' '.join(course) for course in progress['courses']]
      progress['courses'] = [
        {'course': course,
         'url': url_for_course_if_exists(course, completed_courses)}
        for course in progress['courses']]

      major_progress_by_id[major['id']] = progress
    except json.decoder.JSONDecodeError:
      pass

  return major_progress_by_id

def user_progress_is_current(user_id):
  cur = db_conn.cursor()
  cur.execute("""(SELECT term_year, term_month FROM students_completed_courses scc JOIN courses ON scc.course_id = courses.id where student_id = %s ORDER BY term_year desc, term_month desc limit 1)
    UNION
    (SELECT term_year, term_month FROM students_course_equivalences where student_id = %s ORDER BY term_year desc, term_month desc limit 1)""", (user_id, user_id))
  try:
    latest_uploaded_term = max(cur.fetchall())
  except ValueError:
    return False

  return latest_uploaded_term >= previous_term(*const.CURRENT_TERM)

def ical_from_added_courses(user_id, term_year, term_month):
  cal = Calendar()
  added_courses_by_term = added_courses_for_student(user_id)['sections']
  added_courses = added_courses_by_term.get((term_year, term_month))
  if not added_courses:
    return None
  for course in added_courses:
    add_course_to_calendar(cal, course)

  return cal.to_ical()

