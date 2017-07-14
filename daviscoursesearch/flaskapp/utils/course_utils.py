from collections import OrderedDict
from .db_utils import conn as db_conn
from . import utils
from ..models.models import CourseQuery, FilterConditions, completed_courses_join_tuple
from ...common import constants as const
from ...common import config
from ...common import logging
from flask import url_for
from datetime import datetime
from itertools import groupby, chain
from math import ceil
from operator import itemgetter
import json
import re
import psycopg2
import sys
import time

def subjectsWithPrequisitesForTerm(term_year, term_month):
  cur = db_conn.cursor()
  cur.execute("""SELECT subject FROM courses
    WHERE term_year = %s AND term_month = %s AND prerequisites IS NOT NULL
      AND substring(number, 0, 4)::integer < 200
    GROUP BY subject
    ORDER BY subject""", (term_year, term_month))
  return [row[0] for row in cur.fetchall()]

def normalize_child(child, prereqs):
    if child['req_subject']:
        return {'subject': child['req_subject'], 'number': child['req_number']}
    else:
        try:
          children = next(group for group in prereqs if group[0]['parent_req'] == child['id'])
          children = [normalize_child(child, prereqs) for child in children]
        except StopIteration:
          children = []
        return {'rel': child['rel'], 'children': children}

def get_serialized_prereqs(subject, number, term_year, term_month):
    cur = db_conn.cursor()
    cur.execute("""SELECT json_agg(prereq) FROM (SELECT * from courses_prerequisites
        WHERE subject = %s and number = %s and term_year = %s and term_month = %s) AS prereq GROUP BY parent_req
        ORDER BY parent_req DESC""", (subject, number, term_year, term_month))
    groups = [row[0] for row in cur.fetchall()]
    if groups:
        return json.dumps(normalize_child(groups[0][0], groups)) # root is always first group with 'ORDER BY parent_req DESC'
    else:
        return json.dumps({'rel': 'AND', 'children': []})

def add_average_grade_to_course_query(course_query, term_sensitive=False):
  subquery_condition = "WHERE cg.subject = courses.subject and cg.number = courses.number and letter != 'P' AND letter != 'NP'"
  if term_sensitive:
    subquery_condition += " AND cg.term_year = courses.term_year AND cg.term_month = courses.term_month"

  course_query.fields += ('avg_grade.letter avg_grade_letter', 'avg_grade.avg_grade_order')
  course_query.joins += (('left join lateral', """(select subject, number, avg_grade_order, (select letter from courses_grades
              where grade_order = round(avg_grade_order) limit 1) letter FROM
                (SELECT subject, number, (sum(grade_order * count)::float / sum(count)) avg_grade_letter
                  FROM courses_grades cg
                  {0} group by cg.subject, cg.number)
                as cg(subject, number, avg_grade_order)) avg_grade ON true""".format(subquery_condition)),)

def url_for_section(section):
  title = None
  if section['subject'] == 'PHE' and section['number'] == '001':
    title = section['title_url_component']
  return url_for('course',
    subject=section['subject'],
    number=section['number'],
    title=title)

def get_courses_by_instructor_id(instr_id):
  valid_term_months = ','.join([str(month) for month in const.TERM_SESSION_BY_MONTH.keys()])
  cq = CourseQuery(where_conditions=[('instructor_id = %s', instr_id)],
    order_by=('term_year, term_month, subject, number, title',))
  add_average_grade_to_course_query(cq, term_sensitive=True)
  courses = course_query(*cq.sql_and_values())

  return courses

from .instructor_utils import instructor_name_for_id

def add_course_from_transcript(parsed_course):
  cur = db_conn.cursor()
  units = parsed_course.get('units')
  if units:
    units = float(units)

  fields = (parsed_course['term'].year,
    parsed_course['term'].session.value,
    parsed_course.get('crn'),
    parsed_course.get('subject_code'),
    parsed_course.get('number'),
    parsed_course.get('title'),
    units,
    units,
    parsed_course.get('ge_areas'))

  cur.execute("""INSERT INTO courses
    (term_year, term_month, crn, subject, number, title, units_low, units_hi, ge_areas, from_transcript)
    VALUES
    (%s, %s, %s, %s, %s, %s, %s, %s, %s, true) RETURNING id""", fields)
  return cur.fetchone()[0]

def course_numbers_for_subject(subject, min_number=None, max_number=None):
  cur = db_conn.cursor()
  query = "SELECT DISTINCT(number) FROM courses WHERE subject = %s"
  if min_number:
    query += " AND substring(number, 0, 4)::integer => %s"
  if max_number:
    query += " AND substring(number, 0, 4)::integer <= %s"

  cur.execute(query, (subject, min_number, max_number))
  return [row[0] for row in cur.fetchall()]

def units_for_course(subject, number):
  """
  Returns unit range: (low, hi)
  """
  cur = db_conn.cursor()
  cur.execute("""SELECT COALESCE(units_low, units_hi), COALESCE(units_hi, units_low) FROM courses
    WHERE subject = %s AND number = %s AND (units_low IS NOT NULL OR units_hi IS NOT NULL) AND  NOT from_transcript
    ORDER BY term_year DESC, term_month DESC LIMIT 1""", (subject, number))
  row = cur.fetchone()
  if row:
    return tuple([float(units) for units in row])
  else:
    return None

def courses_for_number_range(subject, number_range):
  cur = db_conn.cursor()

  cur.execute("""SELECT DISTINCT number FROM courses
    WHERE subject = %s and
      substring(number, 0, 4)::integer <@ int4range(%s, %s)
      AND NOT from_transcript
  """, (subject, int(number_range[0]), int(number_range[1])))
  return [(subject, number) for number in cur.fetchall()]

def units_for_course_range(subject, course_range):
  cur = db_conn.cursor()
  cur.execute("""SELECT min(units_low), max(units_hi) FROM courses
    WHERE subject = %s and substring(number, 0, %s) >= %s AND substring(number, 0, %s) <= %s
    AND NOT from_transcript""",
    (subject, len(course_range[0]) + 1, course_range[0], len(course_range[1]) + 1, course_range[1]))
  try:
    return tuple([float(units) for units in cur.fetchone()])
  except TypeError:
    return None

def correct_available_seats(available_seats, waitlist_length):
  if waitlist_length and waitlist_length > 0 and available_seats > 0:
    available_seats = available_seats - waitlist_length
    if available_seats < 0:
      available_seats = 0

  return available_seats

def alternative_sections_for_course(course):
  query = CourseQuery(where_conditions=(
      ('term_year = %s', course['term_year']),
      ('term_month = %s', course['term_month']),
      ('subject = %s', course['subject']),
      ('number = %s', course['number']),
      ('title = %s', course['title']),
      ('crn != %s', course['crn'])
      ))
  query = query.merge(meetings_course_query())
  sections = sections_for_query(*query.sql_and_values())
  return [normalize_section_meetings(section) for section in sections]

def sections_for_query(query, *args, **kwargs):
  cur = db_conn.cursor()
  try:
    cur.execute(query, *args, **kwargs)
    if config.debug:
      print(cur.query.decode('utf-8'))
  except psycopg2.Error as e:
    if config.debug:
      print(cur.query.decode('utf-8'))
    raise e

  columns = [column[0] for column in cur.description]
  sections = [{columns[i]: record[i] for i in range(0, len(columns))} for record in cur.fetchall()]
  for section in sections:
    section['instructor'] = instructor_name_for_id(section['instructor_id'])
    section['available_seats'] = correct_available_seats(section['available_seats'], section['waitlist_length'])
    del section['title_desc_tsv']
    if section.get('prerequisite_tree'):
      del section['prerequisite_tree']
    try:
      section['url'] = url_for_section(section)
    except RuntimeError as e:
      if config.debug:
        logging.exception_logger.exception('Non-fatal exception assigning url to section id {}'.format(section['id']))

  return sections

def honors_equivalents(subject, number):
  number, letters = (number[:3], number[3:])
  equivalences = list()
  cur = db_conn.cursor()
  query = """SELECT DISTINCT(number) FROM courses WHERE subject = %(subject)s AND substring(number, 0, 4) = %(number)s
    AND (
      (substring(number, 4, 1) = 'H' AND substring(number, 5) = %(letters)s) -- PHY 009HA
      OR -- OR conditions: the sign of complexity
      (substring(number, 5) = 'H' and substring(number, 4, 1) = %(letters)s)) -- CHE 002AH
    """
  cur.execute(query, {'subject': subject, 'number': number, 'letters': letters})

  equivalences = [{'subject': subject, 'number': row[0]} for row in cur.fetchall()]

  return equivalences

def course_metadata_for_term(term_year, term_month, subject, limit='ALL', offset=0):
  cq = CourseQuery(where_conditions=[('prerequisites IS NOT NULL',),
    ('term_year = %s AND term_month = %s AND subject = %s', term_year, term_month, subject),
    ('subject IS NOT NULL AND NOT from_transcript',)],
    limit=limit,
    offset=offset)
  courses = course_query(*cq.sql_and_values(), sort=True)
  for course in courses:
    course['prerequisite_tree'] = get_serialized_prereqs(course['subject'], course['number'],
      course['term_year'], course['term_month'])
  return courses

def course_query(query, *args, sort=False, omit_sections=False, **kwargs):
  """
  For grouping to occur, query must be ordered by
  term_year, term_month, subject, number, title
  or provide sort=True.
  """
  sections = sections_for_query(query, *args, **kwargs)
  if sort:
    sections = sorted(sections, key=lambda section: (section['term_year'], section['term_month'], section['subject'], section['number'], section['title']))

  sections_by_course = groupby(sections, lambda section: (section['term_year'], section['term_month'], section['subject'], section['number'], section['title']))
  courses = list()
  for course, sections in sections_by_course:
    course = {
      'sections': []
    }
    first_section = next(sections)
    for column, value in first_section.items():
      course[column] = value
    # TODO create explicit mappings of course  cols / sectin colds
    # or maybe this hints courses should be split into 2 tables, courses and sections
    if not omit_sections:
      del course['instructor_id']
      del course['available_seats']
      del course['max_enrollment']
      del course['crn']

    try:
      number = int(course['number'][:3])
      if number < 100:
        course['lower_division'] = True
        course['upper_division'] = False
      elif number < 200:
        course['upper_division'] = True
        course['lower_division'] = False
    except ValueError:
      course['lower_divison'] = course['upper_division'] = False

    if not omit_sections:
      for section in chain((first_section,), sections):
        course['sections'].append(section)

    try:
      course['total_available_seats'] = correct_available_seats(
        course['total_available_seats'],
        course['total_waitlist_length'])
    except KeyError:
      pass

    course['units_frmt'] = utils.format_units(course['units_low'], course['units_hi'])
    courses.append(course)

  return courses

# Postgres 9.5 query planner no longer performs a smart join w/ subquery,
# so in addition to joining on fields, we must add a where condition
# to avoid a full table sort on courses...
AGG_UNIQUE_COURSE_CONDITIONS = """agg.subject = courses.subject AND agg.number = courses.number
      AND agg.title = courses.title
      AND agg.term_year = courses.term_year
      AND agg.term_month = courses.term_month"""
def add_enrollment_aggregates(course_query, user_id=None):
  """
  Aggregates course query to class level from section level. Any WHERE conditions in the provided
  course_query are added onto a new JOIN which performs the aggregation.
  Conditions that refer to an aggregate are preserved in the original course query
  """
  where_conditions_non_agg = [condition for condition in course_query.where_conditions if 'courses.' in condition[0]]
  if any('tsquery' in join[0] for join in course_query.joins):
    where_conditions_non_agg += ('ts_rank(title_desc_tsv, tsquery) > 1e-20',)
  where_conditions_aggregate = [condition for condition in course_query.where_conditions if condition not in where_conditions_non_agg]
  sql_conditions_non_agg = list(map(itemgetter(0), where_conditions_non_agg))
  sql_conditions_non_agg = [sql.replace('courses.', 'agg.') for sql in sql_conditions_non_agg] + [AGG_UNIQUE_COURSE_CONDITIONS]
  where_conditions_lateral_join = 'WHERE {}'.format(' AND '.join(sql_conditions_non_agg)) if sql_conditions_non_agg else ''
  existing_values = [condition[1:] for condition in where_conditions_non_agg if isinstance(condition, tuple) and len(condition) > 1]
  existing_values = list(chain(*existing_values))

  course_query.where_conditions = where_conditions_aggregate
  course_query.fields += ('COALESCE(total_max_enrollment, 0) total_max_enrollment',
    'total_available_seats',
    'total_waitlist_length',
    'unanswered_question_count',
    'answer_count')

  course_query.joins += (
    ('JOIN LATERAL', """(SELECT subject, number, title, term_year, term_month,
      SUM(max_enrollment) total_max_enrollment,
      SUM(waitlist_length) total_waitlist_length,
      SUM(available_seats) total_available_seats,
      (SELECT count(*) FROM course_answers a
        JOIN course_questions q ON q.id = a.question_id
        AND q.subject = courses.subject AND q.number = courses.number) answer_count,
      (SELECT count(*) FROM course_questions q
         WHERE NOT deleted
         AND NOT EXISTS (SELECT 1 FROM course_answers a WHERE a.question_id = q.id)
         AND subject = agg.subject AND number = agg.number) unanswered_question_count
    FROM courses agg
    {}
    GROUP BY term_year, term_month, subject, number, title) course_agg
    ON course_agg.subject = courses.subject
    AND course_agg.number = courses.number
    AND course_agg.title = courses.title
      AND course_agg.term_year = courses.term_year
      AND course_agg.term_month = courses.term_month""".format(where_conditions_lateral_join), *existing_values),)

  # Remove all where conditions except aggregates
  if course_query.group_by:
    course_query.group_by += ('total_max_enrollment', 'total_available_seats', 'total_waitlist_length',
     'unanswered_question_count', 'answer_count')

def average_grade_from_avg_order(avg_order):
  return next(letter for letter, order in const.GRADE_ORDER_BY_LETTER.items()
    if order > avg_order)

def average_grade(letters, counts):
  try:
    y_idx = letters.index('Y')
    letters = letters[:y_idx] + letters[y_idx +1:]
    counts = counts[:y_idx] + counts[y_idx+1:]
  except ValueError:
    pass

  letter_orders = chain(*[[const.GRADE_ORDER_BY_LETTER[letter] for occurance in range(counts[idx])]
    for idx, letter in enumerate(letters)])
  letter_orders = list(letter_orders)

  order_mean = sum(letter_orders) / len(letter_orders)
  avg_letter, avg_order = next((letter, order) for letter, order in const.GRADE_ORDER_BY_LETTER.items()
    if order == round(order_mean))

  if avg_letter not in letters:
    counts_by_letter = {letters[i]: counts[i] for i in range(len(counts))}
    left_sum = sum([count for letter, count in counts_by_letter.items()
      if const.GRADE_ORDER_BY_LETTER[letter] < avg_order])
    right_sum = sum([count for letter, count in counts_by_letter.items()
      if const.GRADE_ORDER_BY_LETTER[letter] > avg_order])

    if left_sum >= right_sum:
      order_by_letter_desc = list(const.GRADE_ORDER_BY_LETTER.items())
      order_by_letter_desc.reverse()
      order_by_letter_desc = OrderedDict(order_by_letter_desc)

      avg_letter = next(letter for letter, order in order_by_letter_desc.items()
        if order < avg_order)
    else:
      avg_letter = next(letter for letter, order in const.GRADE_ORDER_BY_LETTER.items()
        if order > avg_order)

  return avg_letter

@utils.redis_lru()
def grade_stats_for_course(subject, number):
  cur = db_conn.cursor()
  cur.execute("""SELECT term_year, term_month,
    instructors.name,
    array_agg(letter ORDER BY grade_order),
    array_agg(count ORDER BY grade_order)
    FROM courses_grades
    JOIN instructors ON instructors.id = courses_grades.instructor_id
    WHERE subject = %s AND number = %s
    AND letter != 'H' AND letter != 'I' AND letter != 'IP' AND letter != 'NG' AND letter != 'RD' AND letter != 'S' AND letter != 'U' AND letter != 'W04'
    GROUP BY term_year, term_month, instructors.name ORDER BY term_year DESC, term_month DESC""", (subject, number))

  rows = cur.fetchall()
  rows = [
    OrderedDict([
      ('term_year', row[0]),
      ('term_month', row[1]),
      ('pretty_term_month', const.PRETTY_SESSION_BY_MONTH[row[1]]),
      ('instructor', row[2]),
      ('letters', row[3]),
      ('counts', row[4]),
      ('distributions', [float(100 * count / sum(row[4])) for count in row[4]]),
      ('avg_letter_grade', average_grade(row[3], row[4]))
      ])
    for row in rows]

  return rows

def meetings_course_query():
  meetings_query = CourseQuery(
    joins=(('JOIN', 'meetings ON meetings.course_id = courses.id'),),
    fields=("""array_to_json(array_agg(row(to_char(meetings.start_time, 'FMHH:MI AM'), to_char(meetings.end_time, 'FMHH:MI AM'), meetings.location,
    meetings.type, meetings.monday, meetings.tuesday, meetings.wednesday, meetings.thursday, meetings.friday,
    meetings.saturday))) meetings""",),
    group_by=('courses.id',))

  return meetings_query

def meeting_time_to_int(meeting_time):
  hour, minutes_and_meridian = meeting_time.split(':')
  minutes, meridian = minutes_and_meridian.split()
  hour = int(hour)
  minutes = int(minutes)

  if meridian == 'PM' and hour != 12:
    return (hour + 12) * 60 + minutes
  else:
    return hour * 60 + minutes

DAYS = ['M', 'T', 'W', 'R', 'F', 'S']
def normalize_section_meetings(section):
  section['meetings'] = [
    [value for key, value in sorted(meeting.items(), key=lambda tpl: int(tpl[0][1:]))]
    for meeting in section['meetings']] # strips dummy column names ('f1', 'f2', ...) while preserving column order.
  section['meetings'] = [
    {'start_time': meeting[0],
     'end_time': meeting[1],
     'location': meeting[2],
     'type': meeting[3],
     'prettyType': const.PRETTY_MEETING_TYPE_BY_CODE.get(meeting[3], meeting[3]),
     'days': [DAYS[idx] for idx in range(6) if meeting[idx + 4]] # days in result set are offset by 3 elements
    }

    for meeting in section['meetings']]

  for meeting in section['meetings']:
    if meeting['start_time'] and meeting['end_time']:
      meeting['start_time_minutes'] = meeting_time_to_int(meeting['start_time'])
      meeting['end_time_minutes'] = meeting_time_to_int(meeting['end_time'])
    else:
      meeting['start_time_minutes'] = 1441 # 24 hours + 1 minute

  section['meetings_sorted_time'] = sorted(section['meetings'], key=lambda meeting: meeting['start_time_minutes'])
  return section

MAX_SAMPLES = 100
def reduce_enrollment_samples_to_day(enrollment_samples):
  """
  TODO equate samples per day to ensure even sample distribution,
  which supports even chart labels
  """
  seen = set()
  step = int(len(enrollment_samples) / MAX_SAMPLES)
  if step < 1:
    return enrollment_samples
  reduced_samples = enrollment_samples[0::step]
  return reduced_samples + [sample for sample in enrollment_samples[-5:] if sample not in reduced_samples]
  # last_samples = enrollment_samples[-5:]
  # sample_per_day = [seen.add(sample['date']) or sample for sample in enrollment_samples if sample['date'] not in seen]
  # return sample_per_day + [sample for sample in last_samples if sample not in sample_per_day]

def enrollment_samples_for_course(term_year, term_month, subject, number):
  cur = db_conn.cursor()
  dropDeadline = const.DROP_DEADLINE_BY_TERM.get((term_year, term_month))
  timestampCutoff = sys.maxsize
  if dropDeadline:
    timestampCutoff = time.mktime(dropDeadline.timetuple())
    print(timestampCutoff)
  cur.execute("""SELECT timestamp, available_seats, enrolled_seats, waitlist_length FROM courses_enrollment
    WHERE term_year = %s AND term_month = %s AND subject = %s AND number = %s AND timestamp < %s
    ORDER BY timestamp ASC""",
    (term_year, term_month, subject, number, timestampCutoff))

  enrollment_samples = [{'timestamp': row[0],
    'date': datetime.fromtimestamp(row[0]).strftime('%m-%d'),
    'days_since_reg_start': (datetime.fromtimestamp(row[0]).date() - const.REGISTRATION_START_DATES_BY_TERM[(term_year, term_month)]).days,
    'available_seats': row[1],
    'enrolled_seats': row[2],
    'waitlist_length': row[3]} for row in cur.fetchall()]

  return enrollment_samples

def previous_term(term_year, term_month):
  term_month = int(term_month)
  session_numbers = list(const.TERM_SESSION_BY_MONTH.keys())
  idx = session_numbers.index(term_month)
  previous_session = session_numbers[idx - 1]

  if previous_session > term_month:
    term_year -= 1

  return (term_year, previous_session)

def latest_term_course_offered(subject, number, title_url_component=None):
  cur = db_conn.cursor()
  args = (subject, number)

  query = "SELECT term_year, term_month FROM courses WHERE subject = %s AND number = %s"

  if title_url_component:
    query += " AND title_url_component = %s"
    args = (subject, number, title_url_component)

  query += "ORDER BY term_year desc, term_month desc LIMIT 1"
  cur.execute(query, args)
  return cur.fetchone()

def previous_term_with_enrollment(subject, number, reference_term):
  cur = db_conn.cursor()
  year, month = reference_term
  if 5 <= month <= 7:
    term_conditions = ' term_month <@ int4range(5, 8)'
  else:
    term_conditions = ' NOT term_month <@ int4range(5, 8) '

  cur.execute("""SELECT term_year, term_month from courses_enrollment
    WHERE subject = %s AND number = %s
      AND (term_year < %s OR (term_year = %s AND term_month < %s)) --
    AND {}
    ORDER BY term_year desc, term_month desc limit 1""".format(term_conditions),
    (subject, number, year, year, month))

  return cur.fetchone()

EMPTY_ENROLLMENT_SAMPLE = {'available_seats': None, 'enrolled_seats': None, 'waitlist_length': None}
def align_samples(samplesToAlign, anchorSamples):
  """
  Aligns the first set of samples to the 'anchor' samples' time scale.
  In the usage in add_enrollment_to_course,
  samplesToAlign is the live enrollment,
  and anchorSamples is historical.
  """
  lastDay = samplesToAlign[-1]['days_since_reg_start']

  try:
    anchorSampleDays = [sample['days_since_reg_start'] for sample in anchorSamples[::-1]]
    alignedSamples = [{**sample.copy(), **EMPTY_ENROLLMENT_SAMPLE.copy()} for sample in anchorSamples]

    anchorIdxFloor = 0
    for sample in samplesToAlign:
      relevantSamples = enumerate(anchorSamples[anchorIdxFloor:])
      sampleDays = sample['days_since_reg_start']
      matchingAnchorSampleIdx, _ = min(relevantSamples, key=lambda idxAndSample: abs(sample['days_since_reg_start'] - idxAndSample[1]['days_since_reg_start']))
      alignedSamples[matchingAnchorSampleIdx] = sample

    active_sample = alignedSamples[0]
    lastDayAnchorIdx = (len(anchorSamples) - 1) - min(enumerate(anchorSampleDays), key=lambda idxAndDay: abs(lastDay - idxAndDay[1]))[0]
    for idx, sample in enumerate(alignedSamples[:lastDayAnchorIdx]):
      if sample['available_seats'] != None:
        active_sample = sample
      else:
        alignedSamples[idx]['available_seats'] = active_sample['available_seats']
        alignedSamples[idx]['waitlist_length'] = active_sample['waitlist_length']
        alignedSamples[idx]['enrolled_seats'] = active_sample['enrolled_seats']
    return alignedSamples
  except ValueError:
    return align_samples(anchorSamples, samplesToAlign)

def add_enrollment_to_course(course):
  course['live_enrollment'] = enrollment_samples_for_course(course['term_year'],
    course['term_month'],
    course['subject'],
    course['number'])

  most_recent_term = previous_term_with_enrollment(course['subject'], course['number'],
    (course['term_year'], course['term_month']))
  if most_recent_term:
    previous_enrollment_samples = enrollment_samples_for_course(*most_recent_term, course['subject'], course['number'])
    previous_enrollment_samples = reduce_enrollment_samples_to_day(previous_enrollment_samples)
    course['live_enrollment'] = align_samples(course['live_enrollment'], previous_enrollment_samples)
    # course['live_enrollment'] = reduce_enrollment_samples_to_day(course['live_enrollment'])
    course['historical_enrollment'] = {
      'term_year': most_recent_term[0],
      'session': const.PRETTY_SESSION_BY_MONTH[most_recent_term[1]],
      'samples': previous_enrollment_samples}
  else:
    course['historical_enrollment'] = {}
    course['live_enrollment'] = reduce_enrollment_samples_to_day(course['live_enrollment'])

def similar_classes_by_subject_and_number(term_year, term_month, subject, number, user_id=None):
  """
  Looks up classes offered in the same term as the provided class
  that share a subject and are lower/upper divs in the same class.

  This is a basic implementation of related classes
  that can be improved to show users classes
  they still need for their requirements.
  """
  cur = db_conn.cursor()
  query = CourseQuery(where_conditions=[('courses.term_year = %s', term_year),
    ('courses.term_month = %s', term_month),
    ('courses.subject = %s', subject),
    ('courses.number != %s', number)])
  if int(number[:3]) < 100:
    query = query.merge(FilterConditions.lower_division(1))
  else:
    query = query.merge(FilterConditions.upper_division(1))
  add_enrollment_aggregates(query)

  if user_id:
    query.fields += (cur.mogrify("""(EXISTS (SELECT 1 FROM students_completed_courses scc
      JOIN courses courses_scc ON courses_scc.id = scc.course_id
      WHERE scc.student_id = %s
      AND courses_scc.subject = courses.subject
      AND courses_scc.number = courses.number)) user_completed_course""", (user_id,)).decode('utf-8'),)

  # Primary sort: has completed
  # Secondary sort: enrollment
  return sorted(course_query(*query.sql_and_values(), omit_sections=True, sort=True),
    key=lambda course: (not course.get('user_completed_course', False), course['total_max_enrollment']),
    reverse=True)

@utils.redis_lru()
def get_course_detail(term_year, term_month, subject, number, title=None, mock_questions=False, user_id=None):
  detail_query = CourseQuery(where_conditions=[('courses.term_year = %s', term_year),
    ('courses.term_month = %s', term_month),
    ('courses.subject = %s', subject),
    ('courses.number = %s', number)],
    group_by=('courses.id',))

  if title:
    detail_query.where_conditions.append(('courses.title_url_component = %s', title))
  add_enrollment_aggregates(detail_query)
  detail_query.group_by += ('course_agg.total_max_enrollment', 'course_agg.total_available_seats', 'course_agg.total_waitlist_length')
  try:
    course = course_query(*detail_query.sql_and_values())[0]
  except IndexError:
    return None
  try:
    instructors = [(section['instructor'], url_for('instructor', instructor_id=section['instructor_id']))
     for section in course['sections'] if section['instructor_id']]
  except RuntimeError:
    # RuntimeError thrown when function called outside application context
    # Here we insert a dummy URL when not running in application context
    instructors = [(section['instructor'], '') for section in course['sections']]

  instructors = list(set(instructors))
  course['instructors'] = [{'name': name, 'url': url} for name, url in instructors] # transform to dict

  course['grades'] = grade_stats_for_course(course['subject'], course['number'])
  for grade in course['grades']:
    grade['is_term_relevant'] = any(instr == grade['instructor'] for instr, url in instructors)
  course['grades'] = sorted(course['grades'], key=lambda grade: not grade['is_term_relevant'])
  course['related'] = similar_classes_by_subject_and_number(course['term_year'],
    course['term_month'],
    course['subject'],
    course['number'],
    user_id=user_id)


  latest_term_offered = latest_term_course_offered(subject, number, title)
  if (term_year, term_month) != latest_term_offered:
    latest_course = {
      'term_year': latest_term_offered[0],
      'term_month': latest_term_offered[1],
      'subject': subject,
      'number': number,
      'title_url_component': title}

    course['latest_offering'] = {
      'session': const.PRETTY_SESSION_BY_MONTH[latest_term_offered[1]],
      'term_year': latest_term_offered[0],
      'url': url_for_section(latest_course)
    }

  course['term_session'] = const.PRETTY_SESSION_BY_MONTH[course['term_month']]
  course['textbooks'] = [{'title': "Thomas' Calculus: Early Transcendentals (13th Edition)", 'url': 'http://www.amazon.com/Thomas-Calculus-Early-Transcendentals-Edition/dp/0321884078', 'conditions': 'Used & New', 'lowest_price': '$10.00'}]
  return course

def get_courses(groupSections=False, **filters):
  query = "SELECT * FROM courses"

  if filters:
    query += " WHERE "
    comparisons = list()

    for column, value in filters.items():
      cmpr = "{0} = %({0})s".format(column)
      comparisons.append(cmpr)

    query += ' AND '.join(comparisons) + ';'

  if groupSections:
    yield from course_query(query, filters, sort=True)
  else:
    yield from sections_for_query(query, filters)

def match_course_number(text):
  matches = re.search(r'([0-9]{1,3})([A-Za-z]{1,2})?-?([0-9]{1,3})?([A-Za-z]{1,2})?', text)

  if matches:
      offset = matches.end(matches.lastindex)
      number, letters, max_number, max_letters = matches.groups()

      number = number.zfill(3)
      if not letters:
          letters = ''

      if max_number:
        max_number = max_number.zfill(3)
        if not max_letters:
          max_letters = ''
      elif max_letters:
        max_number = number

      if max_number or max_letters:
        return ('{}{}-{}{}'.format(number, letters, max_number, max_letters), offset)
      else:
        return (number + letters, offset)


  return (None, -1)

def courses_from_text(text):
  courses = list()
  offset = 0
  subject = None
  while offset != -1:
    normalized_subject_codes_by_name = {k.lower(): v for k, v in const.SUBJECT_CODES_BY_NAME.items()}
    course_number, offset = match_course_number(text)
    matched_keywords = list()
    exact_match_candidate = None
    for keyword in text[:offset].split()[::-1]:
      # Strip non-alphanumeric
      keyword = re.sub(r'[^\'A-Za-z0-9 ]', '', keyword)
      keyword = keyword.lower()
      if matched_keywords and matched_keywords[-1] == keyword:
        continue

      if keyword.upper() in const.SUBJECTS:
        subject = keyword.upper()
        break

      try:
        matched_subjects = const.SUBJECTS_BY_KEYWORD[keyword]
        matched_keywords.insert(0, keyword)

        try: # attempt exact match
          exact_match_candidate = normalized_subject_codes_by_name[' '.join(matched_keywords)]
        except KeyError:
          exact_match_candidate = None
          subject_sets = list()
          for keyword in matched_keywords:
            subject_sets.append(set(const.SUBJECTS_BY_KEYWORD[keyword]))

          intersection = subject_sets[0]
          for set_ in subject_sets[1:]:
            intersection = intersection & set_
          if len(intersection) == 1:
            subject = next(iter(intersection))
            break
      except KeyError:
        if exact_match_candidate and keyword not in const.CONJUNCTIONS:
          subject = exact_match_candidate
          break

    if exact_match_candidate and keyword not in const.CONJUNCTIONS:
        subject = exact_match_candidate
    if course_number and subject:
      courses.append((subject.upper(), course_number))
    text = text[offset:]
  return courses

def expand_course_number_range(subject, range_str):
  number_split = range_str.split('-')
  if len(number_split) == 1: # no split occurred
    return range_str

  cur = db_conn.cursor()
  cur.execute("""SELECT DISTINCT(number) FROM courses

      WHERE
      subject = %s
      AND substring(number, 0, %s) >= %s
      AND substring(number, 0, %s) <= %s
    ORDER BY number""", (subject,
      len(number_split[0]) + 1, number_split[0],
      len(number_split[1]) + 1, number_split[1]))

  return [row[0] for row in cur.fetchall()]

def coursesStartingWithNumber(subject, numberPrefix):
  cur = db_conn.cursor()
  cur.execute("""SELECT DISTINCT number, trim(leading '0' from number) = %s, position(%s in trim(leading '0' from number)), number FROM courses
    WHERE subject = %s
      AND (trim(leading '0' from number) LIKE %s
      OR trim(leading '0' from number) = %s)
    ORDER BY trim(leading '0' from number) = %s, position(%s in trim(leading '0' from number)), number""",
    (numberPrefix, numberPrefix, subject, numberPrefix + '%', numberPrefix, numberPrefix, numberPrefix))

  return [(subject, row[0]) for row in cur.fetchall()]

def max_annual_enrollment(subject, number):
  cur = db_conn.cursor()
  q = """select term_year, sum(max_enrollment) from courses
    where subject = %s
    and number = %s
    and max_enrollment is not null
    group by term_year
    order by sum desc limit 1;
    """
  cur.execute(q, (subject, number))

  enrollment =  cur.fetchone()
  if enrollment:
    return enrollment[1]
  else:
    return None