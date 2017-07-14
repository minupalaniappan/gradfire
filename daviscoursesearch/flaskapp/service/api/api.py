from ...utils import discussion_utils, search_utils, student_utils, course_utils
from ... import utils
from ....common import tokenizer, constants
from flask import url_for, session
from itertools import product, chain
import json

SUCCESS = json.dumps({"success": 1})
def saveQuestion(user_id, question_id):
    discussion_utils.saveQuestion(user_id, question_id)
    return SUCCESS

def unsaveQuestion(user_id, question_id):
    discussion_utils.unsaveQuestion(user_id, question_id)
    return SUCCESS

def addAdvice(user_id, subject, number, title, advice):
    advice = utils.advice.addAdvice(user_id, subject, number, title, advice)
    return json.dumps(advice, cls=utils.SchemaEncoder)

ADVICE_PER_PAGE=10
def advice_saved_by_user(user_id):
    pass

def adviceForCourse(user_id, subject, number, page=1):
    advice = utils.advice.advice_for_courses(user_id, [{'subject': subject, 'number': number}],
        limit=QUESTIONS_PER_PAGE, offset=(page - 1) * ADVICE_PER_PAGE)

    return json.dumps(advice,
        cls=utils.SchemaEncoder)

def adviceGivenByUser(user_id, page=1):
    advice = utils.advice.advice_given_by_user(user_id, limit=QUESTIONS_PER_PAGE, offset=(page - 1) * ADVICE_PER_PAGE)
    return json.dumps(advice, cls=utils.SchemaEncoder)

def adviceForSavedCourses(user_id, page=1):
    saved_courses = student_utils.added_courses_for_student(user_id)
    advice = utils.advice.advice_for_courses(user_id, saved_courses,
        limit=QUESTIONS_PER_PAGE, offset=(page - 1) * ADVICE_PER_PAGE)
    return json.dumps(advice, cls=utils.SchemaEncoder)
"""
subject code
subjects
course number

to impl:
subject name
instructor
ge area
"""
def courseSuggestionsFromSubjectsAndTokens(subjects, tokens):
    courseNumbers = [token.normalized_value.lstrip('0') for token in tokens if token.type == 'course_number']
    courseCombs = product([s['code'] for s in subjects], courseNumbers)
    courseCombs = map(lambda course: course_utils.coursesStartingWithNumber(course[0], course[1]), courseCombs)
    courseCombs = chain.from_iterable(courseCombs)
    courses = [' '.join([subject, number.lstrip('0')]) for subject, number in courseCombs]
    return [{'type': 'course', 'name': course, 'key': course.replace(' ', '_'), 'url': url_for('search', q=course)} for course in courses]

def subjectsFromQuery(query, tokens):
    subject_codes_from_tokens = [token.normalized_value for token in tokens if token.type == 'subject_code']
    subjects_from_tokens = map(lambda code: {'code': code, 'name': constants.SUBJECT_NAMES_BY_CODE[code]}, subject_codes_from_tokens)

    subject_codes_from_kw, names_headlined, _ = search_utils.subject_candidates_for_keywords(query.split())
    subjects_from_kw = list(map(lambda subject: {'code': subject[0], 'name': subject[1]},
        zip(subject_codes_from_kw, names_headlined)))
    subjects = chain(subjects_from_tokens, subjects_from_kw)
    uniqueSubjects = utils.unique_everseen(subjects, key=lambda subject: subject['code'])

    return list(uniqueSubjects)

def suggestionsForSubjects(subjects):
    return [{'type': 'subject',
             'name': subject['name'],
             'key': subject['code'],
             'url': url_for('search', q=subject['code'])}
            for subject in subjects]

SUGGESTION_COUNT = 5
def autocompleteCourse(query):
    """
    Returns list of autocomplete suggestions
    Each suggestion is a dictionary with keys:
        type: One of ['subject', 'course', 'instructor']
        name: Pretty representation
        key: Key for react component / ID
        url: Link to content
    """
    tokens = tokenizer.tokenize(query)
    subjects = subjectsFromQuery(query, tokens)
    subjectSuggestions = suggestionsForSubjects(subjects)
    courseSuggestions = courseSuggestionsFromSubjectsAndTokens(subjects, tokens)

    topSuggestions = (courseSuggestions + subjectSuggestions)[:SUGGESTION_COUNT]
    return json.dumps(topSuggestions)

QUESTIONS_PER_PAGE = 10
def questionsForCourse(subject, number, user_id, page=1):
    return json.dumps(discussion_utils.questions_and_answers_for_courses([{'subject': subject, 'number': number}], user_id,
        limit=QUESTIONS_PER_PAGE, offset=(page - 1) * QUESTIONS_PER_PAGE), cls=utils.utils.SchemaEncoder)

def recentQuestionsForUser(user_id, sort='recent', page=1):
    """
    page start at 1
    """
    # Should this include tentative courses too?
    completed_courses = student_utils.completed_courses_and_urls(user_id, transfer_courses=False)

    questions = discussion_utils.questions_and_answers_for_courses(completed_courses, user_id,
        sort=sort, limit=QUESTIONS_PER_PAGE, offset=(page - 1) * QUESTIONS_PER_PAGE)
    unansweredQuestions = [question for question in questions if not question['userAnswered'] and not question['is_owner']]
    return json.dumps(unansweredQuestions, cls=utils.utils.SchemaEncoder)

questionSortsByType = {
    'recent': lambda q: q['timestamp'],
    'votes': lambda q: q['votes'],
    'answers': lambda q: len(q['answers'])
}

DEFAULT_QUESTION_SORT = 'recent'
def relevantAnswersForUser(user_id, sort='recent', page=1):
    if page > 1:
        return json.dumps([])
    questionsAskedByUser = discussion_utils.questionsAskedByUser(session.get('user_id'))
    print(questionsAskedByUser)
    savedQuestions = discussion_utils.saved_questions_for_user(session.get('user_id'))

    for q in questionsAskedByUser:
        q['source'] = 'asked'
    for q in savedQuestions:
        q['source'] = 'saved'

    allQuestions = sorted(questionsAskedByUser + savedQuestions,
        key=questionSortsByType.get(sort, questionSortsByType[DEFAULT_QUESTION_SORT]))

    return json.dumps(allQuestions, cls=utils.utils.SchemaEncoder)
