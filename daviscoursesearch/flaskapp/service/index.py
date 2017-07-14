from ...common.constants import SUBJECTS_BY_KEYWORD
from ..utils.db_utils import conn
from ..utils import unique_everseen, redis_lru, departments, course_utils as course
from ...common.constants import CURRENT_TERM
import psycopg2

def _uniqify_numbers(result):
    result['numbers'] = list(unique_everseen(result['numbers']))

@redis_lru()
def subjects_and_top_classes():
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""SELECT courses.subject code,
        subjects.name subject_name,
        array_agg(number ORDER BY max_enrollment DESC NULLS LAST) numbers
        FROM courses
        JOIN subjects ON subjects.code = courses.subject AND subjects.is_undergraduate
        WHERE term_year >= %s AND term_month >= %s
        AND (substring(number, 0, 4)::integer <@ int4range(0, 89) or substring(number, 0, 4)::integer <@ int4range (100,189))
        GROUP BY courses.subject, subjects.name
        """, CURRENT_TERM)
    results = cur.fetchall()
    for res in results:
        _uniqify_numbers(res)

    return results
