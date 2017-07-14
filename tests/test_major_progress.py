import json
import os
import unittest
from daviscoursesearch.flaskapp.utils.major_utils import compute_major_progress, majors_by_id

script_path =  os.path.dirname(os.path.realpath(__file__))
CS_MAJOR_REQS = json.load(open(os.path.join(script_path, 'resources/compsci_req.json'), 'r'))
CS_UPPER_DIV_OVERRIDE_COMPLETIONS = [('ECS', '122A'), ('ECS', '120'), ('LIN', '177')]
class TestMajorProgress(unittest.TestCase):
  def test_compsci_major_total(self):
    __, _, total = compute_major_progress(CS_MAJOR_REQS, CS_UPPER_DIV_OVERRIDE_COMPLETIONS)
    self.assertEqual(total, 107)

  def test_compute_completion_with_override(self):
    _, completion, _ = compute_major_progress(CS_MAJOR_REQS, CS_UPPER_DIV_OVERRIDE_COMPLETIONS)
    # ECS 122A and 120 are hard requirements, but are
    # also listed as *optional* as part of a CS elective.
    # This assertion verifies that such courses are not
    # double-counted.
    self.assertEqual(completion, 12)
