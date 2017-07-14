from ...common import constants as const
from ...common.tokenizer import tokenize, match_course_number
from ..models.models import CourseQuery, PersonalizedFilters, TokenQueries, filter_queries_by_name, personalized_filters_by_name
from .course_utils import course_query, add_enrollment_aggregates, add_average_grade_to_course_query
from .db_utils import conn as db_conn
from .utils import previous_term, split_and_strip_nonalpha, redis_lru, timeit
from ...common import config
from collections import OrderedDict
from itertools import chain
from datetime import datetime
import json
import logging
import os
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

log_file = os.path.join(config.logging_dir, 'query.log')
log_handler = logging.FileHandler(log_file)
logger.addHandler(log_handler)

def _course_number_token_from_keywords(keywords):
  tokens = [match_course_number(kw, starting_with_subject=False) for kw in keywords]
  try:
    return next(token for token in tokens if token)
  except StopIteration:
    return None

def _course_query_for_search(search_query, tokens, instructors):
  """
  Returns CourseQuery object with conditions based on tokens matched in query,
  as well as full-text matches for subject, title, and description
  """
  matched_keywords = list(chain(*[token.keywords for token in tokens]))
  query_lower = split_and_strip_nonalpha(search_query)
  unmatched_keywords = [kw for kw in query_lower if kw not in matched_keywords]
  query = CourseQuery()
  ordering = list()
  subject_candidates = []

  if not any(token.type == 'subject_code' for token in tokens):
      subject_candidates, _, subject_matched_keywords = subject_candidates_for_keywords(unmatched_keywords)
      unmatched_keywords = [re.sub(r'[^A-Za-z0-9]', '', kw) for kw in unmatched_keywords if kw not in subject_matched_keywords]
      unmatched_keywords = [kw for kw in unmatched_keywords if kw]
      if subject_candidates:
        subject_values = ','.join([str((idx, subject)) for subject, idx in enumerate(subject_candidates)])
        query = query.merge(CourseQuery(
          fields=(('subjects.subject_rank subject_rank'),),
          joins=(('join', '(values {0}) as subjects (subject, subject_rank) on subjects.subject = courses.subject'.format(subject_values)),),))
        ordering.append(('subject_rank', False)) # (key, reverse)

        course_number = _course_number_token_from_keywords(unmatched_keywords)
        if course_number:
          tokens.append(course_number)
  if instructors:
    hard_filter = (len(subject_candidates) == 0 and not tokens)
    query = query.merge(_course_query_for_instructors(instructors, hard_filter=hard_filter))
  elif unmatched_keywords:
    query.fields += ("ts_rank(title_desc_tsv, tsquery) rank",)
    query.joins += (('join lateral', "to_tsquery('english', %s) tsquery on true", ' | '.join(unmatched_keywords)),)
    query.fields += ("""(CASE WHEN ts_rank(title_desc_tsv, tsquery) > 1e-20 THEN
      ts_headline('english', courses.title, tsquery)
      ELSE courses.title END) title_headline""",
      """(CASE WHEN ts_rank(title_desc_tsv, tsquery) > 1e-20 THEN
        ts_headline('english', courses.description, tsquery)
        ELSE courses.description END) desc_headline""")
    ordering = [('rank', True)] + query.order_by

    if not tokens and not subject_candidates:
      query.where_conditions += (('ts_rank(title_desc_tsv, tsquery) > 0.1',),)
  if not any(token.type == 'course_number' for token in tokens):
    query.where_conditions += (('substring(courses.number, 0, 4)::integer < 200',),)
  return query, ordering

def _sql_ordering_for_tokens(tokens):
  return ('courses.subject', 'courses.number')

def _course_query_for_filters(filters, tokens):
  query = CourseQuery()
  ordering = list()
  for fltr, value in filters.items():
    try:
      filtered_query = filter_queries_by_name[fltr](value)
      if isinstance(filtered_query, tuple):
        filtered_query, filter_ordering = filtered_query
        ordering += filter_ordering

      query = query.merge(filtered_query)
    except KeyError:
      pass

  if not ('ld' in filters or 'ud' in filters or any(token.type == 'course_number' for token in tokens)):
    query = query.merge(filter_queries_by_name['lower_and_upper'](value))

  for code, area_name in const.GE_AREAS_BY_OASIS_ABBRV.items():
    if code in filters:
      area_query = CourseQuery(where_conditions=[('ARRAY[%s]::text[] <@ courses.ge_areas', area_name)])
      query = query.merge(area_query)

  return query, ordering

# def _requirement_filter/

def _course_query_for_personalized_filters(filters, user_meta):
  query = CourseQuery()

  for fltr, value in filters.items():
    try:
      query = query.merge(personalized_filters_by_name[fltr](user_meta))
    except KeyError:
      pass

  return query

def _log_search_query(query, tokens):
  timestamp = datetime.now().strftime('%m/%d/%Y:%H:%M:%S')
  log_info = {
    'timestamp': timestamp,
    'query': query,
    'tokens': [
      {'type': token.type,
       'keywords': token.keywords,
       'value': token.normalized_value
      } for token in tokens
    ]
  }
  logger.debug(json.dumps(log_info))

def subject_candidates_for_keywords(keywords, prefix_match=False):
  cur = db_conn.cursor()
  subject_candidate_sets = list()
  candidate_tsquery = ' | '.join(keywords)

  query = """SELECT * FROM (SELECT (keywords ~* (%s) OR code ~* %s) prefix_match, code, ts_rank(tsv, query, 2) rnk, ts_headline('english', name, query) name_headline, ts_headline('english', keywords, query, 'StartSel = <, StopSel = >') matches
      FROM subjects, to_tsquery('english', %s) query
      ORDER BY rnk DESC, (keywords ~* %s), (code ~* %s)) AS tmp WHERE rnk > 1e-10 OR prefix_match"""

  for idx in range(0, len(keywords)):
    fields = ('\\m' + keywords[idx], '^' + keywords[idx], candidate_tsquery, '^' + keywords[idx], '^' + keywords[idx])
    cur.execute(query, fields) # 1e-10 hack is due to issue where ts_rank returns nonzero for 0 matches
    subject_rankings = cur.fetchall()
    subject_candidates = [(code, nameHeadline, re.findall('<(.+?)>', matches)) for prefix_match, code, rank, nameHeadline, matches in subject_rankings if prefix_match or rank > 0]
    if subject_candidates:
      subject_candidate_sets.append(subject_candidates)

    candidate_tsquery = '{} & {}'.format(' | '.join(keywords[:idx + 1]), ' | '.join(keywords[idx + 1:]))
  if subject_candidate_sets:
    # Assumption: Best set of subject candidates will be that with the fewest matches
    best_candidate_set = min(subject_candidate_sets, key=lambda candidates: len(candidates))
    codes, headlines, matches = list(zip(*best_candidate_set))
    matches = list(chain(*matches))
    return codes, headlines, matches
  else:
    return [], [], []

# 30000 derived from select 3 * count(distinct component) from (select regexp_split_to_table(name, ' ') from instructors) as tmp(component);
# from populate_caches script, est. 3
@redis_lru(capacity=30000)
@timeit
def instructors_for_query(query):
  """
  Returns list of tuple (id, name) for each instructor whose name shares a keyword with the query
  """
  keywords = ['{}'.format(kw.lower()) for kw in query.split()]
  if not keywords:
    return []

  cur = db_conn.cursor()
  cur.execute("""SELECT instructors_split.id, name, COUNT(keywords.word) matched_kw_count
    FROM
      (SELECT id, name, name_components FROM instructors WHERE %s && name_components)
    AS instructors_split
    JOIN unnest(%s) AS keywords(word)
      ON ARRAY[keywords.word]::text[] <@ instructors_split.name_components
    WHERE EXISTS (SELECT 1 FROM courses WHERE courses.instructor_id = instructors_split.id
      AND courses.term_year >= %s AND courses.term_month >= %s)
    GROUP BY instructors_split.id, name
    ORDER BY matched_kw_count DESC;""", (keywords, keywords, *const.LOWEST_TERM))
  instructors_and_count = cur.fetchall()
  if not instructors_and_count:
    return []
  max_count = instructors_and_count[0][2]
  has_top_choice = False

  for instr_id, name, count  in instructors_and_count:
    if count < max_count:
      has_top_choice = True
      break

  if has_top_choice:
    instr_id, name, matched_kw_count = instructors_and_count[0]
    return [(instr_id, name, matched_kw_count == len(name.split()))]
  else:
    instructor_list = [(instr_id, name, count == len(name.split())) for instr_id, name, count in instructors_and_count]
    return sorted(instructor_list, key=lambda instr: instr[1])

def ge_areas_for_query(courses_and_sections, user_meta, selected_area=None):
  aggregate_areas = set(list(chain(*[course['ge_areas'] for course in courses_and_sections])))
  area_completion = OrderedDict([(const.GE_AREA_SHORTNAMES.get(area, area), False) for area in aggregate_areas])

  if user_meta:
    cur = db_conn.cursor()
    cur.execute("SELECT ge_area FROM students_ge_progress WHERE student_id = %s AND is_complete", (user_meta['id'],))
    relevant_completed_areas = [row[0] for row in cur.fetchall() if row[0] in area_completion]
    for area in relevant_completed_areas:
      area_completion[area] = True

  return sorted(area_completion.items(), key=lambda kv: (kv[1], kv[0]))

def _course_query_for_instructors(instructors, hard_filter=True):
  instructor_ids = [instructor[0] for instructor in instructors]
  if hard_filter:
    return CourseQuery(where_conditions=[('courses.instructor_id = ANY(ARRAY{})'.format(instructor_ids),)])
  else:
    return CourseQuery(order_by=['courses.instructor_id = ANY(ARRAY{}) DESC NULLS LAST'.format(instructor_ids)])

def term_for_search(tokens, request_args):
  year, month = const.ACTIVE_TERM

  try:
    year = int(next(token.normalized_value for token in tokens if token.type == 'term_year'))
  except StopIteration:
    pass
  try:
    month = int(next(token.normalized_value for token in tokens if token.type == 'term_month'))
  except StopIteration:
    pass

  if 'term_year' in request_args and 'term_month' in request_args:
    return (int(request_args['term_year']), int(request_args['term_month']))
  else:
    return (year, month)

# Request arguments supercede query tokens.
# This mapping looks redundant now, but is in place for explicitness and expected future additions.
DISABLED_TOKEN_TYPES_BY_REQUEST_ARG = {
  'term_year': 'term_year',
  'term_month': 'term_month'
}

def personalize_sql_query_for_search(course_query, request_args, user_meta):
  personalized_filter_query = _course_query_for_personalized_filters(request_args, user_meta)
  course_query = course_query.merge(personalized_filter_query)
  return course_query

def add_major_requirements_to_search(course_query, user_id):
  course_query.fields += ('(mrc.is_hard_requirement = false) student_major_option', '(mrc.is_hard_requirement = true) student_major_hard_req', '(sgp.ge_area IS NOT NULL) student_unsatisfied_ge')

  course_query.joins += (
    ('JOIN', """students ON students.user_id = %s""", user_id),
    ('JOIN', """students_programs sp ON sp.user_id = students.user_id"""),
    ('LEFT JOIN', """majors_required_courses mrc ON
      mrc.program_id =  sp.program_id AND
      courses.subject = mrc.subject AND
      courses.number = mrc.number""",),
    ('LEFT JOIN', """students_ge_progress sgp ON sgp.student_id = %s
      AND sgp.is_complete = false
      AND sgp.ge_area = ANY(courses.ge_areas)""", user_id),)

def add_answer_count_to_search(course_query):
  course_query.fields += ("""(SELECT count(1) FROM course_answers a
    JOIN course_questions q ON q.subject = courses.subject AND q.number = courses.number AND q.id = a.question_id) answer_count""",)

@redis_lru(slice=slice(2))
def courses_and_sections_for_search(request_args, user_meta, instructors, fall_back=True):
  query = request_args.get('q', '')
  if not query:
    return []

  tokens = tokenize(query)
  if config.debug:
    print(tokens)
  _log_search_query(query, tokens)
  keyword_sql_query, ordering = _course_query_for_search(query, tokens, instructors)
  for arg, value in request_args.items():
    disabled_token_type = DISABLED_TOKEN_TYPES_BY_REQUEST_ARG.get(arg)
    if disabled_token_type:
      tokens = [token for token in tokens if token.type != disabled_token_type]

  for token in tokens:
    keyword_sql_query = keyword_sql_query.merge(TokenQueries.query_for_token(token))
  filter_sql_query, ordering = _course_query_for_filters(request_args, tokens)
  sql_query = filter_sql_query.merge(keyword_sql_query)
  if user_meta and user_meta['role'] == 'student':
    sql_query = personalize_sql_query_for_search(sql_query, request_args, user_meta)

  if sql_query == CourseQuery():
    return []
  sql_query.order_by += ['total_max_enrollment DESC NULLS LAST', 'subject', 'number', 'title']

  term = term_for_search(tokens, request_args)
  sql_query.where_conditions += (('courses.from_transcript = false',), ('courses.term_year = %s AND courses.term_month = %s', *term))
  add_average_grade_to_course_query(sql_query)
  add_enrollment_aggregates(sql_query)
  add_answer_count_to_search(sql_query)
  if user_meta and user_meta['role'] == 'student':
    add_major_requirements_to_search(sql_query, user_meta['id'])

  courses_and_sections = course_query(*sql_query.sql_and_values())
  if ordering:
    ordering.reverse()
    for key, reverse in ordering:
      courses_and_sections = sorted(courses_and_sections, key=lambda course: course[key], reverse=reverse)
  # look up to two terms backwards if 0 results
  if fall_back and (not instructors and not courses_and_sections and term != previous_term(*previous_term(*previous_term(*previous_term(*previous_term(*previous_term(*const.ACTIVE_TERM))))))
    and not any(token.type == 'term_year' or token.type == 'term_month' for token in tokens)):
    request_args['term_year'], request_args['term_month'] = previous_term(*term)
    return courses_and_sections_for_search(request_args, user_meta, instructors)

  return courses_and_sections
