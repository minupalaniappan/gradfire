from datetime import datetime
from davislib import Registrar, ScheduleBuilder, Sisweb, Term
from daviscoursesearch.flaskapp.utils.db_utils import conn
import daviscoursesearch.common.constants as const
import eventlet
import sys
import psycopg2
import logging
eventlet.monkey_patch(socket=True)

logger = logging.getLogger(__name__)
log_handler = logging.StreamHandler(sys.stderr)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)
logger.addHandler(log_handler)
logger.setLevel(logging.DEBUG)

cur = conn.cursor()

def get_instructor_id(instructor_name, instructor_email):
    if not instructor_name:
        return None

    cur.execute("""INSERT INTO instructors (name, email, name_components)
        SELECT %(name)s, %(email)s, regexp_split_to_array(lower(%(name)s), E'\\\s+')
        WHERE
        NOT EXISTS (
            SELECT name FROM instructors WHERE name = %(name)s
        ) RETURNING id; """, {'name': instructor_name, 'email': instructor_email})

    inserted_instructor_row = cur.fetchone()
    if not inserted_instructor_row:
        # instructor already exists in table
        cur.execute("SELECT id FROM instructors WHERE name = %s", (instructor_name,))
        return cur.fetchone()[0]

    return inserted_instructor_row[0]

def insert_meetings_for_course(course_id, meetings):
    cur.execute("DELETE FROM meetings WHERE course_id = %s", (course_id,))

    for meeting in meetings:
        meeting_values = dict()

        meeting_values['course_id'] = course_id
        meeting_values['type'] = meeting['type']
        meeting_values['location'] = meeting['location']
        meeting_values['start_time'] = meeting_values['end_time'] = None
        try:
            meeting_values['start_time'], meeting_values['end_time'] = meeting['times']
        except TypeError:
            # times TBA
            pass
        try:
            meeting_day_chars = set(meeting['days'])
            valid_day_chars = set(const.MEETING_DAYS_BY_CHAR.keys())

            if meeting_day_chars - valid_day_chars:
                raise ValueError("""Invalid day character found
                    in daystring {}""".format(meeting['days']))
            else:
                for c in meeting_day_chars & valid_day_chars:
                    name = const.MEETING_DAYS_BY_CHAR[c]
                    meeting_values[name] = True
                for c in valid_day_chars - meeting_day_chars:
                    name = const.MEETING_DAYS_BY_CHAR[c]
                    meeting_values[name] = False
        except ValueError:
            for day_name in const.MEETING_DAYS_BY_CHAR.values():
                meeting_values[day_name] = None

        cur.execute("""INSERT INTO meetings
            (course_id,
            type,
            start_time,
            end_time,
            location,
            monday,
            tuesday,
            wednesday,
            thursday,
            friday,
            saturday
            ) VALUES
            (%(course_id)s,
            %(type)s,
            %(start_time)s,
            %(end_time)s,
            %(location)s,
            %(monday)s,
            %(tuesday)s,
            %(wednesday)s,
            %(thursday)s,
            %(friday)s,
            %(saturday)s);""", meeting_values)

def _course_fields_from_obj(course):
    course_fields = {
        'term_year': course.term.year ,
        'term_month': course.term.session.value,
        'crn': course.crn,
        'subject': course.subject_code,
        'max_enrollment': course.max_enrollment,
        'number': course.number,
        'title': course.title,
        'available_seats' : course.available_seats,
        'description': course.description,
        'section': course.section ,
        'drop_time': course.drop_time,
        'prerequisites': course.prerequisites,
        'ge_areas': course.ge_areas,
        'waitlist_length': course.wl_length,
        'updated': datetime.now(),
        'registrar_removed': False,
        'from_transcript': False
    }

    if isinstance(course.units, tuple):
        course_fields['units_low'], course_fields['units_hi'] = course.units
    else:
        course_fields['units_low'] = course_fields['units_hi'] = course.units

    course_fields['instructor_id'] = get_instructor_id(course.instructor, course.instructor_email)

    return course_fields

def insert_course_row(course_fields):
    cur.execute("""INSERT INTO courses
        (term_year,
        term_month,
        crn,
        units_low,
        units_hi,
        subject,
        max_enrollment,
        number,
        title,
        available_seats,
        instructor_id,
        description,
        section,
        drop_time,
        prerequisites,
        ge_areas,
        waitlist_length,
        updated,
        title_desc_tsv)
        VALUES (%(term_year)s,
        %(term_month)s,
        %(crn)s,
        %(units_low)s,
        %(units_hi)s,
        %(subject)s,
        %(max_enrollment)s,
        %(number)s,
        %(title)s,
        %(available_seats)s,
        %(instructor_id)s,
        %(description)s,
        %(section)s,
        %(drop_time)s,
        %(prerequisites)s,
        %(ge_areas)s,
        %(waitlist_length)s,
        %(updated)s,
        setweight(to_tsvector(coalesce(%(title)s,'')), 'A') || setweight(to_tsvector(coalesce(%(description)s,'')), 'B'))
        RETURNING id""", course_fields)

def update_existing_course(course_fields):
    fields_to_update = {k: v for k, v in course_fields.items() if v != None}
    fields_set_directives = ','.join(["{0} = %({0})s".format(field) for field in fields_to_update.keys()])

    query = """
        UPDATE courses SET
            {0}
        WHERE term_year = %(term_year)s AND term_month = %(term_month)s AND crn = %(crn)s
        RETURNING id
        """.format(fields_set_directives)

    cur.execute(query, fields_to_update)

def insert_course(course):
    course_fields = _course_fields_from_obj(course)

    try:
        insert_course_row(course_fields)
    except psycopg2.IntegrityError:
        # Duplicate key
        conn.rollback()
        update_existing_course(course_fields)
    except psycopg2.ProgrammingError as e:
        conn.commit()
        raise e

    row = cur.fetchone()
    course_id = row[0]
    if course.meetings:
        insert_meetings_for_course(course_id, course.meetings)
    conn.commit()

def _existing_crns_for_term(term, start_subject=''):
    cur.execute("""SELECT crn FROM courses
        WHERE registrar_removed = false AND term_year = %s AND term_month = %s AND subject >= %s""",
        (int(term.year), int(term.session.value), start_subject))

    return set([row[0] for row in cur.fetchall()])

def _flag_removed_courses(term, removed_crns):
    for crn in removed_crns:
        cur.execute("""UPDATE courses SET registrar_removed = true
            WHERE crn = %s AND term_year = %s AND term_month = %s""",
            (crn, int(term.year), int(term.session.value)))

def _update_max_enrollment_for_crns(term, crns):
    """
    This method queries the registrar for max enrollment
    on all 'new_crns' and updates the courses table accordingly

    ScheduleBuilder provides all course information except max enrollment, which
    is exclusive to the Registrar and Sisweb data sources.
    """
    r = Registrar()
    for crn in crns:
        course = None
        while not course:
            with eventlet.Timeout(const.QUERY_TIMEOUT, False):
                print('fetching max enrollment for crn {}'.format(crn))
                course = r.course_detail(term, crn)
                if course.max_enrollment:
                    cur.execute("""UPDATE courses SET max_enrollment = %s
                        WHERE term_year = %s AND term_month = %s AND crn = %s""",
                        (course.max_enrollment, int(term.year), int(term.session.value), crn))

def scrape_courses_sb(term, username, password, start_subject=None):
    sb = ScheduleBuilder(username, password)
    existing_crns = _existing_crns_for_term(term, start_subject=start_subject)
    scraped_crns = set()

    for subject in const.SUBJECTS:
        if start_subject and subject < start_subject:
            continue

        courses = None
        while courses == None:
            with eventlet.Timeout(const.QUERY_TIMEOUT, False):
                logger.info('querying sb for subject {}'.format(subject))
                courses = sb.course_query(term, subject=subject)

                for course in courses:
                    logger.info('inserting course {}'.format(course))
                    insert_course(course)
                    scraped_crns.add(course.crn)
            if courses == None:
                logger.warn('timeout')

    new_crns = scraped_crns - existing_crns
    removed_crns = existing_crns - scraped_crns

    _flag_removed_courses(term, removed_crns)
    _update_max_enrollment_for_crns(term, new_crns)

def _scrape_registrar_detail(term, start_subject=None):
    r = Registrar()
    for subject in const.SUBJECTS:
        if start_subject and subject < start_subject:
            continue

        crns = None
        while crns == None:
            with eventlet.Timeout(const.QUERY_TIMEOUT, False):
                logger.info('listing crns for subject {}'.format(subject))
                try:
                    crns = r.course_query(term, subject=subject)
                except Exception as e:
                    logger.exception('exception on r.course_query for term: {}'.format(term))
                    continue

            if crns == None:
                logger.warn('timeout listing crns for {}'.format(crns))

        for crn in crns:
            course_detail = None
            logline = 'term: {}, crn: {}'.format(term, crn)

            while course_detail == None:
                with eventlet.Timeout(const.QUERY_TIMEOUT, False):
                    try:
                        course_detail = r.course_detail(term, crn)
                    except Exception as e:
                        logger.exception('exception on r.course_detail: {}'.format(course_detail))
                        continue

                if course_detail == None:
                    logger.warn('timeout querying course detail {}'.format(logline))

            logger.info(logline)
            try:
                insert_course(course_detail)
            except Exception as e:
                conn.rollback()
                logger.exception('exception inserting course {}'.format(course_detail))

def _scrape_sisweb_detail(term, username, password, start_subject=None):
    sw = Sisweb(username, password)
    for subject in const.SUBJECTS:
        logger.info('Scraping subject {}'.format(subject))
        courses = sw.course_query(term, subject)
        for course in courses:
            insert_course(course)

def scrape_course_detail(term, start_subject=None, username=None, password=None):
    year = int(term.year)
    month = int(term.session.value)
    if year < 2008:
        _scrape_sisweb_detail(term, username, password)
    else:
        _scrape_registrar_detail(term)

def main():
    try:
        start_subject = sys.argv[1]
    except IndexError:
        start_subject = None

    scrape_course_detail(Term(2015, 'fall'), start_subject)

if __name__ == "__main__":
    main()