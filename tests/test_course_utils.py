import unittest
from daviscoursesearch.flaskapp.utils.course_utils import courses_from_text

class TestCourseUtils(unittest.TestCase):
	def test_course_range_string_parsed(self):
		expected_courses = courses_from_text('EAE 100-199')
		self.assertEqual(expected_courses, [('EAE', '100-199')])
