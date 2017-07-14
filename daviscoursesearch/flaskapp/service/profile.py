from ..utils.student_utils import completed_courses_and_urls
from ..utils.discussion_utils import questions_and_answers_for_courses, discourseTeamUserId, questionsAskedByUser, answersGivenByUser
from itertools import groupby, chain
from ...common import constants as const
from ..utils.student_utils import ge_completion_by_area, major_completion_by_major_id, completed_courses_and_urls, user_progress_is_current
from ..utils.discussion_utils import questions_from_completed_courses
import json

def _coursesAnnotatedWithContext(courses, user_id):
    questionsForCourses = questions_and_answers_for_courses(courses, user_id)
    for course in courses:
        questions = [question for question in questionsForCourses
            if question['subject'] == course['subject']
            and question['number'] == course['number']]
        course['questionCount'] = len(questions)

        course['hasAnswered'] = any(q['userAnswered'] for q in questions)
        try:
            course['adviceQuestionId'] = next(q['id'] for q in questions
                if q['user_id'] == discourseTeamUserId())
        except StopIteration:
            if questions:
                course['adviceQuestionId'] = questions[0]['id']
            else:
                course['adviceQuestionId'] = None
    return courses

def _coursesGroupedByTerm(courses):
    keyfunc = lambda course: (course['term_year'], course['term_month'])
    courses = sorted(courses, key=keyfunc)
    groupedByTerm = [[term, list(courses)] for term, courses in groupby(courses, keyfunc)]

    return list(groupedByTerm)

def completedCoursesByTerm(user_id):
    completed_courses = completed_courses_and_urls(user_id, transfer_courses=False)
    courses = _coursesAnnotatedWithContext(completed_courses, user_id)

    return _coursesGroupedByTerm(courses)

def contributions(user_id):
    questions = questionsAskedByUser(user_id)
    answers = answersGivenByUser(user_id)
    for question in questions:
        question['type'] = 'question'
    for answer in answers:
        answer['type'] = 'answer'

    return sorted(questions + answers, key=lambda contrib: contrib['timestamp'], reverse=True)

