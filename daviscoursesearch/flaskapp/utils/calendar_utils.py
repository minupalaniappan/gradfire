from ...common import constants as const
from icalendar import Event, vRecur
from datetime import datetime, timedelta

NUMERIC_DAY_BY_LETTER = {
    'M': 0,
    'T': 1,
    'W': 2,
    'R': 3,
    'F': 4,
    'S': 5
}

RRULE_DAY_BY_LETTER = {
    'M': 'MO',
    'T': 'TU',
    'W': 'WE',
    'R': 'TH',
    'F': 'FR'
}

def date_candidates(start_date):
  date_candidate = start_date
  for x in range(7):
      yield date_candidate
      date_candidate += timedelta(days=1) # Next day

def find_first_meeting(quarter_start, meeting_days, meeting_start_td):
  """
  Returns a datetime instance representing the first meeting past the provided quarter_start

  Parameters:
      quarter_start: datetime representing start of the quarter in which the meeting occurs
      meeting_days: list of days of week on which the meeting occurs
          letter format: ('M', 'T', 'W', 'R', 'F', 'S')
      meeting_start_td: Timedelta representing the difference between the
          meeting's start time and the preceding midnight
  """
  # Find DOW
  numeric_meeting_days = [NUMERIC_DAY_BY_LETTER[day] for day in meeting_days]
  first_meeting_day = next(date for date in date_candidates(quarter_start) if date.weekday() in numeric_meeting_days)
  # first_meeting_day is a datetime w/ the time set at midnight before the first meeting
  # adding the meeting_start_td yields a datetime instance
  first_meeting = first_meeting_day + meeting_start_td

  return first_meeting_day + meeting_start_td

def add_course_to_calendar(cal, course):
    term_year, term_month = (course['term_year'], course['term_month'])
    quarter_start = const.INSTRUCTION_START_DATES_BY_TERM[(term_year, term_month)]
    quarter_end = const.INSTRUCTION_END_DATES_BY_TERM[(term_year, term_month)]
    for meeting in course['meetings']:
        event = Event()
        event.add('summary', ' '.join((course['subject'], course['number'], meeting['type'])))
        event.add('location', meeting['location'])
        meeting_start_td = timedelta(minutes=meeting['start_time_minutes'])
        first_meeting = find_first_meeting(quarter_start, meeting['days'], meeting_start_td)
        event.add('dtstart', first_meeting)

        meeting_duration_mins = meeting['end_time_minutes'] - meeting['start_time_minutes']
        event.add('duration', timedelta(minutes=meeting_duration_mins))

        recurrence_days = [RRULE_DAY_BY_LETTER[day] for day in meeting['days']]
        event.add('rrule', vRecur(freq='weekly', byday=recurrence_days, until=quarter_end))

        cal.add_component(event)
