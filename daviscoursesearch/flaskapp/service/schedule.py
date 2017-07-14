from ...common import constants as const
from ..utils import utils
from ..utils.course_utils import alternative_sections_for_course
from itertools import chain
from operator import itemgetter
import json
import random

def add_prev_term_to_context(context, term_year, term_month):
    prev_term_year, prev_term_month = utils.previous_term(term_year, term_month)
    context['prev_session'] = const.PRETTY_SESSION_BY_MONTH[prev_term_month]
    context['prev_session_short'] = const.TERM_SESSION_BY_MONTH[prev_term_month]

def add_next_term_to_context(context, term_year, term_month):
    next_term_year, next_term_month = utils.next_term(term_year, term_month)
    context['next_session'] = const.PRETTY_SESSION_BY_MONTH[next_term_month]
    context['next_session_short'] = const.TERM_SESSION_BY_MONTH[next_term_month]

# This method will format the response json that will render the schedule.
def filter_sections(sections_without_tuple_key):
    json_ret = []
    json_terms = []
    json_term = []
    for term in sections_without_tuple_key:
        # We will save the values of the quarter names in order
        # to use them for the drop down on the schedule page
        last2 = term[0][-1:]
        if(len(term[0]) == 6):
            last2 = term[0][-2:]
        term_str = const.PRETTY_SESSION_BY_MONTH[int(last2)] + ' ' + term[0][:4]
        json_terms.append({ 'key' : term[0], 'value' : term_str})
        # until here is just for the creation of the drop down (TODO: improve this code)
        days = {'M':[],'T':[],'W':[],'R':[],'F':[]}
        for course in term[1]:
            name = course['subject'] + ' ' + course['number'] + ' ' + \
                    course['section'] + ' - ' + course['title']
            for meets in course['meetings_sorted_time'] :
                session = meets['prettyType']
                classroom = meets['location']
                time = ('' if meets['start_time'] is None else meets['start_time'] ) + ' - ' + \
                       ('' if meets['end_time'] is None else meets['end_time'] )
                sortBy = meets['start_time_minutes']
                for day in meets['days']:
                    days[day].append({ 'courseName' : name ,
                                       'courseid' : course['id'],
                                       'sortBy' : sortBy,
                                       'session' : session,
                                       'classroom' : classroom,
                                       'time' : time,
                                       'id': course['crn'],
                                       'key': random.randint(1, 1000) })
        json_days = []
        json_days.append({ 'day' : "Monday", 'key': random.randint(1, 1000),
            'meetings' : sorted(days['M'], key=lambda k: int(k['sortBy']), reverse=False)})
        json_days.append({ 'day' : "Tuesday", 'key': random.randint(1, 1000),
            'meetings' : sorted(days['T'], key=lambda k: int(k['sortBy']), reverse=False)})
        json_days.append({ 'day' : "Wednesday", 'key': random.randint(1, 1000),
            'meetings' : sorted(days['W'], key=lambda k: int(k['sortBy']), reverse=False)})
        json_days.append({ 'day' : "Thursday", 'key': random.randint(1, 1000),
            'meetings' : sorted(days['R'], key=lambda k: int(k['sortBy']), reverse=False)})
        json_days.append({ 'day' : "Friday", 'key': random.randint(1, 1000),
            'meetings' : sorted(days['F'], key=lambda k: int(k['sortBy']), reverse=False)})
        json_term.append({ 'term' : term[0], 'days' : json_days })
    # Build the final return json with two main children.
    # terms: will contain the values that will be displayed in the drop down.
    # schedule: holds all the information for any given quarter.
    json_ret.append({'key': random.randint(1, 1000), 'terms' : json_terms, 'schedule' : json_term})
    return json.dumps(json_ret)

def getSchedule(context, term_year, term_session):
    term_month = const.TERM_MONTH_BY_SESSION[term_session]
    context['term_session'] = const.PRETTY_SESSION_BY_MONTH[term_month]
    if (term_year, term_month) < const.MAX_TERM:
        add_next_term_to_context(context, term_year, term_month)
    if (term_year, term_month) > const.CURRENT_TERM:
        add_prev_term_to_context(context, term_year, term_month)
    #for section in chain(*[sections for term, sections in context['added_courses']['sections'].items()]):
    #    alt_sections = alternative_sections_for_course(section)

    #    section['alt_sections'] = [utils.stringify_obj_for_json(alt_section)
    #        for alt_section in alt_sections]
    #    for meeting in section['meetings']:
    #        meeting['conflicts_by_day'] = {day: list() for day in const.SCHEDULE_DAYS} # for JS

    # can't json encode tuple term key; use term code
    sections_without_tuple_key = [('{}{}'.format(*term), sections) for term, sections in context['added_courses']['sections'].items()]
    sections_without_tuple_key = [(term, [(utils.stringify_obj_for_json(section)) for section in sections])
            for term, sections in sections_without_tuple_key]

    context['schedule_added_courses_json'] = filter_sections(sections_without_tuple_key).replace("'", "\\'")
    #print(context['schedule_added_courses_json'])
    context['period_minutes'] = 30
    context['schedule_days'] = const.SCHEDULE_DAYS
    return (term_year, term_month)
