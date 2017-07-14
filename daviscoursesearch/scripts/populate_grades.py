from davislib import Term
from ..common.constants import GRADE_ORDER_BY_LETTER
from ..flaskapp.utils.db_utils import conn as db_conn
import sys
import psycopg2
import csv

READER_FIELDNAMES = ['TERM',
  'GRADE',
  'SUBJECT',
  'COURSE NUMBER',
  'COURSE TITLE',
  'INSTRUCTOR',
  'GRADE',
  'COUNT'
]

COLUMN_MAPPINGS = {
  'TOTAL': 'COUNT'
}

def populate_grades(csv_rows):
  cur = db_conn.cursor()
  for row in csv_rows:
    season, _, year = row['TERM'].split()
    term = Term(int(year), season.lower())
    grade_order = GRADE_ORDER_BY_LETTER.get(row['GRADE'])
    try:
      cur.execute("""INSERT INTO courses_grades (term_year, term_month, subject, number, title, instructor, letter, count, grade_order, instructor_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
            )""",
        (term.year, term.session.value, row['SUBJECT'], row['COURSE NUMBER'], row['COURSE TITLE'], row['INSTRUCTOR'], row['GRADE'], row['COUNT'], grade_order,
          row['INSTRUCTOR']))
    except psycopg2.IntegrityError:
      pass

def normalize_row(row):
  for key, value in row.copy().items():
    del row[key]
    row[key.strip()] = value.strip()

  row = map_column_names(row)
  return row

def map_column_names(row):
  keys_to_map = set(row.keys()) - set(READER_FIELDNAMES)
  for key_to_map in keys_to_map:
    mapped_key = COLUMN_MAPPINGS[key_to_map]
    row[mapped_key] = row[key_to_map]

  return row

def main():
  try:
    grade_file = sys.argv[1]
  except IndexError:
    print('Usage: populate_grades.py path_to_grade')
    return

  with open(grade_file, 'r') as f:
    reader = csv.DictReader(f)
    normalized_rows = map(normalize_row, reader)
    if reader.fieldnames != READER_FIELDNAMES:
      normalized_rows = map(map_column_names, normalized_rows)

    populate_grades(map(normalize_row, reader))

if __name__ == '__main__':
  main()