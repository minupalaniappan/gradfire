import os
import re
import daviscoursesearch.common.config as config
from daviscoursesearch.common.constants  import SUBJECT_CODES_BY_NAME, SUBJECTS_BY_KEYWORD
from daviscoursesearch.common.tokenizer import match_course_number
from nltk.parse import stanford
from nltk.tree import Tree, ParentedTree

STANFORD_JARS = os.path.join(config.project_root, 'resources/stanford-jars/')
MODEL_PATH = os.path.join(config.project_root, 'resources/stanford-english-model.ser.gz')
os.environ['STANFORD_PARSER'] = STANFORD_JARS
os.environ['STANFORD_MODELS'] = STANFORD_JARS
parser = stanford.StanfordParser(model_path=MODEL_PATH)

PHRASE_LABELS = ['NP', 'ADJP', 'QP', 'NUMP', 'UCP']
CONJUNCTION_LABELS = ['CC']
CONJUNCTIONS = ['and', 'or']

REQ_NODE_IGNORE = ['preferred']
REQ_NODE_INVALIDATORS = ['recommended', 'concurrent', 'concurrently']
REQ_LEAF_INVALIDATORS = ['equivalent']

def find_nearest_parent(pos, requirement_tree):
  """
  Returns node in requirement_tree that corresponds to the
  nearest parent of node with tree position pos.

  Parameters:
    pos: tuple representing position of node in syntax tree
    requirement_tree: dictionary representation of requirements
  """
  nearest_parent = None

  def traverse(node):
    nonlocal pos, nearest_parent
    node_len = len(node['pos'])

    if pos[:node_len] == node['pos']:
      try:
        if node_len > len(nearest_parent['pos']):
          nearest_parent = node
      except TypeError: # nearest_parent not set yet
        nearest_parent = node

    for child in node['children']:
      if isinstance(child, dict):
        traverse(child)

  if requirement_tree['pos']:
    traverse(requirement_tree)
    if nearest_parent and len(pos) == len(nearest_parent['pos']):
      # Parent cannot be same height
      nearest_parent = None
  else:
    nearest_parent = requirement_tree

  return nearest_parent

def insert_relationship(relationship, pos, requirements):
  """
  Inserts relationship, located in syntax tree at pos, into requirements tree at
  correct position.
  Parameters:
    relationship: 'and' / 'or'
    pos: tuple, position of relationship in syntax tree
    requirements: dictionary representaion of requirement tree
  """
  if not requirements['pos']:
    requirements['relationship'] = relationship
    requirements['pos'] = pos
    return
  parent = find_nearest_parent(pos, requirements)
  if not parent:
    # No suitable parent; set incoming relationship to the root
    child = requirements.copy()
    requirements['pos'] = pos
    requirements['relationship'] = relationship
    requirements['children'] = [child]
    return
  elif parent['pos'] == pos:
    # Relationship already exists
    return
  elif parent['relationship'] == relationship:
    # Redundant relationship; ignore
    return

  # Parent is good; insert in appropriate spot
  new_node = {'children': [],
              'relationship': relationship,
              'pos': pos}
  parent['children'].append(new_node)


def insert_requirement(requirement, pos, requirements):
  """
  Inserts requirement into requirements tree at position corresponding to
  syntax tree position pos.
  """
  parent = find_parent(pos, requirements)
  parent['children'].append(requirement)

def remove_pos(requirements):
  """
  Removes 'pos' from each node in requirements tree,
  because it is irrelevant outside of the parsing logic.
  """
  requirements.pop('pos', None)
  for child in requirements['children']:
    if isinstance(child, dict):
      remove_pos(child)

def flatten_relationships(requirements, parent=None):
  """
  Flattens relationships in requirements tree by removing redundant
  and empty relationships.
  """
  while len(requirements['children']) == 1:
    if parent:
      parent['children'].append(requirements['children'][0])
      parent['children'].remove(requirements)
      requirements = requirements['children'][0]
      flatten_relationships(parent)
      if isinstance(requirements, tuple):
        return
    else:
      if isinstance(requirements['children'][0], dict):
        child_rel = requirements['children'][0]['relationship']
        requirements['children'] = requirements['children'][0]['children']
        requirements['relationship'] = child_rel
      else:
        break

  # Flatten immediate children -- can this be refactored so we don't process children twice?
  for child in requirements['children']:
    if isinstance(child, dict):
      if child['relationship'] == requirements['relationship']:
        requirements['children'].remove(child)
        requirements['children'] += child['children']

  # Then recurse
  for child in requirements['children']:
    if isinstance(child, dict):
      flatten_relationships(child, requirements)

  if not requirements['children']:
    requirements = None
  return requirements

def dedupe(requirements):
  """
  Removes duplicate requirements in requirements tree.
  """
  deduped_children = list()
  for child in requirements['children']:
    if isinstance(child, dict):
      deduped_children.append(dedupe(child))
    else:
      if child not in deduped_children:
        deduped_children.append(child)

  requirements['children'] = deduped_children
  return requirements

def remove_invalidated_leaves(requirements):
  """
  Removes leaf invalidators and their preceding children from requirements['children'].
  """
  for invalidator in REQ_LEAF_INVALIDATORS:
    try:
      leaf_invalidator_idx = requirements['children'].index(invalidator)
      requirements['children'].pop(leaf_invalidator_idx) # Remove the invalidator
      requirements['children'].pop(leaf_invalidator_idx - 1) # and the leaf it invalidates
    except ValueError:
      pass

def remove_invalidated_courses(requirements, invalidated_courses):
  """
  Removes invalidated courses from requirements tree
  """
  valid_children = list()
  for child in requirements['children']:
    if isinstance(child, dict):
      remove_invalidated_courses(child, invalidated_courses)
      try:
        remove_invalidated_leaves(child)
      except IndexError:
        # Child invalidates the last parsed course
        if valid_children:
          last_child = valid_children[-1]
          if isinstance(last_child, dict):
            remove_last_course(valid_children[-1])
          else:
            valid_children.pop()

      if child['children']: # prevents {'children': [], 'relationship': 'or'} from showing up
        valid_children.append(child)
    elif child not in invalidated_courses:
      valid_children.append(child)

  requirements['children'] = valid_children

def add_leaf_exception(syntax_tree, leaf_idx, exception_seq):
  """
  Adds to leaf to exception_seq
  """
  tree_pos = syntax_tree.leaf_treeposition(leaf_idx)
  # tree[tree_pos[:-2]] always represents leaf's containing phrase. parent() call is necessary
  # for the next level above, because can't assume that trimming off the tuple
  # will always yield the correct parent

  parent = syntax_tree[tree_pos[:-2]].parent()
  closest_np_or_root = syntax_tree[0]
  while parent and closest_np_or_root == syntax_tree[0]:
    if parent.label() in PHRASE_LABELS:
      closest_np_or_root = parent
    parent = parent.parent()
  exception_seq.append(closest_np_or_root)

def parse_requirements(tree, initial_subject=None):
  invalidated_nodes = []
  ignored_nodes = []

  for idx, leaf in enumerate(tree.leaves()):
    if leaf in REQ_NODE_INVALIDATORS:
      add_leaf_exception(tree, idx, invalidated_nodes)
    elif leaf in REQ_NODE_IGNORE:
      add_leaf_exception(tree, idx, ignored_nodes)

  requirements = {'children': [], 'relationship': 'and', 'pos': None}
  invalidated_courses = []
  subject = initial_subject
  subject_candidate = ([], set()) # (['kw1', 'kw2', ...], set('SUBJ1', 'SUBJ2', ...))
  idx = 0
  leaves = tree.leaves()
  treepositions = tree.treepositions()
  course_found = False

  def populate_requirements(node, node_invalidated=False):
    nonlocal idx, subject_candidate, subject, requirements, invalidated_courses, course_found
    pos = treepositions[idx]
    idx = idx + 1

    if isinstance(node, Tree):
      label = node.label()
      if label in PHRASE_LABELS and not node_invalidated:
        for child in node:
          if child.label() in CONJUNCTION_LABELS:
            relationship = child.leaves()[0]
            insert_relationship(relationship, pos, requirements)

      for child in node:
        if node_invalidated or child in invalidated_nodes:
          populate_requirements(child, node_invalidated=True)
        elif child not in ignored_nodes:
          populate_requirements(child)
    else:
      course_number_match = match_course_number(node, starting_with_subject=False)
      if course_number_match:
        # Course numbers immediately follow subject names, so try to update
        # 'subject' when a course number is matched.
        candidate_words, subjects = subject_candidate
        subject_phrase = ' '.join([word.title() for word in candidate_words])

        if candidate_words and candidate_words[0].startswith('course'):
          subject = 'course'
        elif subject_phrase in SUBJECT_CODES_BY_NAME.keys():
          subject = SUBJECT_CODES_BY_NAME.get(subject_phrase)
        elif len(subjects) == 1:
          subject = next(iter(subjects))
        if subject:
          # Reset subject candidate once a subject is identified
          subject_candidate = ([], set())
      else:
        # Process keyword
        if re.match(r'[a-z]+', node) and node not in CONJUNCTIONS:
          node_subjects =  set(SUBJECTS_BY_KEYWORD.get(node, []))
          if subject_candidate[1]:
            # Continue narrowing down existing subject candidate
            common_subjects = node_subjects & subject_candidate[1]
            subject_candidate = (subject_candidate[0] + [node], common_subjects)
          else:
            # node is beginning of new subject_candidate
            subject_candidate = ([node], node_subjects)

      if node in REQ_LEAF_INVALIDATORS:
        parent = find_nearest_parent(pos, requirements)
        parent['children'].append(node)

      if subject and course_number_match:
        course_found = True
        # If no requirement yet, and we've already matched a course number,
        course = (subject, course_number_match.normalized_value)
        if node_invalidated:
          invalidated_courses.append(course)
        else:
          try:
            parent = find_nearest_parent(pos, requirements)
            if pos == treepositions[-1] and parent == requirements and len(leaves) > 1: # Handles case observed in
              pos = tree.leaf_treeposition(len(leaves) - 2)
              parent = find_nearest_parent(pos, requirements)
            parent['children'].append(course)
          except TypeError:
            # This occurs when no conjunctions are used in the prerequisite string.
            # Default to AND
            requirements['children'].append(course)

  populate_requirements(tree)
  remove_pos(requirements)
  dedupe(requirements)
  if not requirements['children']:
    requirements = None

  if invalidated_nodes and not course_found:
    # Invalidates a previous course; -1 used as marker
    invalidated_courses = [-1]

  return requirements, subject, invalidated_courses

def remove_last_course(requirements):
  try:
    if not isinstance(requirements['children'][-1], dict):
      requirements['children'] = requirements['children'][:-1]
    else:
      remove_last_course(requirements['children'][-1])
  except IndexError:
    pass

def normalize_relationship(requirements):
  # Default to 'and' relationship for any node with single leaf child
  if len(requirements['children']) == 1 and not isinstance(requirements['children'][0], dict):
    requirements['relationship'] = 'and'
  else:
    for child in requirements:
      if isinstance(child, dict):
        normalize_relationship(child)

PREREQUISITE_TEXT_MISTAKES = {
  "it's equivalent": 'its equivalent' # Looking at you, STA 137...
}

def split_normalize_prereq_text(text):
  normalized_text = ' '.join([word.strip().lower() for word in text.split()])
  for mistake, correction in PREREQUISITE_TEXT_MISTAKES.items():
    normalized_text = normalized_text.replace(mistake, correction)

  sentence_split = [sentence.strip() for sentence in re.split('\.|;|\(|\)', normalized_text) if sentence.strip()]
  return sentence_split

def parse_prereq_text(text):
  sentences = split_normalize_prereq_text(text)

  requirements = {
    'relationship': 'and',
    'children': []
  }
  starting_subject = None
  invalidated_courses = list()

  for sentence in sentences:
    sentence_trees = parser.raw_parse(sentence)
    tree = ParentedTree.convert(next(sentence_trees))

    (sentence_requirements,
    starting_subject,
    sentence_invalidated_courses) = parse_requirements(tree, starting_subject)
    if sentence_invalidated_courses == [-1]:
      # Sentence invalidates previous course
      remove_last_course(requirements)
    else:
      invalidated_courses += sentence_invalidated_courses

    if sentence_requirements:
      requirements['children'].append(sentence_requirements)

  remove_invalidated_courses(requirements, invalidated_courses)
  requirements = flatten_relationships(requirements)
  if requirements:
    normalize_relationship(requirements)

  return requirements