import * as common from 'common';
import "../../../../../node_modules/whatwg-fetch/fetch";
import {objectToQueryString} from 'utils';

const Endpoints = {
    advice: (advice_id) => `/api/advice/${advice_id}`,
    question: (question_id) => `/api/question/${question_id}`,
    answer: (answer_id) => `/api/answer/${answer_id}`,
    addAdvice: '/api/add_advice',
    adviceForCourse: (subject, number) => `/api/course/${subject}/${number}/advice`,
    adviceForSavedCourses: '/api/user/courses/saved/advice',
    adviceGivenByUser: '/api/user/advice',
    notificationsForUser: '/api/user/notifications',
    surveyForUser: '/api/user/survey',
    userLogin: '/api/web/login',
    discoverCourses: (discoveryType) => `/api/user/discover/courses/${discoveryType}`,
    instructorNote: (subject, number) => `/api/course/${subject}/${number}/note`,
    programsForUniversity: '/api/programs',
    grades: (subject, number) => `/api/course/${subject}/${number}/grades`,
    relationToCourse: (subject, number) => `/api/user/courses/${subject}/${number}`
}

const fetchWithParams = function(baseUrl, params, callback) {
    fetch(baseUrl + '?' + objectToQueryString(params), {credentials: 'same-origin'})
        .then(
            (resp) => resp.json().then(
                (json) => {
                    callback(json)
                }
            )
        )
}
function formDataFromObj(data) {
    let formData = new FormData();
    for(key in data) {
        formData.append(key, data[key])
    }

    return formData;
}
const postWithData = function(baseUrl, data, callback) {
    let formData = formDataFromObj(data)

    fetch(baseUrl, {method: 'POST', body: formData, credentials: 'same-origin'})
        .then(
            (resp) => resp.json().then(
                (json) => callback(json)
            )
        )
}

const deleteWithData = function(baseUrl, data, callback) {
    let formData = formDataFromObj(data)

    fetch(baseUrl, {method: 'DELETE', body: formData, credentials: 'same-origin'})
        .then(
            (resp) => resp.json().then(
                (json) =>
                    {
                        if(callback){
                            callback(json)
                        }
                    }
            )
         );
}

class ApiQuestions {
    unansweredByUser(page=1, sort='recent', params={}, callback) {
        var args = {
            page: page,
            sort: sort
        }
        fetchWithParams(common.API.userUnansweredQuestions, args, callback)
    }

    askedByUser(callback) {
        /*

        */
        fetchWithParams(common.API.userQuestions, {}, callback)
    }

    answeredByUser(callback) {
        fetchWithParams(common.API.userAnswers, {}, callback)
    }

    savedQuestions(callback) {
        fetchWithParams(common.API.userSavedQuestions, {}, callback)
    }

    forCourse(page=1, sort='recent', params={}, callback) {
        let url = common.API.courseQuestions(params['subject'], params['number'])
        fetchWithParams(url, {page: page, sort: sort}, callback)
    }

    relevantAnswers(page=1, sort='recent', params={}, callback) {
        var args = {
            page: page,
            sort: sort
        }
        fetchWithParams(common.API.userRelevantAnswers, args, callback)
    }

    delete(q_id, callback) {
        deleteWithData(Endpoints.question(q_id), {}, callback)
    }

    deleteAnswer(answer_id, callback) {
        deleteWithData(Endpoints.answer(answer_id), {}, callback)
    }
}

const DEFAULT_COURSE_SORT = 'term'
const _zipQuestions = function(callback, courses) {
    const questionsUnzipped = courses.map((course) => course['questions'])
    const questionsZipped = [].concat(...questionsUnzipped)
    callback(questionsZipped)
}

class ApiCourses {
    savedCourses(page=1, callback) {
        fetchWithParams(common.API.userSavedCourses, {sort: DEFAULT_COURSE_SORT}, callback);
    }


    savedCoursesWithQuestions(sort=DEFAULT_COURSE_SORT, callback) {
        fetchWithParams(common.API.userSavedCourses, {with_questions: 1, page: page, sort: sort},
            _zipQuestions.bind(null, callback));
    }


    completedCourses(page=1, callback) {
        fetchWithParams(common.API.userCompletedCourses, {sort: DEFAULT_COURSE_SORT}, callback)
    }

    instructorNote(subject, number, callback) {
        fetchWithParams(Endpoints.instructorNote(subject, number), {}, callback)
    }

    reviseInstructorNote(subject, number, note_json, note_plain, callback) {
        postWithData(Endpoints.instructorNote(subject, number),
            {note_json: note_json,
             note_plain: note_plain},
            callback)
    }

    fetchGrades(subject, number, callback) {
        fetchWithParams(Endpoints.grades(subject, number), {}, callback)
    }
}

const DEFAULT_ADVICE_SORT = 'time'
class ApiAdvice {
    constructor() {
        this.cache = {}
    }

    getCachedResponse(endpoint, params) {
        return this.cache[endpoint + '?' + objectToQueryString(params)]
    }

    cacheResponse(endpoint, params, callback, response) {
        this.cache[endpoint + '?' + objectToQueryString(params)] = response
        callback(response)
    }

    deleteAdvice(advice_id, callback) {
        deleteWithData(Endpoints.advice(advice_id), {}, callback)
    }

    addAdvice(advice, subject, number, title, callback) {
        let data = {
            advice: advice,
            subject: subject,
            number: number,
            title: title
        }
        postWithData(Endpoints.addAdvice, data, callback)
    }

    saved(sort='time', callback) {
        fetchWithParams(common.API.userSavedAdvice, {sort: sort}, callback)
    }

    givenByUser(sort='time', callback) {
        fetchWithParams(Endpoints.adviceGivenByUser, {sort: sort}, callback)
    }

    forSavedCourses(sort='time', page=1, callback) {
        fetchWithParams(Endpoints.adviceForSavedCourses, {sort: sort}, callback)
    }


    forCourse(subject, number, sort='time', page=1, callback) {
        const endpoint = Endpoints.adviceForCourse(subject, number)
        const params = {sort: sort, page: page}
        const cachedResp = this.getCachedResponse(endpoint, params)
        if(cachedResp) {

            callback(cachedResp);
            return
        } else {
            const cachedCallback = this.cacheResponse.bind(this, endpoint, params, callback);
            fetchWithParams(Endpoints.adviceForCourse(subject, number), {sort: sort, page: page},
                cachedCallback)
        }
    }


}


DISCOVERY_TYPES = ['major', 'ge', 'random']
class ApiUser {
    notifications(callback, page=1) {
        fetchWithParams(Endpoints.notificationsForUser, {page: page}, callback)
    }

    discoveriesForType(discoveryType, page=1, callback) {
        fetchWithParams(Endpoints.discoverCourses(discoveryType), {page: page}, callback)
    }

    login(email, id_token, callback) {
        const data = {
            email: email,
            id_token: id_token
        };
        postWithData(Endpoints.userLogin, data, callback);
    }

    fetchRelationToCourse(subject, number, callback) {
        fetchWithParams(Endpoints.relationToCourse(subject, number), {}, callback)
    }

    surveyPrompt(callback) {
        fetchWithParams(Endpoints.surveyForUser, {}, callback);
    }
}

class ApiPrograms {
    constructor() {
        this.cache = {}
    }
    cacheResponse(endpoint, callback, response) {
        this.cache[endpoint] = response;
        callback(response);
    }
    programsForUniversity(callback) {
        const endpoint = Endpoints.programsForUniversity
        if(endpoint in this.cache) {
            callback(this.cache[endpoint]);
            return;
        }

        const cachedCallback = this.cacheResponse.bind(this, endpoint, callback);
        fetchWithParams(endpoint, {}, cachedCallback);
    }
}

export const Questions = new ApiQuestions();
export const Courses = new ApiCourses();
export const Advice = new ApiAdvice();
export const User = new ApiUser();
export const Programs = new ApiPrograms();