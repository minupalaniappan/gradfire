import unittest
from daviscoursesearch.flaskapp.utils.student_utils import _ge_completion_initial_sum, _ge_completion_resolve_conflicts
from daviscoursesearch.common.constants import GE_AREAS, GE_AREAS_BY_CATEGORY

class TestGeCompletion(unittest.TestCase):
  def test_ge_initial_sum_no_conflicts(self):
    """
    Ensures the initial GE completion sum is accurate when conflicts are not present.
    Tests with mock courses, each of which is 4 units and satisfies one GE area.
    """
    # Setup
    course_completion_records = list()
    for area in GE_AREAS:
      record = (4, [area])
      course_completion_records.append(record)

    # Test
    area_totals, conflicting_records = _ge_completion_initial_sum(course_completion_records)
    self.assertEqual(len(conflicting_records), 0)
    for area in GE_AREAS:
      try:
        if area == 'American Cultures, Governance & History':
          self.assertEqual(area_totals[area], 8)
        else:
          self.assertEqual(area_totals[area], 4)
      except AssertionError as e:
        print('Area {} failed assertion'.format(area))
        raise e

  def test_ge_initial_sum_with_conflicts(self):
    """
    Ensures the initial GE completion sum is accurate when conflicts are present.
    """
    # Setup
    course_completion_records = list()

    # For each GE category, add a course that satisfies two areas within the category.
    # Each record contains a conflict
    for category, areas in GE_AREAS_BY_CATEGORY.items():
      record = (4, areas[:2])
      course_completion_records.append(record)

    # Test
    area_totals, conflicting_records = _ge_completion_initial_sum(course_completion_records)
    self.assertEqual(len(conflicting_records), len(course_completion_records))
    self.assertFalse(any(total > 0 for total in area_totals.values()))

  def test_handling_domestic_diversity(self):
    """
    Domestic diversity credit counts towards itself and ACGH.
    This test ensures that relationship is properly handled.
    """
    # Setup
    dd_acgh_completion_records = [
      (4, ['Domestic Diversity', 'American Cultures, Governance & History'])
    ]

    dd_completion_records = [
      (4, ['Domestic Diversity'])
    ]

    # Test DD, ACGH
    area_totals, conflicting_records = _ge_completion_initial_sum(dd_acgh_completion_records)
    self.assertEqual(len(conflicting_records), 1)

    resolved_area_totals = _ge_completion_resolve_conflicts(area_totals, conflicting_records)
    self.assertEqual(resolved_area_totals['Domestic Diversity'], 4)
    self.assertEqual(resolved_area_totals['American Cultures, Governance & History'], 4)

    # Test DD only
    area_totals, conflicting_records = _ge_completion_initial_sum(dd_completion_records)
    self.assertEqual(len(conflicting_records), 0)
    self.assertEqual(area_totals['Domestic Diversity'], 4)
    self.assertEqual(area_totals['American Cultures, Governance & History'], 4)

def test_domestic_diversity_with_conflict(self):
  """
  This test ensures that DD credit propagates when a real conflict occurs.
  ACGH and DD credit should be bundled in the area optimization logic
  """
  dd_acgh_completion_records = [
    (4, ['Visual Literacy']),
    (4, ['Visual Literacy', 'Domestic Diversity', 'American Cultures, Governance & History']),
  ]

  area_totals, conflicting_records = _ge_completion_initial_sum(dd_acgh_completion_records)
  self.assertEqual(len(conflicting_records), 1)

  resolved_area_totals = _ge_completion_resolve_conflicts(area_totals, conflicting_records)
  self.assertEqual(resolved_area_totals['Domestic Diversity'], 4)
  self.assertEqual(resolved_area_totals['American Cultures, Governance & History'], 4)
  self.assertEqual(resolved_area_totals['Visual Literacy'], 4)
