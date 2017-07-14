import json
import sys
from ..common import environment
from ..flaskapp.utils.db_utils import conn
from ..flaskapp.utils.major_utils import normalize_major_reqs

def normalize_all_major_reqs():
  cur = conn.cursor()
  cur.execute("SELECT id, requirements_json FROM majors WHERE requirements_json != ''")
  requirements_by_id = cur.fetchall()
  for major_id, req_json in requirements_by_id:
    nrml_req_json = normalize_major_reqs(req_json)
    cur.execute("UPDATE majors SET requirements_json = %s WHERE id = %s", (nrml_req_json, major_id))

if __name__ == '__main__':
  normalize_all_major_reqs()