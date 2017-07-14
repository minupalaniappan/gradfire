from davislib import ScheduleBuilder, Term
from ..flaskapp.utils.course_utils import get_courses
from ..flaskapp.utils.db_utils import conn as db_conn
from ..common.constants import SUBJECTS
from .coursescraper import insert_course
import json
import os.path
import sys
import time

def get_course_metadata(crn, term_year, term_month):
  course = next(get_courses(crn=crn, term_year=term_year, term_month=term_month))
  if not course['max_enrollment']:
    raise ValueError()

  return {
    'subject': course['subject'],
    'number': course['number'],
    'max_enrollment': course['max_enrollment']
  }

def collect_enrollment_samples(sb, term):
  enrollment_samples = []
  run_timestamp = int(time.time())
  for subject in SUBJECTS:
    courses = sb.course_query(term, subject=subject)
    for course in courses:
      enrollment_data = {
        'term_year': term.year,
        'term_month': int(term.session.value),
        'crn': course.crn,
        'timestamp': int(time.time()),
        'run_timestamp': run_timestamp,
        'available_seats': course.available_seats,
        'wl_length': course.wl_length
      }
      try:
        course_meta = get_course_metadata(course.crn, term.year, int(term.session.value))
        enrollment_samples.append({**enrollment_data, **course_meta})
      except (StopIteration, ValueError): # course does not exist yet. likely a new section. wait for sync.py to run
        pass

  return enrollment_samples

def update_section_enrollment(samples):
  cur = db_conn.cursor()
  for section in samples:
    cur.execute("""UPDATE courses SET available_seats = %s, waitlist_length = %s
      WHERE term_year = %s and term_month = %s and crn = %s""",
      (section['available_seats'], section['wl_length'], section['term_year'], section['term_month'], section['crn']))

def aggregate_enrollment_samples(samples):
  course_enrollments_by_subject = dict()
  for section in samples:
    enrlmnt_for_subject = course_enrollments_by_subject.get(section['subject'])

    if enrlmnt_for_subject:
      course = enrlmnt_for_subject.get(section['number'])
      if course:
        course['available_seats'] += section['available_seats']
        course['wl_length'] += section['wl_length']
        try:
          course['max_enrollment'] += section['max_enrollment']
          course['enrolled_seats'] += section['max_enrollment'] - section['available_seats']
        except TypeError as e:
          print(e)
      else:
        section_copy = section.copy()
        section_copy.update(enrolled_seats=section['max_enrollment'] - section['available_seats'])
        enrlmnt_for_subject[section['number']] = section_copy
    else:
      section_copy = section.copy()
      section_copy.update(enrolled_seats=section['max_enrollment'] - section['available_seats'])
      course_enrollments_by_subject[section['subject']] = {section['number']: section_copy}

  return course_enrollments_by_subject

def last_enrollment_for_course(course, cur):
  cur.execute("""SELECT enrolled_seats, available_seats, waitlist_length
    FROM courses_enrollment
    WHERE term_year = %(term_year)s AND term_month = %(term_month)s AND crn = %(crn)s
    ORDER BY timestamp DESC
    LIMIT 1""", course)
  try:
    enrolled_seats, available_seats, wl_length = cur.fetchone()
    return {
      'enrolled_seats': enrolled_seats,
      'available_seats': available_seats,
      'wl_length': wl_length
    }
  except TypeError as e:
    print(e)

def store_agg_enrollment(enrollment):
  cur = db_conn.cursor()
  for subject, courses_by_number in enrollment.items():
    for number, course in courses_by_number.items():
      cur.execute("""INSERT INTO courses_enrollment
        (term_year, term_month, crn, subject, number, timestamp, run_timestamp, enrolled_seats,
          available_seats, waitlist_length)
        VALUES
          (%(term_year)s, %(term_month)s, %(crn)s, %(subject)s, %(number)s, %(timestamp)s,
            %(run_timestamp)s, %(enrolled_seats)s, %(available_seats)s, %(wl_length)s)""", course)

def scrape_enrollment(term, credentials):
  sb = ScheduleBuilder(*credentials)
  enrollment_samples = collect_enrollment_samples(sb, term)
  update_section_enrollment(enrollment_samples)
  enrollment_samples_agg = aggregate_enrollment_samples(enrollment_samples)
  store_agg_enrollment(enrollment_samples_agg)
