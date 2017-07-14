from ...common import constants as const
from copy import deepcopy
from itertools import chain
import collections

class CourseQuery(object):
  def __init__(self, table_alias=None, additonal_from=None, condition=None, fields=None, subquery=None, joins=None,
    where_conditions=None, group_by=None, order_by=None, limit=None, offset=None):
    """
    Parameters:
      table_alias: string, SELECT * FROM courses table_alias
      condition: string e.g. DISTINCT ON ...
      fields: tuple column names
      subquery: CourseQuery object to substitute in FROM statement
      join: optional tuple
        (sql string omitting 'JOIN' prefix, (optional) value1, value2, ...)
      where_conditions: sequence of condition tuples (sql, value)
      order_by: tuple of conditions following 'ORDER BY'
      limit: number following 'LIMIT'

      everything is optional
    """
    if not table_alias:
      table_alias = 'courses'
    self.table_alias = table_alias

    if not additonal_from:
      additonal_from = tuple()
    self.additonal_from = additonal_from

    if not condition:
      condition = ''
    self.condition = condition

    if not fields:
      fields = ('courses.*',)
    self.fields = fields

    self.subquery = subquery

    if not joins:
      joins = tuple()
    self.joins = joins

    if not where_conditions:
      where_conditions = tuple()
    self.where_conditions = where_conditions

    if not group_by:
      group_by = tuple()
    self.group_by = group_by

    if not order_by:
      order_by = list()
    self.order_by = order_by

    self.limit = limit
    self.offset = offset

  def __eq__(self, other):
    return self.__dict__ == other.__dict__

  def count_query(self):
    query = deepcopy(self)
    query.fields = ('COUNT(DISTINCT (courses.term_year, courses.term_month, courses.subject, courses.number))',)
    query.condition = ''
    query.order_by = list()
    query.offset = None
    return query

  def merge(self, other):
    # TODO make this DRY
    table_alias = self.table_alias
    if not table_alias:
      table_alias = other.table_alias

    subquery = self.subquery
    if not subquery:
      subquery = other.subquery

    condition = self.condition
    if not condition:
      condition = other.condition

    joins = self.joins + other.joins

    limit = self.limit
    if not limit:
      limit = other.limit

    offset = self.offset
    if not offset:
        offset = other.offset

    return CourseQuery(
      table_alias=table_alias,
      additonal_from=self.additonal_from + other.additonal_from,
      condition=condition,
      subquery=subquery,
      fields=tuple(set(self.fields + other.fields)),
      joins=joins,
      where_conditions=tuple(self.where_conditions) + tuple(other.where_conditions),
      order_by=self.order_by + other.order_by,
      group_by=self.group_by + other.group_by,
      limit=limit,
      offset=offset)

  def _sql_and_values_tuple_or_str(self, query_component, delimeter=','):
    sql_fields = ([field[0] for field in query_component if isinstance(field, tuple)] +
      [field for field in query_component if not isinstance(field, tuple)])
    sql = delimeter.join(sql_fields)
    values = list(chain(*[field[1:] for field in query_component if isinstance(field, tuple)]))

    return sql, values

  def sql_and_values(self):
    values = list()

    if not self.subquery:
      from_ = 'courses {}'.format(self.table_alias)
    else:
      subquery_sql, subquery_vals = self.subquery.sql_and_values()
      values += subquery_vals
      from_ = '({}) as {}'.format(subquery_sql, self.table_alias)

    fields_sql, fields_values = self._sql_and_values_tuple_or_str(self.fields)
    values += fields_values

    query = 'SELECT {} {} FROM {} '.format(self.condition, fields_sql, from_)
    if self.joins:
      query += ' '.join([' '.join(join_type_and_sql[:2]) for join_type_and_sql in self.joins])
      values += chain(*[join[2:] for join in self.joins if len(join) > 2])

    add_from_sql, add_from_values = self._sql_and_values_tuple_or_str(self.additonal_from)
    if add_from_sql:
      add_from_sql = ' ,' + add_from_sql
    values += add_from_values

    query += add_from_sql
    if self.where_conditions:
      sql_conditions = list()
      condition_values = list()

      for condition in self.where_conditions:
        try:
          sql, *corresp_values = condition
          if isinstance(corresp_values, CourseQuery):
            # Value is a subquery; format its sql and add its values in order
            subquery_sql, subquery_vals = corresp_values.sql_and_values()
            sql = sql.replace('%s', subquery_sql)
            condition_values += subquery_vals
          else:
            if isinstance(corresp_values, collections.Iterable) and not isinstance(corresp_values, str):
              condition_values += list(corresp_values)
            else:
              condition_values.append(corresp_values)

          sql_conditions.append(sql)
        except ValueError:
          # where condition is sql-only; add it to sql_conditions
          if isinstance(condition, str):
            sql_conditions.append(condition)
          else:
            sql_conditions.append(condition[0])

      query += ' WHERE {}'.format(' AND '.join(sql_conditions))
      values += condition_values

    if self.group_by:
      query += ' GROUP BY {}'.format(','.join(self.group_by))

    if self.order_by:
      query += ' ORDER BY {}'.format(','.join(self.order_by))


    if self.limit:
      query += ' LIMIT {}'.format(self.limit)

    if self.offset:
      query += ' OFFSET {}'.format(self.offset)

    return (query, values)

def completed_courses_join_tuple(user_id, join_type):
  """
  Tuple for CourseQuery 'joins' field that will.
  Parameters:
    user_id (int): User id
    join_type (str): JOIN/INNER JOIN/LEFT JOIN/WEIRD POSTGRES JOIN
  """
  return ((join_type, """students_completed_courses scc ON
    scc.course_id = courses.id
    AND scc.student_id = %s""", (user_id, )),)

class FilterConditions(object):
    @classmethod
    def ge_areas(cls, ge_areas):
      """
      Parameters:
          ge_areas: Double-comma separated list of ge_area names to filter on
      """
      ge_area_seq = ge_areas.split(',,')
      array_elements = ','.join(['%s' for a in ge_area_seq])
      return CourseQuery(where_conditions=[('ARRAY[{}]::text[] && courses.ge_areas'.format(array_elements), ge_area_seq)])

    @classmethod
    def term_at_least(cls, term):
      return CourseQuery(where_conditions=[('courses.term_year >= %s AND courses.term_month >= %s', *term)])

    @classmethod
    def term_year(cls, year):
      return CourseQuery(where_conditions=[('courses.term_year = %s', year)])

    @classmethod
    def term_month(cls, term_month):
      return CourseQuery(where_conditions=[('courses.term_month = %s', term_month)])

    @classmethod
    def seats_available(cls, *args):
      return CourseQuery(where_conditions=[('(total_available_seats - total_waitlist_length) > 0',)])

    @classmethod
    def lower_division(cls, value):
      base_condition = 'substring(courses.number, 0, 4)::integer <@ int4range(0,100)'
      if value == '0':
        base_condition = 'NOT ' + base_condition
      return CourseQuery(where_conditions=[(base_condition,)])

    @classmethod
    def upper_division(cls, value):
      base_condition = 'substring(courses.number, 0, 4)::integer <@ int4range(100,200)'
      if value == '0':
        base_condition = 'NOT ' + base_condition
      return CourseQuery(where_conditions=[(base_condition,)])

    @classmethod
    def lower_and_upper(cls, *args):
      return CourseQuery(where_conditions=[('substring(courses.number, 0, 4)::integer <@ int4range(0,200)',)])

    @classmethod
    def has_grade_data(cls, *args):
      return CourseQuery(where_conditions=[('EXISTS (SELECT 1 FROM courses_grades cg WHERE cg.subject = courses.subject AND cg.number = courses.number AND cg.title = courses.title)',)])

    @classmethod
    def no_prerequisites(cls, *args):
      return CourseQuery(where_conditions=[("""prerequisites = ''
        OR lower(prerequisites) = 'none'""")])

    SORT_FIELDS = ['size', 'avg_grade', 'number', 'seats_avail']
    @classmethod
    def sort(cls, field):
      if field not in cls.SORT_FIELDS:
        return CourseQuery()

      if field == 'avg_grade':
        return CourseQuery(
          order_by=['avg_grade_order ASC NULLS LAST'])

      if field == 'number':
        return CourseQuery(order_by=['subject, number'])

      if field == 'seats_avail':
        return CourseQuery(order_by=['(total_available_seats::float / NULLIF(total_max_enrollment, 0)) DESC NULLS LAST'])

      return CourseQuery(), [('total_max_enrollment', True)] # order_by=['total_max_enrollment desc nulls last']

filter_queries_by_name = {
    'ge_areas': FilterConditions.ge_areas,
    'seats_avail': FilterConditions.seats_available,
    'ld': FilterConditions.lower_division,
    'ud': FilterConditions.upper_division,
    'lower_and_upper': FilterConditions.lower_and_upper,
    'term_year': FilterConditions.term_year,
    'term_month': FilterConditions.term_month,
    'grades': FilterConditions.has_grade_data,
    'sort': FilterConditions.sort
}

"""
SELECT * from courses c1  # support table alias
    JOIN major_courses mc ON mc.major_id = 9 AND mc.course_number = c1.number AND mc.course_subject = c1.subject
WHERE NOT EXISTS
    (SELECT 1 FROM courses c2
        JOIN students_completed_courses scc on scc.course_id = c2.id
    WHERE c1.subject = c2.subject AND c1.number = c2.number);
"""
class PersonalizedFilters(object):
    @classmethod
    def major(cls, user_meta):
      return CourseQuery(
        where_conditions=[
          ('mrc.major_id IS NOT NULL',),
          (
            """NOT EXISTS (
            SELECT 1 FROM courses c
            JOIN students_completed_courses scc ON scc.course_id = c.id AND scc.student_id = %s
            WHERE c.subject = courses.subject AND c.number = courses.number)""", user_meta['id'])])

    @classmethod
    def general_ed(cls, user_meta):
        return CourseQuery(
            # fields=('sgp.ge_area', '*'),
            where_conditions=(('sgp.ge_area IS NOT NULL',),)
            )

    @classmethod
    def prerequisites(cls, user_meta):
      return CourseQuery(
        where_conditions=(("""
          ((WITH RECURSIVE prereq_satisfied AS (
              SELECT 0, parent_req, array_agg(sts) child_satisfactions FROM

                 (SELECT DISTINCT ON (id) cp.*, (scc.student_id IS NOT NULL OR sce.student_id IS NOT NULL) sts FROM courses_prerequisites cp
                 LEFT JOIN courses c ON c.subject = cp.req_subject AND c.number = cp.req_number
                 LEFT JOIN students_completed_courses scc ON scc.student_id = %s AND scc.course_id = c.id
                 LEFT JOIN students_course_equivalences sce ON sce.student_id = %s AND sce.subject = c.subject AND sce.number = c.number
                 WHERE cp.course_id = courses.id AND cp.rel IS NULL ORDER BY id, sts DESC) course_satisfaction

               GROUP BY parent_req
               UNION
               SELECT id, cp.parent_req,
                 ARRAY[((cp.rel = 'AND' AND true = all(ps.child_satisfactions))
                       OR cp.rel = 'OR' AND true = any(ps.child_satisfactions))]::boolean[]
               FROM prereq_satisfied ps
               JOIN courses_prerequisites cp ON ps.parent_req = cp.id
               WHERE cp.parent_req IS NOT NULL)

            SELECT ((root_req.rel = 'OR' AND true = ANY(array_agg(child_satisfactions))) OR
             (root_req.rel = 'AND' and TRUE = ALL(array_agg(child_satisfactions))))
            FROM
             (SELECT parent_req, unnest(child_satisfactions) FROM prereq_satisfied)
             ps(parent_req, child_satisfactions)
            JOIN courses_prerequisites root_req ON root_req.course_id = courses.id AND root_req.parent_req IS NULL AND ps.parent_req = root_req.id
            GROUP BY ps.parent_req, root_req.rel) = true or
            NOT EXISTS (SELECT 1 FROM courses_prerequisites WHERE course_id = courses.id)
            OR courses.prerequisites ILIKE '%%concurrent%%n')
            """,
          user_meta['id'], user_meta['id']),))

    @classmethod
    def hide_completed_courses(cls, user_meta):
      return CourseQuery(
          where_conditions=(
            ("""NOT EXISTS
                (SELECT 1 FROM students_completed_courses scc
                  JOIN courses c2 on scc.course_id = c2.id
                  WHERE scc.student_id = %s
                  AND courses.subject = c2.subject
                  AND courses.number = c2.number)""", user_meta['id']),
            ("""NOT EXISTS
              (SELECT 1 FROM students_course_equivalences sce
                WHERE sce.student_id = %s
                AND sce.subject = courses.subject
                AND sce.number = courses.number)""", user_meta['id'])
            )
        )
personalized_filters_by_name = {
    'pslz_major': PersonalizedFilters.major,
    'pslz_ge': PersonalizedFilters.general_ed,
    'pslz_prereq': PersonalizedFilters.prerequisites,
    'pslz_no_cc': PersonalizedFilters.hide_completed_courses
}

class TokenQueries(object):
    @classmethod
    def query_for_token(cls, token):
        return query_by_token_type[token.type](token)

    @classmethod
    def crn(cls, token):
        return CourseQuery(where_conditions=[('courses.crn = %s', str(token.normalized_value))])

    @classmethod
    def course_number(cls, token):
        return CourseQuery(where_conditions=[('left(courses.number, %s) = %s', len(token.normalized_value), token.normalized_value)])

    @classmethod
    def subject(cls, token):
        return CourseQuery(where_conditions=[('courses.subject = %s', token.normalized_value)])

    @classmethod
    def term_year(cls, token):
        return CourseQuery(where_conditions=[('courses.term_year = %s', token.normalized_value)])

    @classmethod
    def term_month(cls, token):
        return CourseQuery(where_conditions=[('courses.term_month = %s', token.normalized_value)])

    @classmethod
    def unit(cls, token):
        return CourseQuery(where_conditions=[('courses.units_low = %s', token.normalized_value)])

    @classmethod
    def ge_area(cls, token):
      return CourseQuery(where_conditions=[('%s = ANY(courses.ge_areas)', token.normalized_value)])

query_by_token_type = {
    'crn': TokenQueries.crn,
    'course_number': TokenQueries.course_number,
    'subject_code': TokenQueries.subject,
    'term_year': TokenQueries.term_year,
    'term_month': TokenQueries.term_month,
    'unit': TokenQueries.unit,
    'ge_area': TokenQueries.ge_area
}