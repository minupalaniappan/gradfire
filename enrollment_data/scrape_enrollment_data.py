from davislib import ScheduleBuilder, Term
from daviscoursesearch.common.constants import SUBJECTS
import json
import os.path
import sys
import time


def display_enrollment_data(sb, term):
  for subject in SUBJECTS:
    courses = sb.course_query(term, subject=subject)
    for course in courses:
      enrollment_data = {
        'crn': course.crn,
        'timestamp': int(time.time()),
        'available_seats': course.available_seats,
        'wl_length': course.wl_length
      }
      print(json.dumps(enrollment_data))

def main():
  try:
    season, year = sys.argv[1:]
    year = int(year)
  except ValueError:
    print('Usage: scrape_enrollment_data.py term_season term_year')
    return

  try:
    credentials_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials')
    username, password = open(credentials_path, 'r').read().split()
  except IOError as e:
    print(e)
    return
  except ValueError:
    print('Credentials file not of format: "{username} {password}"')
    return

  sb = ScheduleBuilder(username, password)
  term = Term(year, season)
  display_enrollment_data(sb, term)

if __name__ == '__main__':
  main()

