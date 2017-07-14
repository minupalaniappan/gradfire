import unittest
from daviscoursesearch.flaskapp.utils import utils

class TestUtils(unittest.TestCase):
  def test_next_term_should_wrap_around(self):
    next_term = utils.next_term(2016, 10)
    self.assertEqual(next_term, (2017, 1))

  def test_prev_term_should_wrap_around(self):
    prev_term = utils.previous_term(2016, 1)
    self.assertEqual(prev_term, (2015, 10))

  def test_prev_term_should_report_correct(self):
    prev_term = utils.previous_term(2016, 10)
    self.assertEqual(prev_term, (2016, 3))

  def test_next_term_should_report_correct(self):
    next_term = utils.next_term(2016, 1)
    self.assertEqual(next_term, (2016, 3))