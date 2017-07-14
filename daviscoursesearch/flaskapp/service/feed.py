from ..utils.discussion_utils import questions_and_answers_for_courses,answers_for_courses
from ..utils import student_utils, utils
from ...common.constants import CURRENT_TERM
from itertools import chain
import json

def answersRelevantToUserSchedule(user_id, added_courses):
    # answers to questions user has scheduled
    tentative_courses = list(chain(*[courses for term, courses in added_courses.items() if term > CURRENT_TERM]))
    return answers_for_courses(tentative_courses, user_id)

def context(user_id, added_courses):
    return {'recentQuestions': recentQuestionsForUser(user_id),
            'answersRelevantToSchedule': answersRelevantToUserSchedule(user_id, added_courses['sections'])}
