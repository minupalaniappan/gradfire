from .course_utils import honors_equivalents, courses_from_text, expand_course_number_range, units_for_course, units_for_course_range
from ...common.tokenizer import match_course_number

def normalize_course_node(node, parent):
  try:
    nrml_components = [match_course_number(number, starting_with_subject=False).normalized_value
      for number in node['number'].split('-') if number]
  except AttributeError:
    return None
  if len(nrml_components) == 2: # does this node contain a course number range?
    # Select minimum units from valid courses
    node['number'] = '-'.join(nrml_components)
    course_numbers = expand_course_number_range(node['subject'], node['number'])
    parent['children'] += [{'subject': node['subject'], 'number': number} for number in course_numbers]
    parent['children'].remove(node)
    if parent['rel'] == 'AND':
      units_for_courses = [units_for_course(node['subject'], number) for number in course_numbers]
      return tuple([sum(units) for units in zip(*units_for_courses)]) # element-wise sum
    else: # rel is OR
      return units_for_course_range(node['subject'], nrml_components)
  else:
    node['number'] = ''.join(nrml_components)
    return units_for_course(node['subject'], node['number'])

def expand_course_options(node, parent=None, root=None):
  if not root:
    root = node

  try:
    for child in node['children'].copy():
      expand_course_options(child, node, root)
  except KeyError:
    if node.get('course_options', None):
      courses = courses_from_text(node['course_options'])
      for course in courses:
        course_obj = {
          'subject': course[0],
          'number': course[1]
        }
        parent['children'].append(course_obj)
      parent['children'].remove(node) # Remove course options

    if node.get('subject'):
      honors_eq = honors_equivalents(node['subject'], node['number'].upper())
      if honors_eq:
        # import ipdb; ipdb.set_trace()
        if parent['rel'] == 'OR':
          parent['children'] += [course for course in honors_eq if course not in parent['children']]
        else:
          honors_equiv_or_group = dict.fromkeys(root.keys())
          for key, value in root.items():
            if key != 'children':
              honors_equiv_or_group[key] = value
          honors_equiv_or_group['name'] = '__honors__'
          honors_equiv_or_group['rel'] = 'OR'
          honors_equiv_or_group['children'] = [node] + honors_eq
          parent['children'] += [honors_equiv_or_group]
          parent['children'].remove(node)


def flatten_relationships(requirements, parent=None):
  """
  Flattens relationships in requirements tree by removing redundant
  and empty relationships.
  """
  if 'children' in requirements:
    children_flattened = list()
    for child in requirements['children']:
      child = flatten_relationships(child)

      flatten_by_and = ('children' in child and len(child['children']) and child['rel'] == 'AND' and requirements['rel'] == child['rel'])
      if flatten_by_and:
        print(requirements['rel'], child)
        children_flattened += child['children']
      else:
        children_flattened.append(child)

    requirements['children'] = children_flattened

  return requirements