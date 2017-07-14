from werkzeug.routing import BuildError
from ..common import config
from flask import Flask, abort, render_template, request, redirect, session, url_for, make_response
app = Flask(__name__)
app.debug = (config.env == 'dev')
app.config.from_object(__name__)
app.config.from_envvar('DAVISCOURSESEARCH_SETTINGS', silent=True)
app.secret_key = config.secret_key

sentry = None
if config.env == 'production':
    from raven.contrib.flask import Sentry
    sentry = Sentry(app, dsn=config.sentry_dsn)

def log_exception_to_sentry():
    if sentry:
        sentry.captureException()

from collections import OrderedDict
from datetime import datetime
from functools import wraps
from .utils.course_utils import get_course_detail, course_metadata_for_term, subjectsWithPrequisitesForTerm
from .utils.instructor_utils import courses_taught_by_term, instructor_name_for_id, most_taught_subject, teaching_since
from .utils.student_utils import reset_password, verify_reset_code, send_reset_email, InvalidPasswordError, update_user, student_major_completion, resend_verification_email, set_user_is_verified, verification_code_for_user, add_user_google, verify_login, user_meta_by_id, handle_transcript, user_id_by_email, user_meta_by_id, user_is_admin, add_course_for_student, del_course_for_student, added_courses_for_student, update_session_token, verify_session, SignupError, get_all_users, InvalidTranscriptError, impacted_areas_for_course, ge_completion_by_area, major_completion_by_major_id, completed_courses_and_urls, user_progress_is_current, remove_session_token, ical_from_added_courses
from .utils.discussion_utils import questions_and_answers_for_course, store_answer, store_question, add_vote, DuplicateSubmissionError, LimitOneError, UnverifiedUserError, deleteQuestion, deleteAnswer, questions_from_completed_courses
from .utils.search_utils import courses_and_sections_for_search, instructors_for_query
from .utils.major_utils import majors_by_id, add_major, update_major, remove_major, get_major_req_json, store_major_reqs, get_major_detail
from .utils.prereq_utils import store_prereq_json
from .utils import utils, discussion_utils, student_utils, course_utils
from ..common import constants as const
from ..common.logging import exception_logger, slack_log_exception, log_js_exception
from itertools import chain
from . import service
import copy
import json
import urllib.parse
import math
import time
from . import service
import re

# Profiler
# if app.debug:
#     from werkzeug.contrib.profiler import ProfilerMiddleware
#     app.config['PROFILE'] = True
#     app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30], sort_by=['cumtime'])

@app.errorhandler(Exception)
def handle_exception(error):
    if sentry:
        sentry.captureException()

    exception_summary = {
        'time': datetime.now().isoformat(),
        'url': request.url,
        'user_id': session.get('user_id')
    }
    if config.db_name == 'dcs_dev':
        slack_log_exception(exception_summary)
    exception_logger.exception(json.dumps(exception_summary))
    return render_template('errors/500.html'), 500

@app.before_request
def ensure_verified_session():
    if request.cookies.get('token') and request.cookies.get('user_id'):
        session['token'] = request.cookies['token']
        session['user_id'] = request.cookies['user_id']

    if not verify_session(session.get('user_id'), session.get('token')):
        session.clear()

def auth_required(func=None, onboard_redirect=True):
    def decorator(f):
        @wraps(f)
        def verify_auth(*args, **kwargs):
            if not verify_session(session.get('user_id'), session.get('token')) or (
                request.path.startswith('/admin') and not user_is_admin(session.get('user_id'))):
                session.clear()
                return redirect(url_for('home', ref=func.__name__))
            if onboard_redirect:
                if not student_utils.get_user_role(session.get('user_id')):
                    return redirect(url_for('onboard'))

            return f(*args, **kwargs)
        return verify_auth
    if func:
        return decorator(func)
    return decorator

@app.context_processor
def template_utility_processor():
    def url_modify_keys(_raw=False, **kv_pairs):
        args = request.args.to_dict()
        for key, value in kv_pairs.items():
            args[key] = value
        if _raw:
            return request.base_url + '?' + '&'.join(['='.join((k, v)) for k, v in args.items()])
        else:
            return request.base_url + '?' + urllib.parse.urlencode(args)
    return dict(url_modify_keys=url_modify_keys)

url_modify_keys = template_utility_processor()['url_modify_keys']
def url_toggle_filter(filter_name, default=False):
    args = request.args.to_dict()
    if filter_name in args:
        del args[filter_name]
    else:
        if default:
            args[filter_name] = '0'
        else:
            args[filter_name] = '1'

    return request.base_url + '?' + urllib.parse.urlencode(args)

def template_context(user_meta=None, term_year=None, term_month=None):
    if term_year and term_month:
        session['term_year'], session['term_month'] = (term_year, int(term_month))
    elif 'term_year' in request.args and 'term_month' in request.args:
        session['term_year'], session['term_month'] = (request.args['term_year'], int(request.args['term_month']))
    elif not session.get('term_year'):
        session['term_year'], session['term_month'] = const.ACTIVE_TERM
    elif isinstance(session.get('term_month'), str): # Patch 1/30/16
        session['term_month'] = int(session.get('term_month'))
    user_id = session.get('user_id', None)

    added_courses = []
    notifications = []
    if user_id:
        added_courses = added_courses_for_student(user_id)
        notifications = service.notifications.notifications_for_user(user_id)
    if user_id and not user_meta:
        user_meta = user_meta_by_id(user_id)

    try:
        user_meta['json'] = json.dumps(user_meta)
    except TypeError:
        pass

    notifications = service.notifications.notifications_for_user(user_id)
    return {
            'active_terms': utils.term_range(const.CURRENT_TERM, const.MAX_TERM),
            'saved_questions': discussion_utils.saved_questions_for_user(user_id),
            'added_courses': added_courses,
            'user_meta': user_meta,
            'catalog': service.index.subjects_and_top_classes(),
            'sessions': const.TERM_SESSION_BY_MONTH,
            'pretty_sessions': const.PRETTY_SESSION_BY_MONTH,
            'is_admin': user_is_admin(session.get('user_id')),
            'url_toggle_filter': url_toggle_filter,
            'cache_buster': config.last_commit_hash,
            'term_session': const.PRETTY_SESSION_BY_MONTH[session['term_month']],
            'current_term': const.CURRENT_TERM,
            'active_term': const.ACTIVE_TERM,
            'env': config.env,
            'notifications': notifications,
            'has_unread_notifications': any(not notif['read'] for notif in notifications)
        }

@app.route("/")
def home(signup_errors=None):
    context = template_context()
    if context['user_meta']:
        return redirect(url_for('profile'))

    context['majors'] = majors_by_id()
    ref = request.args.get('ref')
    try:
        return render_template('pages/index.html',
            ref_url=url_for(ref) if ref else None,
            signup_errors=signup_errors, **context)
    except BuildError:
        return render_template('pages/index.html',
            ref_url=None,
            signup_errors=signup_errors, **context)

@app.route("/admin/api/major_reqs_by_id")
@auth_required
def api_major_reqs_by_id():
    return get_major_req_json(request.args.get('major_id'))

@app.route("/admin/api/store_major_reqs", methods=['POST'])
@auth_required
def api_store_major_reqs():
    store_major_reqs(request.form['major_id'], request.form['major_req_json'])
    return 'success'

@app.route("/admin/")
@auth_required
def admin_home():
    return render_template('admin/index.html', **template_context())

@app.route('/admin/email')
@auth_required
def admin_email():
    return render_template('admin/email.html', **template_context())

@app.route('/admin/users')
@auth_required
def admin_users():
    users = get_all_users()
    return render_template('admin/users.html', users=users, **template_context())

@app.route('/admin/user/<id>')
@auth_required
def admin_user_detail():
    return render_template('admin/user_detail.html')

@app.route("/admin/add_major", methods=['GET', 'POST'])
@auth_required
def admin_add_major():
    if user_is_admin(session.get('user_id')):
        if request.method == 'POST':
            if request.form.get('major_name'):
                if request.form.get('major_id_to_update'):
                    update_major(request.form['major_id_to_update'],
                        request.form['major_name'],
                        request.form['major_variant'])
                else:
                    add_major(request.form['major_name'],
                    request.form['major_variant'])
            else:
                # Remove
                remove_major(request.form['major_id_to_remove'])
        return render_template('admin/add_major.html',
            **template_context(), majors_by_id=majors_by_id())

@app.route('/admin/api/store_prerequisites', methods=['POST'])
@auth_required
def store_prerequisites():
    normalized_req_json = store_prereq_json(request.form['subject'], request.form['number'],
        request.form['term_year'], request.form['term_month'], request.form['req_json'])
    return normalized_req_json

@app.route('/admin/prerequisites/<term_year>/<term_session>/')
@auth_required
def prereq_listing(term_year, term_session):
    term_month = const.TERM_MONTH_BY_SESSION[term_session]
    return render_template('admin/prereq_choose_subject.html',
        subjects=subjectsWithPrequisitesForTerm(term_year, term_month), **template_context())

@app.route('/admin/prerequisites/<term_year>/<term_session>/<subject>', methods=['GET', 'POST'])
@auth_required
def admin_prerequisites(term_year, term_session, subject):
    term_month = const.TERM_MONTH_BY_SESSION[term_session]
    return render_template('admin/prereq_edit.html',
        courses=course_metadata_for_term(term_year, term_month, subject),
        subjects=const.SUBJECTS,
        **template_context())

@app.route("/admin/update_major_reqs")
@auth_required
def admin_major_reqs():
    if user_is_admin(session.get('user_id')):
        return render_template('admin/major_reqs.html',
            **template_context(), majors_by_id=majors_by_id(),
            subjects=const.SUBJECTS)
    else:
        abort(404)

def clear_session():
    session.clear()

    response = make_response(redirect(url_for('home')))
    response.set_cookie('token', value='', expires=0)

@app.route('/major/<major_id>')
def major(major_id=None):
    major = get_major_detail(major_id)
    return render_template('pages/major.html', major=major, **template_context())

@app.route('/logout')
def logout():
    remove_session_token(session['user_id'], session['token'])
    session.clear()

    response = make_response(redirect(url_for('home')))
    response.set_cookie('token', value='', expires=0)
    return response

def establish_user_session(user_id, response, remember_me=False):
    session.clear()
    session['user_id'] = user_id
    session['token'] = update_session_token(session['user_id'])
    if remember_me:
        response.set_cookie('token',
            value=session['token'],
            max_age=config.remember_me_expiration.total_seconds(),
            expires=datetime.now() + config.remember_me_expiration,
            secure=True)
        response.set_cookie('user_id',
            value=str(session['user_id']),
            max_age=config.remember_me_expiration.total_seconds(),
            expires=datetime.now() + config.remember_me_expiration,
            secure=True)
    else:
        response.set_cookie('token',
            value='',
            max_age=0,
            expires=0)
        response.set_cookie('user_id',
            value='',
            max_age=0,
            expires=0)
    return response

@app.route('/settings', methods=['GET'])
@auth_required
def preferences_form():
    return render_template('pages/user_settings.html', **template_context(), majors=majors_by_id())

@app.route('/settings', methods=['POST'])
@auth_required
def handle_preferences(errors=[]):
    context = template_context()
    transcript = request.form['transcript']
    programs = request.form.getlist('programs')
    try:
        service.user.update_student(session['user_id'], transcript, programs)
    except InvalidTranscriptError:
        log_exception_to_sentry()
        errors.append("""Invalid transcript.
            Please make sure the contents of your entire OASIS transcript
            is copied into the text box.""")

    form_stripped = {k: v.strip() for k, v in request.form.items() if v.strip()}
    try:
        update_user(session['user_id'],
            name=form_stripped.get('name'),
            current_password=form_stripped.get('current_password'),
            new_password=form_stripped.get('new_password'))
    except InvalidPasswordError:
        errors.append('Incorrect current password.')

    return render_template('pages/user_settings.html',
        **template_context(),
        majors=majors_by_id(),
        errors=errors)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password_form():
    user_id = request.args.get('id')
    reset_code = request.args.get('c')
    if not verify_reset_code(user_id, reset_code):
        return redirect(url_for('home'))

    if request.method == 'POST':
        return handle_reset_password(user_id)
    else:
        return render_template('pages/reset_password.html', **template_context())

def handle_reset_password(user_id):
    password = request.form.get('password')
    password_confirm = request.form.get('password_confirm')

    try:
        reset_password(user_id, password, password_confirm)
    except InvalidPasswordError as e:
        return render_template('pages/reset_password.html', error=e, **template_context())

    return redirect(url_for('home'))

@app.route('/send_password_reset', methods=['GET'])
def send_password_reset_form():
    return render_template('pages/send_password_reset.html', **template_context())

@app.route('/send_password_reset', methods=['POST'])
def handle_send_password_reset():
    user_email = request.form.get('email').strip()
    send_reset_email(user_email)

    return render_template('pages/send_password_reset.html', sent=True, **template_context())

@app.route('/signup', methods=['GET'])
def signup_form(**kwargs):
    return redirect(url_for('home'))

@app.route('/signup', methods=['POST'])
def handle_signup():
    form_stripped = {k: v.strip() for k, v in request.form.items() if v.strip()}
    major_ids = [int(v) for k, v in form_stripped.items() if k.startswith('major_')]
    try:
        user_id = add_user(form_stripped.get('email', ''), form_stripped.get('password', ''),
            form_stripped.get('name', ''), form_stripped.get('userRole'), major_ids)
    except SignupError as e:
        return home(signup_errors=[str(e)])
    if form_stripped.get('userRole') == 'student':
        resp = make_response(redirect(url_for('transcript_upload')))
    else:
        resp = make_response(redirect(url_for('profile')))
    return establish_user_session(user_id, resp)

@app.route('/verify_email', methods=['GET'])
def verify_email():
    user_id = request.args.get('user_id')
    stored_code = verification_code_for_user(user_id)
    if stored_code == request.args.get('code'):
        set_user_is_verified(user_id)
        return redirect(url_for('home', verified=1))
    else:
        return redirect(url_for('home', verified=0))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'user_id' not in session:
            return render_template('login.html', **template_context())
        else:
            if request.args.get('verified'):
                return redirect(url_for('profile', verified=1))
            else:
                return redirect(url_for('profile'))
    else:
        email = request.form['email']
        password = request.form['password']
        if verify_login(email, password):
            response = make_response(redirect(url_for('profile')))
            return establish_user_session(user_id_by_email(email), response,
                remember_me=request.form['remember_me'])
        else:
             return render_template('login.html', errors=['Incorrect email or password'], **template_context())

@app.route("/search")
def search():
    if not request.args.get('q'):
        return redirect(url_for('home'))
    request_args = request.args.to_dict()
    request_args['q'] = request_args['q'].lower()

    user_meta = user_meta_by_id(session.get('user_id'))
    instructors = []
    if not any(kw in [subject.lower() for subject in const.SUBJECTS] for kw in request_args['q'].split()):
        instructors = instructors_for_query(request_args.get('q'))
        if len(instructors) == 1 and instructors[0][2]:
            return redirect(url_for('instructor', instructor_id=instructors[0][0]))
        for idx, instructor_detail in enumerate(instructors):
            instr_id, name, is_exact_match = instructor_detail
            instructors[idx] = (instr_id, name, url_for('instructor', instructor_id=instr_id))
    fall_back = True
    if request.args.get('term_year'):
        fall_back = False # Don't automatically produce alternate results if a specific term
                          # is queried.
    courses  = courses_and_sections_for_search(request_args, user_meta, instructors, fall_back=fall_back)
    all_sections = list(chain(*[course['sections'] for course in courses]))
    instructors = [(instr_id, name, any(section['instructor_id'] == instr_id for section in all_sections), url) for instr_id, name, url in instructors]
    instructors =  sorted(instructors, key=lambda instr: instr[2], reverse=True)
    term_year, term_month = (int(request.args.get('term_year', 0)), int(request.args.get('term_month', 0)))

    if courses:
        term_year = courses[0]['term_year']
        term_month = courses[0]['term_month']

    if len(courses) == 1 and (not instructors or all(instr[2] == False for instr in instructors)) and list(request.args.keys()) == ['q']:
        return redirect(courses[0]['url'])

    context = template_context(term_year=term_year, term_month=term_month)
    context['term_year'] = term_year
    context['term_month'] = term_month

    if term_year and term_month:
        if (term_year, term_month) < const.MAX_TERM:
            next_term_year, next_term_month = utils.next_term(term_year, term_month)
            context['next_session'] = const.PRETTY_SESSION_BY_MONTH[next_term_month]
            context['next_term_link'] = url_modify_keys(term_year=next_term_year, term_month=next_term_month)
        if (term_year, term_month) != const.LOWEST_TERM:
            prev_term_year, prev_term_month = utils.previous_term(term_year, term_month)
            context['prev_session'] = const.PRETTY_SESSION_BY_MONTH[prev_term_month]
            context['prev_term_link'] = url_modify_keys(term_year=prev_term_year, term_month=prev_term_month)

    courses_ge_areas = set(list(chain(*[course['ge_areas'] for course in courses])))

    return render_template('pages/results.html',
        request_args=request_args,
        instructors=instructors,
        courses=courses,
        ge_codes_by_area={v: k for k, v in const.GE_AREAS_BY_OASIS_ABBRV.items()
            if v in courses_ge_areas},
        courses_ge_areas=courses_ge_areas,
        **context)

@app.route('/course/<subject>/<number>')
def course(subject, number):
    term_year, term_month = course_utils.latest_term_course_offered(subject, number)
    return course_response(term_year, term_month, subject, number, None)

def course_response(term_year, term_month, subject, number, title):
    context = template_context(term_year=term_year, term_month=term_month)
    context['current_term'] = const.CURRENT_TERM # Course page hides the section details for old terms (data integrity issues)
    course_detail = get_course_detail(term_year,
        term_month,
        subject.upper(),
        number.upper(),
        title=title,
        user_id=session.get('user_id'))

    if not course_detail:
        return abort(404)

    if context['user_meta']:
        course_detail['impacted_areas'] = impacted_areas_for_course(context['user_meta']['id'], course_detail)
        context['student_completion'] = ge_completion_by_area(session['user_id'])
        context['student_completion']['json'] = json.dumps(context['student_completion'])

    course_detail['json'] = utils.stringify_obj_for_json(copy.deepcopy(course_detail))
    course_detail['json'] = json.dumps(course_detail['json'], cls=utils.SchemaEncoder)

    show_grade_distrib = True
    grade_views = 1
    if not context['user_meta']:
        course_detail.pop('grades')
    try:
        resp = make_response(render_template('pages/course.html',
            course=course_detail,
            grade_views=grade_views,
            max_grade_views=const.MAX_GRADE_VIEWS,
            show_grade_distrib=show_grade_distrib,
            **context))
        if not context['user_meta']:
            resp.set_cookie('grade_views', str(grade_views + 1))

        return resp
    except StopIteration:
        # TODO return 404
        pass

@app.route('/course/<int:term_year>/<term_session>/<subject>/<number>', defaults={'title': None})
@app.route('/course/<int:term_year>/<term_session>/<subject>/<number>/<title>')
def course_term(term_year=None, term_session=None, subject=None, number=None, title=None):
    term_month=None
    try:
        term_month = const.TERM_MONTH_BY_SESSION[term_session]
    except KeyError:
        return redirect('/search?q={}+{}'.format(subject, number))
    return course_response(term_year, term_month, subject, number, title)


@app.route('/course/<subject>/<number>/question/<int:question_id>')
def question_thread(subject=None, number=None, question_id=None):
    context = template_context()
    try:
        user_id = context.get('user_meta').get('id')
    except AttributeError:
        user_id = None
    context['related_questions'] = service.question.related_questions(subject, number, user_id)
    context['question'] = service.question.question_thread_for_question(subject, number, question_id, user_id)
    return render_template('pages/question.html', **context)


@app.route('/course/<subject>/<number>/question/<int:question_id>/answer/<int:answer_id>')
def answer(subject=None, number=None, question_id=None, answer_id=None):
    context = template_context()
    try:
        user_id = context.get('user_meta').get('id')
    except AttributeError:
        user_id = None
    context['question'] = service.question.question_thread_for_question(subject, number, question_id, user_id)
    context['answerId'] = answer_id

    return render_template('pages/answer.html', **context)

@app.route('/ads/course/<int:term_year>/<term_session>/<subject>/<number>', defaults={'title': None})
@app.route('/ads/course/<int:term_year>/<term_session>/<subject>/<number>/<title>')
def course_ad(term_year=None, term_session=None, subject=None, number=None, title=None):
    term_month=None
    try:
        term_month = const.TERM_MONTH_BY_SESSION[term_session]
    except KeyError:
        return redirect('/search?q={}+{}'.format(subject, number))

    context = template_context(term_year=term_year, term_month=term_month)
    course_detail = get_course_detail(term_year, term_month, subject.upper(), number.upper(), title=title)
    if not course_detail:
        return abort(404)

    course_detail['json'] = json.dumps(utils.stringify_obj_for_json(course_detail)).replace("'", "\\'").replace('\\"', '\\\\"')
    try:
        return render_template('ads/course_ad.html',
            course=course_detail,
            **context)
    except StopIteration:
        # TODO return 404
        pass

@app.route('/instructor/<int:instructor_id>')
def instructor(instructor_id=None):
    courses = courses_taught_by_term(instructor_id)
    instructor_name = instructor_name_for_id(instructor_id)
    earliest_term = list(teaching_since(instructor_id))
    earliest_term[1] = const.TERM_SESSION_BY_MONTH[earliest_term[1]] # 1 maps to 'Winter', etc

    instructor = {
        'name': instructor_name,
        'main_subject': most_taught_subject(instructor_id),
        'earliest_year': earliest_term[0],
        'earliest_session': earliest_term[1]
    }
    return render_template('pages/instructor.html', instructor=instructor,
        courses_by_term=courses,
        term_session_by_month=const.PRETTY_SESSION_BY_MONTH,
        lowest_term=const.LOWEST_TERM,
        **template_context())

@app.route('/api/user/<int:user_id>', methods=['POST'])
@auth_required
def userUpdate(user_id):
    """
    Updates field for specific user. Only accessible if authenticated for user_id

    supported fields:


    """
    if session.get('user_id') != user_id: # Security!
        return abort(403)

    try:
        return service.api.user.update(user_id, dict(request.form))
    except ValueError as e:
        # Invalid field provided in request.form. Bad request!
        return abort(400)

@app.route('/api/web/login', methods=['POST'])
def google_login():
    email = request.form['email']
    id_token = request.form['id_token']

    token_info = service.auth.get_token_info(id_token)
    if service.auth.is_google_token_valid(token_info):
        user_id = user_id_by_email(email)
        resp = make_response(json.dumps({'success': 1}))
        if not user_id:
            user_id = student_utils.add_user_google(token_info)
        return establish_user_session(user_id, resp, remember_me=True)


@app.route('/api/autocomplete')
def apiAutocomplete():
    query = request.args.get('q')

    return service.api.autocompleteCourse(query)

# @app.route('/api/instructor/autocomplete')
@app.route('/api/programs')
def apiPrograms():
    return json.dumps(service.api.programs.getPrograms(), cls=utils.SchemaEncoder)

@app.route('/api/course/<subject>/<number>/grades')
@auth_required
def apiCourseGrades(subject, number):
    return json.dumps(service.api.course.get_grades(subject, number), cls=utils.SchemaEncoder)

@app.route('/api/course/<subject>/<number>/questions')
def apiCourseQuestions(subject, number):
    return service.api.questionsForCourse(subject, number, session.get('user_id'), page=int(request.args.get('page', 1)))

@app.route('/api/course/<subject>/<number>/advice')
def api_course_advice(subject, number):
    return service.api.adviceForCourse(session.get('user_id'), subject, number, page=int(request.args.get('page', 1)))

@app.route('/api/course/<subject>/<number>/note', methods=['GET'])
def api_course_note(subject, number):
    return service.api.course.get_note(subject, number)

@app.route('/api/course/<subject>/<number>/note', methods=['POST'])
@auth_required
def api_course_note_update(subject, number):
    note_json = request.form['note_json']
    note_plain = request.form['note_plain']

    return service.api.course.update_note(
        session.get('user_id'),
        subject,
        number,
        note_json,
        note_plain)

@app.route('/api/question/<question_id>', methods=['DELETE'])
@auth_required
def apiDelQuestion(question_id):
    deleteQuestion(session['user_id'], question_id)
    return '1'

@app.route('/api/answer/<answer_id>', methods=['DELETE'])
@auth_required
def apiDelAnswer(answer_id):
    deleteAnswer(session['user_id'], answer_id)
    return '1'


@app.route('/api/save_question', methods=['POST'])
@auth_required
def apiSaveQuestion():
    return service.api.saveQuestion(session.get('user_id'), request.form['question_id'])

@app.route('/api/unsave_question', methods=['POST'])
@auth_required
def apiUnsaveQuestion():
    return service.api.unsaveQuestion(session.get('user_id'), request.form['question_id'])

@app.route('/api/add_question', methods=['POST'])
@auth_required
def add_question():
    user_meta = user_meta_by_id(session.get('user_id'))
    try:
        question = store_question(request.form['subject'], request.form['number'],
            request.form['term_year'], request.form['term_month'],
            request.form['question'], user_meta['id'])

        return json.dumps(question)
    except DuplicateSubmissionError:
        return json.dumps({'error': 'dupe'})
    except UnverifiedUserError:
        return json.dumps({'error': 'unverified'})

@app.route('/api/add_answer', methods=['POST'])
@auth_required
def add_answer():
    user_meta = user_meta_by_id(session.get('user_id'))
    try:
        return json.dumps(store_answer(request.form['question_id'], user_meta['id'], request.form['answer']))
    except LimitOneError:
        return json.dumps({'error': 'limit_1'})
    except UnverifiedUserError:
        return json.dumps({'error': 'unverified'})

@app.route('/api/add_course', methods=['POST'])
@auth_required
def add_course():
    user_id = session['user_id']
    subject = request.form['subject']
    number = request.form['number']
    title = request.form['title']
    term_year = request.form['term_year']
    term_month = request.form['term_month']
    add_course_for_student(user_id, subject, number, title, term_year, term_month)

    return '1'

@app.route('/api/add_advice', methods=['POST'])
@auth_required
def addAdvice():
    user_id = session['user_id']

    return service.api.addAdvice(session['user_id'],
            request.form['subject'],
            request.form['number'],
            request.form['title'],
            request.form['advice'])

@app.route('/api/upvote', methods=['POST'])
@auth_required
def qa_vote():
    item_id = request.form['item_id']
    add_vote(session.get('user_id'), item_id, request.form['type'])
    return '1'

@app.route('/api/del_course', methods=['POST'])
@auth_required
def del_course():
    user_id = session['user_id']
    subject = request.form['subject']
    number = request.form['number']
    title = request.form['title']
    term_year = request.form['term_year']
    term_month = request.form['term_month']
    del_course_for_student(user_id, subject, number, title, term_year, term_month)

    return '1'

@app.route('/api/log_error', methods=['POST'])
def log_error():
    err_message = request.form['message']
    url = request.form['url']
    linecol = request.form['linecol']
    log_js_exception(err_message, url, linecol, session.get('user_id'))
    return '1'

@app.route('/api/advice/<advice_id>', methods=['DELETE'])
@auth_required
def delete_advice(advice_id):
    if service.api.advice.advice_is_owned_by_user(session['user_id'], advice_id):
        service.api.advice.delete_advice(session['user_id'], advice_id)
        return service.api.SUCCESS
    else:
        return abort(403)

@app.route('/api/schedule_ics/<int:term_year>/<int:term_month>')
@auth_required
def ical_for_student(term_year, term_month):
    body = ical_from_added_courses(session.get('user_id'), term_year, term_month)
    resp =  make_response(body)
    filename = '{}{}Calendar.ics'.format(const.PRETTY_SESSION_BY_MONTH[term_month], term_year)
    resp.headers['Content-Disposition'] = "attachment; filename={}".format(filename)
    return resp

@app.route('/api/user/discover/courses/<list_type>')
@auth_required
def user_discover_courses(list_type):
    page = int(request.args.get('page', 1))
    courses = service.api.user.discover_courses(
        session['user_id'],
        list_type,
        page=page)
    return json.dumps(courses,
        cls=utils.SchemaEncoder)

@app.route('/api/user/relevant_answers')
@auth_required
def user_relevant_answers():
    return service.api.relevantAnswersForUser(session.get('user_id'),
        page=int(request.args.get('page', 1)),
        sort=request.args.get('sort', 'recent'))

@app.route('/api/user/notifications')
@auth_required
def user_notifications():
    page = int(request.args.get('page', 1))
    notifications = service.notifications.notifications_for_user(session['user_id'], page=page)
    return json.dumps(notifications, cls=utils.SchemaEncoder)

@app.route('/api/instructor/<int:instructor_id>/courses')
def instructor_taught_courses(instructor_id):
    return json.dumps(service.api.instructor.courses_taught(instructor_id),
        cls=utils.SchemaEncoder)

@app.route('/api/instructor/disambiguate')
def instructor_disambiguate():
    """
    When an instructor signs up with their UCD email, we need to map
    their user ID to an instructor ID.
    """
    pass
@app.route('/api/user/courses/saved')
@auth_required
def user_saved_courses():
    page = int(request.args.get('page', 1))
    if page > 1:
        return json.dumps([])
    saved_courses = added_courses_for_student(session.get('user_id'))
    with_questions = bool(request.args.get('with_questions', False))
    if with_questions:
        questions = discussion_utils.questions_and_answers_for_courses(saved_courses, session.get('user_id'))
        for course in saved_courses:
            course['questions'] = next(filter(
                lambda q: q['subject'] == course['subject'] and q['number'] == course['number'],
                questions))

    return json.dumps(saved_courses, cls=utils.SchemaEncoder)

@app.route('/api/user/survey')
@auth_required
def user_survey():
    return json.dumps(service.api.user.survey(session['user_id']), cls=utils.SchemaEncoder)

@app.route('/api/user/courses/saved/advice')
@auth_required
def user_saved_courses_advice():
    return service.api.adviceForSavedCourses(session.get('user_id'))

@app.route('/api/user/courses/completed')
@auth_required
def user_completed_courses():
    completed_courses = completed_courses_and_urls(session.get('user_id'))
    return json.dumps(completed_courses, cls=utils.SchemaEncoder)

@app.route('/api/user/courses/<subject>/<number>')
@auth_required
def fetch_relation_to_specific_course(subject, number):
    completed_courses = completed_courses_and_urls(session.get('user_id'))
    course = list(filter(lambda course: course['subject'] == subject and course['number'] == number, completed_courses))[0]
    course['placeholder'] = determineAttributesForRelation(course['letter_grade'], course['upper_division'], course['subject'], course['number'], course['instructor'])
    return (json.dumps(course))

def determineAttributesForRelation (grade, division, subject, number, instructor):
    letter = grade[re.search('[a-zA-Z]', grade).start()]
    course_instructor = '?'
    result = {
      'A': lambda div: ('How did lower divs help you do really well in ' + course_instructor) if div else ('What allowed you to do well in this class ' + course_instructor),
      'B': lambda div: ('What could you have done to push yourself to an A ' + course_instructor) if div else ('Do you have any advice for underclassmen interested in taking ' + course_instructor),
      'C': lambda div: ('What prerequisite classes helped in doing well in ' + course_instructor) if div else ('How was  ' + course_instructor),
      'D': lambda div: ('Which lower division classes would you take to do better ' + course_instructor) if div else ('How could you have improved while taking ' + course_instructor),
      'F': 'Were there any major differences between an upper division{course_instructor}',
      'P': 'What did you take away from {course_instructor}',
      'Y': 'What prevented you from completing {course_instructor}'
    }[letter](division)

    return (result);

@app.route('/api/user/saved_questions')
@auth_required
def user_saved_questions():
    return json.dumps(discussion_utils.saved_questions_for_user(session.get('user_id')),
        cls=utils.SchemaEncoder)

@app.route('/api/user/unanswered_questions')
@auth_required
def user_unanswered_questions():
    return service.api.recentQuestionsForUser(session.get('user_id'),
        page=int(request.args.get('page', 1)),
        sort=request.args.get('sort', 'recent'))

@app.route('/api/user/questions')
@auth_required
def user_questions():
    return json.dumps(discussion_utils.questionsAskedByUser(session.get('user_id')),
        cls=utils.SchemaEncoder)

@app.route('/api/user/answers')
@auth_required
def user_answers():
    return json.dumps(discussion_utils.answersGivenByUser(session.get('user_id')),
        cls=utils.SchemaEncoder)

@app.route('/api/user/advice')
@auth_required
def user_advice():
    return service.api.adviceGivenByUser(session['user_id'])

@app.route('/api/user/saved_advice')
@auth_required
def user_saved_advice():
    return service.api.advice_saved_by_user(session['user_id'])

@app.route('/onboard')
@auth_required(onboard_redirect=False)
def onboard():
    if service.onboard.is_user_onboarded(session['user_id']):
        return redirect('profile')

    return render_template('pages/onboard.html', **template_context())

@app.route('/onboard', methods=['POST'])
@auth_required(onboard_redirect=False)
def onboard_process():
    if request.form.get('transcript'):
        # Student
        transcript = request.form['transcript']
        if not ('programs' in request.form):
            return redirect('/onboard?role=student&error=no_program')

        programs = request.form['programs']
        try:
            service.onboard.process_student_onboard(session['user_id'], transcript, programs)
        except InvalidTranscriptError:
            return redirect('/onboard?role=student&error=invalid_transcript')
    elif request.form.get('instructor_id'):
        # Instructor
        service.onboard.process_instructor_onboard(session['user_id'], request.form['instructor_id'])
    elif request.form.get('subjects'):
        # Campus affiliated (general)
        serivce.onboard.process_general_onboard(session['user_id'], request.form['subjects'])

    return redirect('profile')

@app.route('/transcript_upload', methods=['GET', 'POST'])
@auth_required
def transcript_upload():
    if request.method == 'GET':
        return render_template('pages/transcript_upload.html', **template_context())
    else:
        transcript = request.form['transcript']
        user_id = session['user_id']
        try:
            handle_transcript(user_id, transcript)
        except InvalidTranscriptError:
            error = 'Error: no courses found in transcript.'
            return render_template('pages/transcript_upload.html', errors=[error], **template_context())
            # TODO log me + transcript text
        return redirect(url_for('profile', ))

@app.route("/profile")
@auth_required
def profile():
    context = template_context()
    if request.args.get('resend_verification'):
        resend_verification_email(session['user_id'])
        return redirect(url_for('profile', resent_verification=1))

    if context['user_meta']['role'] == 'student':
        completed_courses = completed_courses_and_urls(session['user_id'])
        return render_template('pages/student_profile.html', **context)
    elif context['user_meta']['role'] == 'instructor':
        return render_template('pages/teacher_profile.html', **context, **service.uni_profile.context(context))
    elif context['user_meta']['role'] == 'affiliate':
        return render_template('pages/affiliate_profile.html', **context)

def paginate_link(page):
    query = urllib.parse.urlparse(request.url).query
    if query:
        args = dict(urllib.parse.parse_qsl(query))
        args['page'] = page
        return request.base_url + '?' + urllib.parse.urlencode(args)
    else:
        return request.url + '?page={}'.format(page)

@app.route('/sitemap')
def sitemap():
    term_range = list(utils.term_range(const.LOWEST_TERM, const.MAX_TERM))
    term_range.reverse()

    return render_template('common/sitemap.html',
        terms=term_range,
        term_sessions_by_month=const.PRETTY_SESSION_BY_MONTH,
        **template_context())

@app.route('/subjects/<int:term_year>/<term_session>')
def subjects_for_term(term_year, term_session):
    return render_template('common/subjects_for_term.html',
        subjects=const.SUBJECT_CODES_BY_NAME,
        subject_term_year=term_year,
        subject_term_session=term_session,
        **template_context())

@app.route('/blog/uc-davis-textbook-market')
def ucd_textbook_market():
    return render_template('blog/ucd_textbook_market.html', **template_context())

@app.route('/notifications')
@auth_required
def notifications():
    return render_template('pages/notifications.html', **template_context())

@app.route('/about')
def about():
    return render_template('pages/about.html', **template_context())

@app.route('/unsubscribe',methods=['GET', 'POST'])
def unsubscribe():
    if request.method == 'GET':
        return render_template('pages/unsubscribe.html')
    else:
        service.unsubscribe.unsub(request.form['email'])
        return render_template('pages/unsubscribe.html', success=1)

