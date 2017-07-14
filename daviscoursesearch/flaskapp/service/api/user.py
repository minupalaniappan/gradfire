from ...utils.db_utils import conn
from ...utils.course_utils import course_query, add_average_grade_to_course_query, add_enrollment_aggregates
from ...utils import student_utils as student
from ... import utils
from ...utils import SchemaEncoder, redis_lru
from ...models.models import CourseQuery, FilterConditions
from ....common import constants
from itertools import chain
import random
import json
import psycopg2
VALID_UPDATE_FIELDS = ['transcript_needs_update']
def update(user_id, fields):
    """
    Updates fields in 'students' table for provided user

    Parameters:
        user_id: int, user id.
        fields: MultiDict of user fields to update.
                Keys must exist in VALID_UPDATE_FIELDS (security precaution)
    Raises:
        ValueError if any key in fields parameter does not exist
        in VALID_UPDATE_FIELDS
    """

    # Ensure provided fields are valid
    bad_key = next((key for key in fields.keys() if key not in VALID_UPDATE_FIELDS),
        None)
    if bad_key:
        raise ValueError('Invalid field {}'.format(bad_key))

    cur = conn.cursor()

    field_keys, values = zip(*fields.items())
    values = tuple(map(lambda values: values[0], values))
    # fields is a MultiDict where values are lists
    # here we expect fields to have 1 associated value
    # so the 0th element is used.

    all_fields = values + (user_id,)
    field_expressions = ','.join(['{} = %s'.format(key) for key in field_keys])

    cur.execute("UPDATE students SET {} WHERE id = %s".format(field_expressions),
        all_fields)

    return json.dumps(student.user_meta_by_id(user_id), cls=SchemaEncoder)

COURSES_PER_PAGE = 100
@redis_lru()
def _major_courses_for_user(user_id):
    user_meta = student.user_meta_by_id(user_id)
    if 'programs' not in user_meta:
        return []
    major_ids = [program['id'] for program in user_meta['programs']]
    query = CourseQuery(joins=(('JOIN', """ majors_required_courses mrc
               ON mrc.program_id = ANY(%s)
               AND courses.subject = mrc.subject
               AND courses.number = mrc.number""", major_ids),),
                        where_conditions=[("""NOT EXISTS (SELECT 1 FROM students_completed_courses scc
                            JOIN courses c2 ON
                                c2.id = scc.course_id
                                AND c2.subject = courses.subject
                                AND c2.number = courses.number
                            WHERE scc.student_id = %s)""", user_id)])
    query = query.merge(FilterConditions.term_at_least(constants.CURRENT_TERM))
    query = query.merge(FilterConditions.lower_and_upper())
    add_average_grade_to_course_query(query)
    courses = course_query(*query.sql_and_values())
    for course in courses:
        course['relevancy'] = 'major'

    return courses

@redis_lru()
def _ge_courses(*args):
    query = CourseQuery(where_conditions=[('array_length(courses.ge_areas, 1) > 0',), ('avg_grade_order <= 5',)],)
    query = query.merge(FilterConditions.term_at_least(constants.CURRENT_TERM))
    query = query.merge(FilterConditions.lower_and_upper())
    add_average_grade_to_course_query(query)
    courses = course_query(*query.sql_and_values())
    for course in courses:
        course['relevancy'] = 'ge'

    return courses

@redis_lru()
def _no_prereq_courses(*args):
    query = CourseQuery(where_conditions=[('coalesce(array_length(courses.ge_areas, 1), 0) = 0',)])
    query = query.merge(FilterConditions.term_at_least(constants.CURRENT_TERM))
    query = query.merge(FilterConditions.lower_and_upper())
    courses = course_query(*query.sql_and_values())
    add_average_grade_to_course_query(query)
    for course in courses:
        course['relevancy'] = 'no_prereq'

    return courses
def _reservoir_sample(courses, n):
    sample = []
    # TY Knuth
    for idx, course in enumerate(courses):
        if idx < n:
            sample.append(course)
        elif idx >= n and random.random() < n/float(idx+1):
            replace = random.randint(0,len(sample) - 1)
            sample[replace] = course

    return sample

DISCOVER_FUNC_BY_TYPE = {
    'major': _major_courses_for_user,
    'ge': _ge_courses,
    'random': _no_prereq_courses
}

def discover_courses(user_id, discover_type, page=1):
    """
    Returns samples of courses:
        - relevant to user's major(s)
        - containing GE fulfillments
        - with no prerequisites

    Notes
        Drilldown: Explore and Exploit
        Exploit:
            ge fulfillments
            major
        Explore:
            irrelvant classes

        small class y/n define a threshold


    """
    if page > 1:
        return [] # Until infinite load
    discover_func = DISCOVER_FUNC_BY_TYPE[discover_type]

    discoveries = discover_func(user_id)
    return _reservoir_sample(discoveries, COURSES_PER_PAGE)
    # start_idx = ((page-1) * COURSES_PER_PAGE)
    # end_idx = page*COURSES_PER_PAGE

    # return discoveries[start_idx:end_idx]

def survey(user_id):
    q = """
    select subject, number, title, term_year, term_month, sum(max_enrollment)
    from students_completed_courses
    join courses on courses.id = students_completed_courses.course_id
    WHERE
    students_completed_courses.student_id = %s
    AND NOT EXISTS
        (SELECT 1 FROM course_advice a
            WHERE a.subject = courses.subject
            and a.number = courses.number
            and a.user_id = %s)
        AND subject != 'PHE'
        AND NOT substring(number FROM '^[0-9]+')::integer <@ int4range(190,200)
        AND NOT substring(number FROM '^[0-9]+')::integer <@ int4range(90,100)
    group by subject, number, title, term_year, term_month
    ORDER BY term_year desc, term_month desc
    limit 5;
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(q, (user_id, user_id))

    survey_candidates = [{'type': 'advice',
             'subject': r['subject'],
             'number': r['number'],
             'title': r['title'],
             'course_url': utils.course.url_for_section(r),
             'prompt': "What advice do you have for {} {} students?".format(r['subject'], r['number'])}
        for r in cur.fetchall()]
    if survey_candidates:
        candidate = _reservoir_sample(survey_candidates, 1)[0]
        candidate['reader_count'] = utils.course.max_annual_enrollment(candidate['subject'],
            candidate['number'])
        if candidate['reader_count']:
            candidate['reader_count'] = candidate['reader_count'] * 4

        return candidate
    else:
        return None
