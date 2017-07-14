import requests
from bs4 import BeautifulSoup
from ..flaskapp.utils.db_utils import conn as db_conn
import logging
import psycopg2
import re

STORE_ENDPOINT = "http://ucdavisstores.com/SelectCourses.aspx"
# http://ucdavisstores.com/SelectCourses.aspx?src=2&type=2&stoid=192&trm=Spring%2016&cid=49592

class TextbooksTbdError(Exception):
  pass

class InclusiveAccessError(Exception):
  """
  Inclusive access deserves to be an error...
  """
  pass

def materials_for_course(term, crn):
  """
  Returns list of tuple ('isbn', 'requirement_description')
  """
  params = {
    'src': 2,
    'type': 2,
    'stoid': 192,
    'trm': '{}%{}'.format(str(term.session).split()[0], term.year),
    'cid': crn
  }
  s = requests.Session()
  req = requests.Request('GET', STORE_ENDPOINT, params=params).prepare()
  req.url = req.url.replace('%25', '%')
  resp = s.send(req)

  soup = BeautifulSoup(resp.text, 'html.parser')
  page_texts = [span.text for span in soup.find_all()]

  if any(re.match("Textbook requirements have not yet been determined for this course.", text.strip())  for text in page_texts):
    raise TextbooksTbdError()

  if any(re.match("No Unique IDs match your search request.", text.strip()) for text in page_texts):
    raise TextbooksTbdError()

  materials = list()
  material_containers = soup.find_all('div', {'class': 'material_info'})
  for material in material_containers:
    # removes bogus hidden text from isbn element.
    # "<h1 class="hidden">bogus</h1>" is literally placed in between the isbn numbers..
    isbn_ele = material.find('span', {'class': 'isbn'})
    if not isbn_ele and any('Inclusive Access' in span.text for span in material.find_all('span')):
      raise InclusiveAccessError()

    isbn = ''.join([text for text in isbn_ele.contents if isinstance(text, str) and text.isdigit() and text != '0'])

    if isbn:
      req_desc = material.find('div', {'class': 'material_label'}).find('span').text.strip()
      materials.append((isbn, req_desc))

  if not materials:
    raise TextbooksTbdError()

  return materials

def scrape_unknown_isbns_for_stored_term(term):
  cur = db_conn.cursor()
  cur.execute("""SELECT id, crn FROM courses WHERE term_year = %s AND term_month = %s
    AND length(crn) = 5 AND NOT EXISTS (SELECT 1 FROM courses_textbooks WHERE course_id = courses.id)""",
    (term.year, term.session.value))

  courses = cur.fetchall()
  for course_id, crn in courses:
    try:
      materials = materials_for_course(term, crn)
    except TextbooksTbdError:
      continue
    except InclusiveAccessError:
      cur.execute("UPDATE courses SET is_inclusive_access = true WHERE id = %s", (course_id,))
      continue

    print(crn, materials)
    for isbn, req_desc in materials:
      try:
        cur.execute("INSERT INTO courses_textbooks (course_id, isbn, requirement_desc) VALUES (%s, %s, %s)", (course_id, isbn, req_desc))
      except psycopg2.IntegrityError:
        pass