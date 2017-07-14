import unittest
import os.path
from davislib import Term
from daviscoursesearch.flaskapp.utils.student_utils import _parse_transcript_lines, parse_transcript
from daviscoursesearch.common import constants

script_path =  os.path.dirname(os.path.realpath(__file__))
transcript_lines = open(os.path.join(script_path, 'resources/sample_transcript.txt'), 'r').readlines()
transcript_text = '\n'.join(transcript_lines)

AP_EQUIVALENCE_LINE = '  201310  (ECS TR1) - APCA - ADV PLAC Computer Science A (score: 5) 2.00  P '
AP_EQUIVALENCE_EXPECTED = {
  'equivalence': True,
  'grade': 'P',
  'number': 'TR1',
  'subject_code': 'ECS',
  'term': Term(2013, '10'),
  'title': 'APCA - ADV PLAC Computer Science A (score: 5)',
  'units': '2.00'}

COURSE_LINE = '  201410  MAT 021C - Calculus 4.00  B-  '
GE_LINE = 'GE3 (AH,VL,WC,WE)'
COURSE_LINE_EXPECTED = {
  'equivalence': False,
  'grade': 'B-',
  'number': '021C',
  'subject_code': 'MAT',
  'term': Term(2014, '10'),
  'title': 'Calculus',
  'units': '4.00',
  'ge_areas': ['Arts & Humanities', 'Visual Literacy', 'World Cultures', 'Writing Experience']}

class TranscriptParseTest(unittest.TestCase):
  def test_parse_transcript_lines_equivalence(self):
    parsed_line = _parse_transcript_lines([AP_EQUIVALENCE_LINE])
    self.assertEqual(parsed_line, AP_EQUIVALENCE_EXPECTED)

  def test_parse_transcript_lines_non_equivalence(self):
    parsed_line = _parse_transcript_lines([COURSE_LINE, GE_LINE])
    self.assertEqual(parsed_line, COURSE_LINE_EXPECTED)

  def test_sample_transcript_parse(self):
    constants.CURRENT_TERM = (2016, 1)
    completed_course_ids, tentative_course_ids, equivalences = parse_transcript(transcript_text)

    self.assertEqual(len(completed_course_ids), 18)
    self.assertEqual(len(tentative_course_ids), 3)
    self.assertEqual(len(equivalences), 7)
    self.assertEqual(equivalences[0],
      {
        'term_year': 2013,
        'term_month': '10',
        'subject': 'ECS',
        'number': 'TR1',
        'description': 'APCA - ADV PLAC Computer Science A (score: 5)',
        'ge_areas': None,
        'units': '2.00',
        'grade': 'P',
        'course_exists': False
      })
    self.assertEqual(equivalences[1],
      {
        'term_year': 2013,
        'term_month': '10',
        'subject': 'ENL',
        'number': '003',
        'ge_areas': None,
        'description': 'APEL - ADV PLAC English Language (score: 4)',
        'units': '4.00',
        'grade': 'P',
        'course_exists': True
      }
      )

