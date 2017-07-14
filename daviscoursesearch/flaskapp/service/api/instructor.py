from ...utils.course_utils import CourseQuery, course_query

def courses_taught(instructor_id):
    query = CourseQuery(where_conditions=[('instructor_id = %s', instructor_id)],
        order_by=['term_year DESC, term_month DESC'])

    return course_query(*query.sql_and_values())