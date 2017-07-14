from daviscoursesearch.flaskapp.models.models import CourseQuery
import unittest

class TestCourseQuery(unittest.TestCase):
  def test_conditions_should_propagate(self):
    cq = CourseQuery(where_conditions=
      [
        ('subject = %s', 'ECS'),
        ('term_year = %s', '2015')
      ])

    sql, values = cq.sql_and_values()

    self.assertEqual(values, ['ECS', '2015'])

  def test_join_should_propagate(self):
    cq = CourseQuery(joins=[('JOIN', "ON foo_table foo_column = %s AND bar_column = %s", 'foo', 'bar')])
    sql, values = cq.sql_and_values()
    self.assertEqual(values, ['foo', 'bar'])

  def test_conditions_should_render_without_value(self):
    cq = CourseQuery(where_conditions=
      [
        ('subject NOT NULL',),
        ('term_year = 2015',)
      ])

    sql, values = cq.sql_and_values()
    self.assertFalse(values)
    self.assertTrue('subject NOT NULL' in sql)
    self.assertTrue('term_year = 2015' in sql)

if __name__ == '__main__':
  unittest.main()