"""
Sum major unit requirement and list courses mentioned on page
"""
import requests
from bs4 import BeautifulSoup
import daviscoursesearch.common.constants as const
from daviscoursesearch.flaskapp.utils.db_utils import conn as db_conn
import re

REQ_PAGE_BY_MAJOR = {
  'Computer Science': 'http://catalog.ucdavis.edu/programs/compsci/compscireqt.html',
  'Engineering: Civil and Environmental': 'http://catalog.ucdavis.edu/programs/ECI/ECIreqt.html',
  'Computer Science and Engineering':  'http://catalog.ucdavis.edu/programs/ECS/ECSreqt.html',
  'Animal Science': 'http://catalog.ucdavis.edu/programs/ANS/ANSreqt.html',
  'Nutrition Science': 'http://catalog.ucdavis.edu/Programs/nutsci/nutscireqt.html'
}

def match_course_number(text):
  matches = re.search(r'([0-9]{1,3})([A-Za-z]{1,2})?', text)
  # 001
  # 001A
  
  if matches:
      # TODO consider 1 digit matches
      if len(matches.group(0)) == 1:
        return (None, -1)
      number, letters = matches.groups()
      if not letters:
          letters = ''

      if int(number) < 100 and len(number) < 3:
          number = ''.join(['0' for i in range(3 - len(number))]) + number

      return (number + letters, matches.end(1))

  return (None, -1)

def extract_courses(cell_contents):
  courses = list()
  offset = 0
  subject = None
  while offset != -1:
    normalized_subject_codes_by_name = {k.lower(): v for k, v in const.SUBJECT_CODES_BY_NAME.items()}
    cell_contents = cell_contents.replace('-', ' ')
    course_number, offset = match_course_number(cell_contents)
    matched_keywords = list()
    exact_match_candidate = None

    for keyword in cell_contents[:offset].split()[::-1]:
      keyword = keyword.strip(',')
      keyword = keyword.lower()

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
      courses.append((subject, course_number))
    cell_contents = cell_contents[offset:]

  return courses

def extract_units(cell_contents):
  matches = re.match(r'^([0-9]+)', cell_contents)
  if matches:
    return int(matches.group(1))
  return 0

def insert_major_courses(major, units, major_courses):
  cur = db_conn.cursor()
  cur.execute("SELECT id FROM majors WHERE name = %s", (major,))
  major_id = cur.fetchone()[0]
  cur.execute("UPDATE majors SET units = %s WHERE id = %s", (units, major_id))

  for subject, number in major_courses:
    query = """
    INSERT INTO major_courses (major_id, course_subject, course_number) VALUES (%s, %s, %s)
    """
    cur.execute(query, (major_id, subject, number))
  
def main():
  for major, req_url in REQ_PAGE_BY_MAJOR.items():
    print('Major {}'.format(major))
    r = requests.get(req_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    req_table = soup.find('td', {'id': 'announcements'}).find('table')
    major_courses = list()
    units = 0
    for row in req_table.find_all('tr'):
      cells = row.find_all('td')

      course_cell = unit_cell = None
      try:
        course_cell, unit_cell = cells
      except ValueError:
        course_cell = cells[0]
      
      major_courses += extract_courses(course_cell.text)
      if unit_cell:
        units += extract_units(unit_cell.text)
    print(units)
    insert_major_courses(major, units, set(major_courses))

if __name__ == '__main__':
  main()