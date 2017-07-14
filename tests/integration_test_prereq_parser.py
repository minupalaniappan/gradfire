import collections
import unittest
from environment import config 
from daviscoursesearch.scripts.prereq_parser import parse_prereq_text

ANNOTATED_PREREQUISITES = [
  {
      "text": "Biological Sciences 2A; concurrent enrollment in Exercise Biology 106L or course 101L strongly recommended.",
      "requirements": {
        "children": [('BIS', '002A')],
        "relationship": "and"
      }
  },
  {
      "text": "Biological Sciences 2A; concurrent enrollment in course 106L or Cell Biology and Human Anatomy 101L strongly recommended.",
      "requirements": {
        "children": [('BIS', '002A')],
        "relationship": "and"
      }
  },
  {
      "text": "course 102.",
      "requirements": {
        "children": [('course', '102')],
        "relationship": "and"
      }
  },
  {
      "text": "Biological Sciences 1A or 2A; Chemistry 2B (may be taken concurrently).",
      "requirements": {
        'children': [('BIS', '001A'), ('BIS', '002A')],
        "relationship": "or"
      }
  },
  {
      "text": "Biological Sciences 1A, or 2A and Chemistry 2B; Physics 1B or 7C strongly recommended.",
      "requirements": {
        "children": [
          ('BIS', '001A'), 
          {
            'children': [('BIS', '002A'), ('CHE', '002B')],
            'relationship': 'and'
          }],
        "relationship": "or"
      }
  },
  {
      "text": "course 1, 41, 101.",
      "requirements": {
        "children": [('course', '001'), ('course', '041'), ('course', '101')],
        "relationship": "and"
      }
  },
  {
      "text": "course 16A, 17A, or 21A.",
      "requirements": {
        "children": [('course', '016A'), ('course', '017A'), ('course', '021A')],
        "relationship": "or"
      }
  },
  {
      # 
      "text": "nine units of college mathematics and Engineering 6 or knowledge of Matlab or course 22AL (to be taken concurrently).",
      "requirements": None
  },
  {
      "text": "introductory biology or zoology.",
      "requirements": None
  },
  {
      "text": "courses 1, 41.",
      "requirements": {
        "children": [('course', '001'), ('course', '041')],
        "relationship": "and"
      }
  },
  {
      "text": "course 102.",
      "requirements": {
        "children": [('course', '102')],
        "relationship": "and"
      }
  },
  {
      "text": "courses 1, 41.",
      "requirements": {
        "children": [('course', '001'), ('course', '041')],
        "relationship": "and"
      }
  },
  {
      "text": "Chemistry 8B; Neurology, Physiology, and Behavior 101 or the equivalent.",
      "requirements": {
        "children": [
          ('CHE', '008B')        ],
        "relationship": "and"
      }
  },
  {
      "text": "upper division standing in Engineering",
      "requirements": None
  },
  {
      "text": "course 1A or 2A; Chemistry 8B or 118B or 128B.",
      "requirements": {
        "children": [
          {
            'children': [('course', '001A'), ('course', '002A')],
            'relationship': 'or'
          },
          {
            'children': [('CHE', '008B'), ('CHE', '118B'), ('CHE', '128B')],
            'relationship': 'or'
          }
        ],
        "relationship": "and"
      }
  },
  {
      "text": "courses 1 and 41.",
      "requirements": {
        "children": [
          ('course', '001'),
          ('course', '041')
        ],
        "relationship": "and"
      }
  },
  {
      "text": "course 1, 41.",
      "requirements": {
        "children": [
          ('course', '001'),
          ('course', '041')
        ],
        "relationship": "and"
      }
  },
  {
      "text": "courses 1 and 41",
      "requirements": {
        "children": [
          ('course', '001'),
          ('course', '041')
        ],
        "relationship": "and"
      }
  },
  {
      "text": "courses 21C; 22A or 67",
      "requirements": {
        "children": [
          ('course', '021C'),
          {
            'children': [
              ('course', '022A'),
              ('course', '067')
            ],
            'relationship': 'or'
          }
        ],
        "relationship": "and"
      }
  },
  {
      "text": "upper division standing or consent of instructor.",
      "requirements": None
  },
  {
      "text": "Biological Sciences 101 and one course from among Biological Sciences 102, 105, or Animal Biology 102 (Biological Sciences 102, 105 or Animal Biology 102 may be taken concurrently although prior completion is recommended).",
      "requirements": {
        "children": [
          ('BIS', '101')
        ],
        "relationship": "and"
      }
  },
  {
      "text": "course 101; 102 or 105.",
      "requirements": {
        "children": [
          ('course', '101'),
          {
            'children': [
              ('course', '102'),
              ('course', '105')
            ],
            'relationship': 'or'
          }
        ],
        "relationship": "and"
      }
  },
  {
      "text": "course 1, 41.",
      "requirements": {
        "children": [
          ('course', '001'),
          ('course', '041')
        ],
        "relationship": "and"
      }
  },
  {
      "text": "Biological Sciences 102 or equivalent or consent of instructor.",
      "requirements": None
  },
  {
      "text": "Biological Sciences 1A, 102.",
      "requirements": {
        "children": [
          ('BIS', '001A'),
          ('BIS', '102')
        ],
        "relationship": "and"
      }
  },
  {
      "text": "course 2A and 2B; Chemistry 8A or 118A or 128A; Statistics 100 or 13 or 102 or 130A (Statistics 100 preferred).",
      "requirements": {
        "children": [
          ('course', '002A'),
          ('course', '002B'),
          {
            'children': [
              ('CHE', '008A'),
              ('CHE', '118A'),
              ('CHE', '128A')
            ],
            'relationship': 'or'
          },
          {
            'children': [
              ('STA', '100'),
              ('STA', '013'),
              ('STA', '102'),
              ('STA', '130A')
            ],
            'relationship': 'or'
          }
        ],
        "relationship": "and"
      }
  },
  {
      "text": "Psychology 1 recommended.",
      "requirements": None
  },
  {
      "text": "courses 1, 41 and 100 or 135.",
      "requirements": {
        'children': [
          {"children": [
              ('course', '001'),
              ('course', '041'),
              ('course', '100')
            ],
            'relationship': 'and'
          },
          ('course', '135')
        ],
        "relationship": "or"
      }
  },
  {
      "text": "Biological Sciences 102 or 105.",
      "requirements": {
        "children": [
          ('BIS', '102'),
          ('BIS', '105')
        ],
        "relationship": "or"
      }
  },
  {
      "text": "course 1 or the equivalent; completion of Statistics 13 or 102 strongly recommended.",
      "requirements": None
  },
  {
      "text": "course 107A.",
      "requirements": {
        "children": [
          ('course', '107A')
        ],
        "relationship": "and"
      }
  },
  {
      "text": "Sophomore standing",
      "requirements": None
  },
  # {
  #     "text": "Psychology 1, Biological Sciences 1A, or 2A, or 10.",
  #     "requirements": {
  #       "children": [
  #         ('PSC', '001'),
  #         {
  #           'children': [
  #             ('BIS', '001A'),
  #             ('BIS', '002A'),
  #             ('BIS', '010')
  #           ],
  #           'relationship': 'or'
  #         }
  #       ],
  #       "relationship": "and"
  #     }
  # },
  {
      "text": "two years of high school algebra, plane geometry, plane trigonometry; and obtaining required score on the Precalculus Diagnostic Examination.",
      "requirements": None
  },
  {
      "text": "course 16B, 17B, or 21B.",
      "requirements": {
        "children": [
          ('course', '016B'),
          ('course', '017B'),
          ('course', '021B')
        ],
        "relationship": "or"
      }
  },
  {
      "text": "course 2C; Mathematics 16C or 21C; one year of college level physics.",
      "requirements": {
        "children": [
          ('course', '002C'),
          {
            'children': [
              ('MAT', '016C'),
              ('MAT', '021C')
            ],
            'relationship': 'or'
          }
        ],
        "relationship": "and"
      }
  },
  {
      "text": "Mathematics 21D with C- or better, and Mathematics 22A or concurrent.",
      "requirements": {
        "children": [
          ('MAT', '021D')
        ],
        "relationship": "and"
      }
  },
  {
      "text": "introductory psychology.",
      "requirements": None
  },
  {
      "text": "grade of C- or better in Engineering 35 and Mathematics 22B.",
      "requirements": {
        "children": [
          ('ENG', '035'),
          ('MAT', '022B')
        ],
        "relationship": "and"
      }
  },
  {
      "text": "course 2C.",
      "requirements": {
        "children": [
          ('course', '002C')
        ],
        "relationship": "and"
      }
  },
  {
      "text": "trigonometry or consent of instructor.",
      "requirements": None
  },
  {
      "text": "course 1A or 9A.",
      "requirements": {
        "children": [
          ('course', '001A'),
          ('course', '009A')
        ],
        "relationship": "or"
      }
  },
  {
      "text": "course 1 recommended.",
      "requirements": None
  },
  # {
  #     "text": "courses 3-3L or Biological Sciences 1B.",
  #     "requirements": {
  #       "children": [

  #       ],
  #       "relationship": "and"
  #     }
  # },
  {
      "text": "course 140 and course 51 or concurrent.",
      "requirements": {
        "children": [
          ('course', '140')
        ],
        "relationship": "and"
      }
  },
  {
      "text": "courses 1A, 1B, and 1C, or 2A, 2B, and 2C; Chemistry 8B or 118B or 128B.",
      "requirements": {
        "children": [
          {
            'children': [
              {
                'children': [
                  ('course', '001A'),
                  ('course', '001B'),
                  ('course', '001C'),
                ],
                'relationship': 'and'
              },
              {
                'children': [
                  ('course', '002A'),
                  ('course', '002B'),
                  ('course', '002C'),
                ],
                'relationship': 'and'
              }
            ],
            'relationship': 'or'
          },
          {
            'children': [
              ('CHE', '008B'),
              ('CHE', '118B'),
              ('CHE', '128B')
            ],
            'relationship': 'or'
          }
        ],
        "relationship": "and"
      }
  },
  {
      "text": "course 100A, 120, or the equivalent; introductory biology.",
      "requirements": {
        'children': [
          ('course', '100A')
        ],
        'relationship': 'and'
      }
  },
  {
      "text": "Biological Sciences 101.",
      "requirements": {
        "children": [
          ('BIS', '101')
        ],
        "relationship": "and"
      }
  },

  {
    "text": "course 155.",
    "requirements": {
      "children": [
        ('course', '155')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 152A.",
    "requirements": {
      "children": [
        ('course', '152A')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 101 or 111, and 116A.",
    "requirements": {
      "children": [
        {
          'children': [
            ('course', '101'),
            ('course', '111')
          ],
          'relationship': 'or'
        },
        ('course', '116A')
      ],
      "relationship": "and"
    }
},
{
    "text": "courses 111, 112 and Neurobiology, Physiology, and Behavior 101 or the equivalent.",
    "requirements": {
      "children": [
        ('course', '111'),
        ('course', '112')
      ],
      "relationship": "and"
    }
},
{
    "text": "C- or better in each of the following: Engineering 35 and Mathematics 22B and Physics 9B.",
    "requirements": {
      "children": [
        ('ENG', '035'),
        ('MAT', '022B'),
        ('PHY', '009B')
      ],
      "relationship": "and"
    }
},
{
    "text": "grade of C- or better in Mathematics 22B and Physics 9B.",
    "requirements": {
      "children": [
        ('MAT', '022B'),
        ('PHY', '009B')
      ],
      "relationship": "and"
    }
},
{
    "text": "upper division standing.",
    "requirements": None
},
{
    "text": "course 121.",
    "requirements": {
      "children": [
        ('course', '121')
      ],
      "relationship": "and"
    }
},
{
    "text": "grade of C- or better in Engineering 35; grade of C- or better in Mathematics 22B.",
    "requirements": {
      "children": [
        ('ENG', '035'),
        ('MAT', '022B')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 1, 41.",
    "requirements": {
      "children": [
        ('course', '001'),
        ('course', '041')
      ],
      "relationship": "and"
    }
},
{
    "text": "sociology, political science, or applied behavioral science background                                                                                                                                                          +",
    "requirements": None
},
{
    "text": "recommended, or registration in medical school.",
    "requirements": None
},
{
    "text": "course 100A; Statistics 103.",
    "requirements": {
      "children": [
        ('course', '100A'),
        ('STA', '103')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 118C or 128C.",
    "requirements": {
      "children": [
        ('course', '118C'),
        ('course', '128C')
      ],
      "relationship": "or"
    }
},
{
    "text": "Biological Sciences 1C, or 2A, 2B and 2C; Chemistry 8B.",
    "requirements": {
      "children": [
        ('CHE', '008B'),
        {
          'children': [
            ('BIS', '001C'),
            {
              'children': [
                ('BIS', '002A'),
                ('BIS', '002B'),
                ('BIS', '002C'),
              ],
              'relationship': 'and'
            }
          ],
          'relationship': 'or'
        }
      ],
      "relationship": "and"
    }
},
{
    "text": "Management 11A; 11B.",
    "requirements": {
      "children": [
        ('MGT', '011A'),
        ('MGT', '011B')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 148A.",
    "requirements": {
      "children": [
        ('course', '148A')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 128A or consent of instructor, course 128A strongly recommended; chemistry majors should enroll in course 129B concurrently.",
    "requirements": None
},
{
    "text": "Biological Sciences 103, Chemistry 118C.",
    "requirements": {
      "children": [
        ('BIS', '103'),
        ('CHE', '118C')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 130.",
    "requirements": {
      "children": [
        ('course', '130')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 158A.",
    "requirements": {
      "children": [
        ('course', '158A')
      ],
      "relationship": "and"
    }
},
{
    "text": "admission subject to audition before first class meeting.",
    "requirements": None
},
{
    "text": "C- or better in Engineering 103 and 105.",
    "requirements": {
      "children": [
        ('ENG', '103'),
        ('ENG', '105')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 60.",
    "requirements": {
      "children": [
        ('course', '060')
      ],
      "relationship": "and"
    }
},
{
    "text": "C- or better in Chemistry 2B.",
    "requirements": {
      "children": [
        ('CHE', '002B')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 1.",
    "requirements": {
      "children": [
        ('course', '001')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 101 and 102 (or equivalent course in research methods).",
    "requirements": {
      "children": [
        ('course', '101')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 3 or University Writing Program 1.",
    "requirements": {
      "children": [
        ('course', '003'),
        ('UWP', '001')
      ],
      "relationship": "or"
    }
},
{
    "text": "course 101, 102 (or equivalent course in research methods), and 140.",
    "requirements": {
      "children": [
        ('course', '101'),
        ('course', '140')
      ],
      "relationship": "and"
    }
},
{
    "text": "courses 116AL, and 116B (may be taken concurrently).",
    "requirements": {
      "children": [
        ('course', '116AL')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 3 or Science and Technology Studies 1 or equivalent.",
    "requirements": {
      "children": [
        ('course', '003')
      ],
      'relationship': 'and'
    }
},
{
    "text": "course 100; course 140A recommended.",
    "requirements": {
      "children": [
        ('course', '100')
      ],
      "relationship": "and"
    }
},
{
    "text": "Engineering 6 or Mathematics 22AL (may be taken concurrently); course 100.",
    "requirements": {
      "children": [
        ('ENG', '006'),
        ('course', '100')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 102 or 104; Biological Sciences 103 or 105.",
    "requirements": {
      "children": [
        {
          'children': [
            ('course', '102'),
            ('course', '104')
          ],
          'relationship': 'or'
        },
        {
          'children': [
            ('BIS', '103'),
            ('BIS', '105')
          ],
          'relationship': 'or'
        }
      ],
      "relationship": "and"
    }
},
{
    "text": "elementary biology recommended.",
    "requirements": None
},
{
    "text": "course 1 or English 3 or equivalent.",
    "requirements": {
      "children": [
        ('course', '001')
      ],
      "relationship": "and"
    }
},
{
    "text": "Course 3 or UWP 1 or equivalent.",
    "requirements": {
      'children': [
        ('course', '003')
      ],
      'relationship': 'and'
    }
},
{
    "text": "course 101, 102 (or equivalent course in research methods), and 140.",
    "requirements": {
      "children": [
        ('course', '101'),
        ('course', '140')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 3, upper division standing or consent of instructor.",
    "requirements": {
      "children": [
        ('course', '003')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 3.",
    "requirements": {
      "children": [
        ('course', '003')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 3, upper division standing or consent of instructor.",
    "requirements": {
      "children": [
        ('course', '003')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 3, upper division standing; course 123 recommended.",
    "requirements": {
      "children": [
        ('course', '003')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 100A or 100B or Psychology 140.",
    "requirements": {
      "children": [
        ('course', '100A'),
        ('course', '100B'),
        ('PSC', '140')
      ],
      "relationship": "or"
    }
},
{
    "text": "course 100A or 100B or Psychology 140.",
    "requirements": {
      "children": [
        ('course', '100A'),
        ('course', '100B'),
        ('PSC', '140')
      ],
      "relationship": "or"
    }
},
{
    "text": "course 3, upper division standing or consent of instructor.",
    "requirements": {
      "children": [
        ('course', '003')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 3, upper division standing.",
    "requirements": {
      "children": [
        ('course', '003')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 3 or consent of instructor.",
    "requirements": {
      "children": [
        ('course', '003')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 2.",
    "requirements": {
      "children": [
        ('course', '002')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 101 and 102 (or equivalent course in research methods).",
    "requirements": {
      "children": [
        ('course', '101')
      ],
      "relationship": "and"
    }
},
{
    "text": "course 2 or consent of instructor.",
    "requirements": {
      "children": [
        ('course', '002')
      ],
      "relationship": "and"
    }
},


]
class TestPrereqParser(unittest.TestCase):
  def assertEqualRequirement(self, req1, req2):
    try:
      self.assertEqual(req1['relationship'], req2['relationship'])
      self.assertEqual(len(req1['children']), len(req2['children']))
      self.assertTrue(all((child in req1['children']) for child in req2['children']))
    except TypeError as e:
      self.assertEqual(req1, req2)

  def test_annotated_prerequisites(self):
    incorrect = 0
    for prereq in ANNOTATED_PREREQUISITES[:46]:
      requirements = parse_prereq_text(prereq['text'])
      try:
        print(requirements)
        self.assertEqualRequirement(requirements, prereq['requirements'])
      except AssertionError as e:
        raise e
        incorrect += 1
        print(e)

    print('{} / {} correct'.format(len(ANNOTATED_PREREQUISITES) - incorrect, len(ANNOTATED_PREREQUISITES)))

