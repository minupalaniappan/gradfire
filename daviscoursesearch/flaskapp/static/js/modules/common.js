'use strict';
import "../../../../../node_modules/babel-polyfill/dist/polyfill";
import * as update from 'update';
import Autocomplete from 'autocomplete';
import "../../../../../node_modules/whatwg-fetch/fetch";
import { Questions, User, Courses } from 'api';
import { Advice as AdviceController } from 'api';
import { GenericBlock } from 'block';
import * as cards from 'cards';



export function posCreate(top="0px", bottom="0px", left="0px", right="0px") {
  return (
    {position: "relative", top: top, bottom: bottom, left: left, right: right}
  );
  console.log("ji")
}

var sassVariables;

var GLOBAL_MOUNT_POINT_MAX = Math.pow(2, 53);

function lineBreaksFromNewlines(text) {
  if (text)
    return text.split("\n").map((item, index) => {
      return (index === 0) ? item : [<br/>, item]
    })
}

export function commoncallback (data) {
  return (data);
}

export function initGoogle() {
  window.gapi_auth2.signIn().then(function() {
    var googleUser = window.gapi_auth2.currentUser.get();
    window.GAuth.onSignIn(googleUser);
  });
}
export function adjustHeight(el){
    el.target.style.height = (el.scrollHeight > el.clientHeight) ? (el.scrollHeight)+"px" : "60px";
}

export function createReactRootIndex () {
    return Math.ceil(Math.random()  * GLOBAL_MOUNT_POINT_MAX);
  }

export function prettyDateAndTime() {
    var now = new Date();
    return [(now.getMonth() + 1), now.getDate(), now.getFullYear()].join('/');
  }

export var API = {
      addQuestion: '/api/add_question',
      addAnswer: '/api/add_answer',
      delQuestion: '/api/del_question',
      delAnswer: '/api/del_answer',
      saveQuestion: '/api/save_question',
      unsaveQuestion: '/api/unsave_question',
      upvote: '/api/upvote',
      autoComplete: '/api/autocomplete',
      userRelevantAnswers: '/api/user/relevant_answers',
      userUnansweredQuestions: '/api/user/unanswered_questions',
      userSavedQuestions: '/api/user/saved_questions',
      userSavedCourses: '/api/user/courses/saved',
      userSavedAdvice: '/api/user/advice/saved',
      userCompletedCourses: '/api/user/courses/completed',
      userQuestions: '/api/user/questions',
      userAnswers: '/api/user/answers',
      courseQuestions: (subject, number) => `/api/course/${subject}/${number}/questions`
    };
export function loadSassVariables() {
      if(sassVariables) {
        return;
      }
      var callback = function(resp) {
        sassVariables = JSON.parse(resp);
      };
      getWithCallback('/static/style/variables.json', callback.bind(this));
  };

export function getWithCallback(endpoint, callback) {
      var xhr = requestWithCallback(callback);
      xhr.open('GET', endpoint);
      xhr.send();
    };

export var GE_CATEGORY_ORDER = ['Topical Breadth', 'Core Literacies'];
export function termCodeFromArr(term) {
      return term[0] +  '' + term[1];
    }
export function formatDate(date) {
    var cts =  new Date(date);
    var month = ("0" + cts.getMonth()).slice(-2);
    var day = ("0" + cts.getDate()).slice(-2);
    return cts.getFullYear() + '-' + month + '-' + day +
              ' ' + cts.getHours() + ':' + cts.getMinutes();
  }
export function refreshWithNewParam(params) {
      var current_url = [location.protocol, '//', location.host, location.pathname].join('');
      var params_plus_preserved = $.param(params).replace(new RegExp('%2B', 'g'), '+');
      window.location = current_url + '?' + params_plus_preserved;
    }
export function searchUrlForText(text) {
      return [location.protocol, '//', location.host, '/search', '?q=', encodeURIComponent(text).replace('%20', '+')].join('');
    }
export var indefiniteArticleByLetter = {
      'A': 'an',
      'B': 'a',
      'C': 'a',
      'D': 'a',
      'F': 'an',
      'P': 'a',
      'N': 'a'
};

export function getUrlParameters() {
      var vars = {}, hash;
      var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
      for(var i = 0; i < hashes.length; i++)
      {
          hash = hashes[i].split('=');
          vars[hash[0]] = decodeURIComponent(hash[1]).replace('+', ' ');
      }
      return vars;
}

export function addCourse(callback) {
      endpoint = '/api/add_course';
      var form_data = new FormData();
      form_data.append('user_id', window.USER_META.id);
      form_data.append('subject', window.COURSE.subject);
      form_data.append('number', window.COURSE.number);
      form_data.append('title', window.COURSE.title);
      form_data.append('term_year', window.COURSE.term_year);
      form_data.append('term_month', window.COURSE.term_month);

      postFormData(endpoint, form_data, callback);
    }
export function delCourse(callback) {
      endpoint = '/api/del_course';
      var form_data = new FormData();
      form_data.append('user_id', window.USER_META.id);
      form_data.append('subject', window.COURSE['subject']);
      form_data.append('number', window.COURSE['number']);
      form_data.append('title', window.COURSE['title']);
      form_data.append('term_year', window.COURSE['term_year']);
      form_data.append('term_month', window.COURSE['term_month']);
      postFormData(endpoint, form_data, callback);
    }
export function addQuestion(question, callback) {
      var form_data = new FormData();
      form_data.append('subject', window.COURSE['subject']);
      form_data.append('number', window.COURSE['number']);
      form_data.append('term_year', window.COURSE['term_year']);
      form_data.append('term_month', window.COURSE['term_month']);
      form_data.append('question', question);
      postFormData(API.addQuestion, form_data, callback);
    }
export function addQuestionWithParams(question, subject, number, term_year, term_month, callback) {
      var form_data = new FormData();
      form_data.append('subject', subject);
      form_data.append('number', number);
      form_data.append('term_year', term_year);
      form_data.append('term_month', term_month);
      form_data.append('question', question);
      postFormData(API.addQuestion, form_data, callback);
    }
export function delQuestion(question_id) {
      var form_data = new FormData();
      form_data.append('question_id', question_id);
      postFormData(API.delQuestion, form_data);
    }
export function saveQuestion(question_id) {
      var form_data = new FormData();
      form_data.append('question_id', question_id);
      form_data.append('user_id', window.USER_META.id);
      postFormData(API.saveQuestion, form_data);
    }

export function unsaveQuestion(question_id) {
      var form_data = new FormData();
      form_data.append('question_id', question_id);
      form_data.append('user_id', window.USER_META.id);
      postFormData(API.unsaveQuestion, form_data);
}

export function addAnswer(answer, question_id, callback) {
      var form_data = new FormData();
      form_data.append('question_id', question_id);
      form_data.append('user_id', window.USER_META.id);
      form_data.append('answer', answer);
      postFormData(API.addAnswer, form_data, callback);
    }
export function delAnswer(answer_id) {
      var form_data = new FormData();
      form_data.append('answer_id', answer_id);
      postFormData(API.delAnswer, form_data);
    }
export function upvote(item_id, type) {
      var form_data = new FormData();
      form_data.append('item_id', item_id);
      form_data.append('type', type);
      postFormData(API.upvote, form_data);
}

export function autoCompleteQuery(query, callback) {
  fetch(API.autoComplete + '?q=' + query)
  .then(function(resp) {
    if(resp.ok) {
      resp.text().then(callback);
    }
    else {

    }
  });
}

export function fetchGrades(subject, number, callback) {
  Courses.fetchGrades(subject, number, (grades) => {
    var labels = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-'], spread = {};
    labels.forEach((letter, i) => {
      spread[letter] = 0;
      grades.map((values, j) => {
        var indexOfLetter = values['letters'].indexOf(letter);
        if (indexOfLetter > -1) {
          spread[letter] += values['counts'][indexOfLetter];
        } else {
          spread[letter] += 0;
        }
      })
    });
    callback(spread)
  });
}

export function requestWithCallback(callback) {
      var xhr = new XMLHttpRequest();
      xhr.onreadystatechange = function() {
        if (xhr.readyState == XMLHttpRequest.DONE) {
          if(xhr.status != 200) {
            console.log(xhr.response);
            return;
          }
          if(callback)
            callback(xhr.response);
        }
      };
      return xhr;
    }
export function postFormData(endpoint, form_data, callback) {
      var xhr = requestWithCallback(callback);
      xhr.open('POST', endpoint);
      xhr.send(form_data);
    }

export var SaveCourse = React.createClass({
  getInitialState: function () {
    return({
      mode: this.props.initialMode
    });
  },
  addCourse: function () {
    this.setState({
      mode: true
    }, addCourse());
  },
  deleteCourse: function () {
    this.setState({
      mode: false
    }, delCourse());
  },
  render: function () {
    var currentMode;
    if (!window.USER_META)
      currentMode = (<button className = "load" onClick={initGoogle}>Follow</button>)
    else {
      if (!this.state.mode)
      currentMode = (<button className = "load" onClick={this.addCourse}>Follow</button>);
      else
        currentMode = (<button className = "loadAlternate" style = {{border: '2px solid #769aff'}} onClick={this.deleteCourse}><i aria-hidden="true"></i>Unfollow</button>);
    }
    return (<div>{currentMode}</div>);
  }
});

export var AutocompleteSearch = React.createClass({
  getInitialState: function () {
    return ({
      query: this.props.query,
      results: [],
      loading: false,
    });
  },
  render: function () {
    var queryInputContainer  = (
        <div className="foundation-form" id="query_input_container">
          <Autocomplete
            inputProps={{name: "q", id: "query_input_large", className: "", placeholder: "Search classes and professors"}}
            ref="autocomplete"
            value={this.state.query}
            resize={this.state.resize}
            items={this.state.results}
            getItemValue={(item) => item.name}
            onSelect={(value, item) => {
              document.getElementById('searchform').submit();
              this.setState({ value, results: [ item ] })
            }}
            onChange={(event, value) => {
              this.setState({ query: event.target.value })
              this.setState({ value, loading: true })
              autoCompleteQuery(value, (items) => {
                this.setState({ results: JSON.parse(items), loading: false })
              })
            }}
            renderItem={(item, isHighlighted, index) => (
              <div style={{display: "block", backgroundColor: (!index || !(index%2)) ? "#FAFAFA" : "white",
                                                 borderTop: (!index || !(index%2)) ? "1px solid #EBEBEB" : "none",
                                                 borderBottom: (!index || !(index%2)) ? "1px solid #EBEBEB" : "none"}} className="padding-1">
                <div
                  key={item.key}
                  id={item.key}
                  className="autocomplete-item padding-1 column-12 wrapper-12"
                  style={{display: "block"}}
                  >
                    <a href={item.url}>
                      <div>
                        <span dangerouslySetInnerHTML={{__html: item.name}}></span>
                        <span> - {item.type}</span>
                      </div>
                    </a>
                  </div>
              </div>
            )}
          />
          <i className="fa fa-search right width-1 middle top"></i>
        </div>);

    return (
      <div>
        {queryInputContainer}
      </div>);
  }
});

export var Votes = React.createClass({
  propTypes: {
    userVoted: React.PropTypes.bool.isRequired,
    votes: React.PropTypes.number.isRequired,
    voteFunc: React.PropTypes.func.isRequired
  },
  render: function() {
    vote = (<div className={"column-12"}>
      <div onClick={this.props.voteFunc} className={"inline middle"}>
        <i className={(this.props.userVoted) ? "fa fa-heart fa-1x voted" : "fa fa-heart fa-1x unvoted"}></i>
      </div>
      <p className="metric inline top margin-side-2">{this.props.votes} VOTES</p>
      </div>);

    return (vote);
  }
})

export var Question = React.createClass ({
  getInitialState: function () {
    return ({
      isDeleted: false,
      votes: this.props.votes,
      userAnswered: this.props.userAnswered,
      userVoted: this.props.user_voted,
      responseBoxIsShown: true,
      answerdata: this.props.answers,
      answercount: this.props.answers.length,
      isSaved: this.props.is_saved,
    })

  },
  deleteQuestion: function() {
    Questions.delete(this.props.id);
    this.setState({
      isDeleted: true
    });
  },
  getDefaultProps: function () {
    return ({hideSave: false})
  },
  voteQuestion: function () {
    if (!this.state.userVoted) {
      this.setState({
        userVoted: true,
        votes: ++this.state.votes
      });

      if(window.USER_META['role'] !== 'student') {
        var newEndorsements = this.props.endorsements;
        newEndorsements = newEndorsements.concat(window.USER_META);
        this.setState({
          endorsements: newEndorsements
        })
      }

      upvote(this.props.id, 'question');
    }
  },
  deleteAnswer: function (id) {
    var currentdata = this.state.answerdata;
    this.setState({
      answerdata: update.deleteItem(currentdata, id),
      answercount: --this.state.answercount,
      userAnswered: false
    }, Questions.deleteAnswer(id));
  },
  saveCurrentQuestion: function (id) {
    if(this.state.isSaved) {
      unsaveQuestion(this.props.id)
      this.setState({isSaved: false})
    } else {
      saveQuestion(this.props.id);
      this.setState({isSaved: true})
    }
  },
  voteAnswer: function (id) {
    var currentdata = this.state.answerdata;
    var currentanswer = update.fetchAnswerById(currentdata, id);
    if (!currentanswer.user_voted) {
      this.setState({
        answerdata: update.voteAnswer(window.USER, currentdata, id)
      }, upvote(id, 'answer'));
    }
  },
  submitAnswer: function (answer) {
    var that = this;
    if (answer) {
      addAnswer(answer, this.props.id, (payload) => {
        var jsnpayload = JSON.parse(payload);
        jsnpayload.deleteAnswer = that.deleteAnswer;
        jsnpayload.saveAnswer = that.saveAnswer;
        jsnpayload.voteAnswer = that.voteAnswer;
        jsnpayload.voteText = update.mapElementTextToState('userVoted', jsnpayload['userVoted']);
        jsnpayload.endorsements = [];
        this.setState({
          answerdata: this.state.answerdata.concat(jsnpayload)
        }, this.setState({
          answercount: ++this.state.answercount,
          userAnswered: true,
          responseBoxIsShown: false
        }));
      });
    }

  },
  buildAnswerSlug: function (answers) {
    var answersList = [];
    answers.forEach(answer => {
      answer.deleteAnswer = this.deleteAnswer;
      answer.saveAnswer = this.saveAnswer;
      answer.voteAnswer = this.voteAnswer;
      answer.voteText = update.mapElementTextToState('userVoted', answer.userVoted);
      answersList.push(<Answer key = {this.props.id} {...answer} />);
    });

    return (answersList);
  },
  render: function () {
    var question, owner;
    var voteText = update.mapElementTextToState('userVoted', this.state.userVoted);
    var saveText = update.mapElementTextToState('isSaved', this.state.isSaved);

    var saveGraphic = (this.state.isSaved) ? (<i className="fa fa-bookmark fa-2x" aria-hidden="true"></i>) : (<i className="fa fa-bookmark-o fa-2x" aria-hidden="true"></i>)


    var delQuestionButton, saveQuestion, responseBox, voteQuestion, replyQuestion, answers, questionAnswers;

    if(this.state.answerdata.length > 0) {
      if (Array.isArray(this.state.answerdata))
        answers = this.buildAnswerSlug(this.state.answerdata);
        questionAnswers = (<div className="column-12 border-top">{ answers }</div>)
    }

    if (!window.USER_META) {
    replyQuestion = (<div><div id="g-signin2" class="google-signin"></div>
        <div><a href = {'/'}><button type="button">Sign up to answer this question</button></a></div></div>);
      //saveQuestion = (<a href = {'/'}><button className="btn "btn-link btn-save" type="button">{ saveText }</button></a>);
    }
    if (!this.props.hideSave && !this.props.is_owner) {
      //saveQuestion = (<button className="btn btn-link btn-save" type="button" onClick={this.saveCurrentQuestion}>{ saveGraphic }</button>);
    }
    //if (this.props.is_owner && this.props.showBadges)
      //owner = (<span className="btn btn-owner" type="button">By me</span>)

    if (this.props.is_owner)
      delQuestionButton = (<div><span className="dot"></span><button type="button" className = "delete" onClick={this.deleteQuestion}>Delete</button></div>);
    //if (this.props.votable && window.USER_META && this.props.user_id !== window.USER_META.id)fa-lg
    voteQuestion = (<Votes userVoted={this.state.userVoted} votes={this.state.votes} voteFunc={this.voteQuestion} />);

    if (!this.state.isDeleted)
      question = (
        <div className="column-12 question-col border padding-2 marginNone paddingNoneVertical">
          <div className = "column-12 border">
            <div className = "inline middle">
              <div className="column-12 qaheader">
                <p className="small">{this.props.subject} {this.props.number}</p><span className="dot"></span>
                <p className="small">{this.props.timestamp_ago}</p><span className="dot"></span>
                <p className="small">{this.state.answercount} Answers</p><span className="dot"></span>
                <p className="small">{(this.props.is_owner) ? 'by you' : ''}</p>
                { delQuestionButton }
              </div>
              <div className="column-12 paddingNoneVertical middle">
                <p className="regular">{lineBreaksFromNewlines(this.props.question)}</p>
              </div>
            </div>
            <div className = "left middle">
              { voteQuestion }
            </div>
          </div>
          {(!this.state.userAnswered) ?
          (<Response isAnchor={false} className = "column-12 foundation-form" type = {'question'} sendResponse={this.submitAnswer}/>)
          :
          (null)
          }
          { questionAnswers }
        </div>
      );

    return (<div className="column-12 padding-none margin-vert-2">{ question }</div>);
  }
});

export var Answer = React.createClass({
  getInitialState: function () {
    return ({
      endorsements: this.props.endorsements,
      endorsementsShown: false
    })
  },
  toggleEndorsements: function () {
    var currentState = this.state.endorsementsShown;
    this.setState({
      endorsementsShown: !currentState
    });
  },
  render: function () {
    var deleteAnswer, saveAnswer, voteAnswer;
    if (this.props.is_owner)
      deleteAnswer = (<div><span className="dot"></span><button type="button" className = "delete" onClick={this.props.deleteAnswer.bind(null, this.props.id)}>Delete</button></div>);
    if (!(this.props.is_owner)) {
      voteAnswer = (<div><span className="dot"></span><a className = {"small link"} onClick={(window.USER_META) ? this.props.voteAnswer.bind(null, this.props.id) : initGoogle}>{ this.props.voteText }</a></div>);
    }

    var endorsements = this.state.endorsements.map((element, index) => {
      return (<div key = {createReactRootIndex()} className={"inline left margin-side-2"}><p className = {"regular"}>{element['name']}</p></div>)
    });

    return (
        <li className="column-12 paddingNoneVertical">
            <div>
                <p className = "regular">{lineBreaksFromNewlines(this.props.answer)}</p>
            </div>
            <div className="qaheader">
                <p className="small">{this.props.timestamp_ago}</p>
                <span className="dot"></span><p className="small">{this.props.votes} Votes</p>
                { voteAnswer }
                { deleteAnswer }
            </div>
            <div className = "left">
              {((this.state.endorsements.length)) ? (<div onClick={this.toggleEndorsements}><p className={"small small-link"}>{(this.state.endorsementsShown) ? 'Hide endorsements' : 'View endorsements'}</p></div>) : (null)}
              {(this.state.endorsements.length) ? (<div style={(this.state.endorsementsShown) ? {display: 'block'} : {display: 'none'}}>{ endorsements }</div>) : (null)}
            </div>
        </li>
    )
  }
});

export var Response = React.createClass({
  getDefaultProps: function () {
    return ({
      subject: null,
      number: null,
      questionId: null,
      containStarBar: false,
      isAnswered: false,
      canAnswer: false,
      readerCount: '1.2K',
      placeholder: null,
      sendResponse: function (answer) {
        var that = this;
        addAnswer(answer, this.props.questionId, (payload) => {
        });
      },
    });
  },
  getInitialState: function () {
    return ({
      response: '',
      wordcount: 500,
      focus: false,
      isAnswered: this.props.isAnswered,
    })
  },
  componentDidMount: function () {
      window.addEventListener('click', this.pageClick, false);
  },
  pageClick: function (e) {
    if ((e.target.getAttribute('contenteditable')) === null) {
      this.setState({
        focus: false
      });
      return;
    }
    else {
      if (this.state.focus) {
        return;
      }
    }

    this.setState({
        focus: true
    });
  },
  submitResponse: function (e) {
    if (/\S/.test(this.state.response)) {
      this.props.sendResponse(this.state.response);
      return;
    }
  },
  setResponse: function (e) {
    this.setState({
      wordcount: 500 - e.refs.formInputText.innerText.replace(/ /g,"").length
    });

    if (e.refs.formInputText.innerText) {
      this.setState({
        response: e.refs.formInputText.innerText,
      });
    }
  },
  fetchStatistics: function () {
    var breakdown;
    if (this.state.focus)
      breakdown = this.fetchStatisticsBreakdown();
    return (
      <div className = "column-12 inline paddingNoneHorizontal">
        <p className = "inline reader-stat">{this.props.readerCount} readers are waiting</p>
        { breakdown }
      </div>
    );
  },
  fetchStatisticsBreakdown: function () {
    return (
      <div className = "inline margin-side-2">
        <div className="inline margin-side-1">
          <div className="agreen inline"></div>
          <p className = "small inline margin-side-1">15 instructors</p>
        </div>
        <div className="inline margin-side-1">
          <div className="alogo inline"></div>
          <p className = "small inline margin-side-1">3k students</p>
        </div>
      </div>
    )
  },
  render: function () {
    var wc = this.state.wordcount;
    var wcClass = update.determineWordCountClass(this.state.wordcount);
    var course, responseBar, statBar, placeholder, rightElement, statBreakdownBar;



    if (window.COURSE)
      course = window.COURSE['subject'] + " " + window.COURSE['number'];
    else
      course = this.props.subject + " " + this.props.number;
    if (!this.props.isAnswered && this.props.canAnswer) {
      rightElement = (<button onClick={(window.USER_META) ? this.submitResponse : initGoogle} className={"inline middle loadAlternate segmented max-width-3 right float-right"} style = {posCreate("8px")}>SUBMIT</button>)
    } else if (!this.props.canAnswer) {
      rightElement = (<div className = "inline middle loadAlternate segmented max-width-3 right float-right"><i className="fa fa-lock" aria-hidden="true"></i></div>);
    } else {
      rightElement = (<div className = "inline middle loadAlternate segmented max-width-3 right float-right"><i className="fa fa-check" aria-hidden="true"></i></div>);
    }

    responseBar = (<div className="column-12">
                    <div className = "form-backdrop column-12 max-width-10 inline middle small floatNone" style={(this.state.focus && !this.props.isAnswered) ? {height: "300px"} :{}}
                      contentEditable={(!this.props.isAnswered && this.props.canAnswer)}
                      ref="formInputText"
                      onInput={this.setResponse.bind(null, this)}
                      placeholder = {this.props.placeholder} autoFocus={this.props.autoFocus} onClick={(!this.props.isAnswered && this.props.canAnswer) ? this.pageClick : null}>
                    </div>
                    { rightElement }
                    </div>);
    if (!this.props.isAnswered && this.props.canAnswer)
      statBar = this.fetchStatistics();
    return (
      <div>
        <div>{responseBar}</div>
        <div className = "column-12">{statBar}</div>
      </div>
    )
  }
});

export var PaginatedQuestions = React.createClass({
  propTypes: {
    questionApiFunc: React.PropTypes.func, // questionApiFunc will receive parameters:
                        // (1) page number (int)
                        // (2) sort type (one of 'recent', 'votes', 'answers')
                        // (3) callback accepting the API response as an array of questions
                        // See fetchQuestionsWithCallback for the calling code
    addedQuestions: React.PropTypes.array,
    addedAdvice: React.PropTypes.array
  },
  getInitialState: function () {
    return ({
      filter: 'all',
      sort: 'recent',
    });
  },
  changeFilter: function (event) {
    this.setState({
      filter: event.target.value
    });
  },
  changeSort: function (event) {
    this.setState({
      sort: event.target.getAttribute("value")
    });
  },
  fetchQuestionsWithCallback: function(page, callback) {
    var params = {
      subject: this.props.subject,
      number: this.props.number,
    }
    this.props.questionApiFunc(page, this.state.sort, params, (questions) => {
      var components = questions.map((question) => {
        return(
          <cards.Template key={createReactRootIndex()}
                          preloadedElement = {<Question className = {"column-12 padding-none"}
                                                        key={createReactRootIndex()} {...question}
                                                        hasSkip={false}
                                                        hideSave = {this.props.hideSave}
                                                        showBadges = {this.props.showBadges}
                          />}
                          columns = {1}
                          column_size = {12}
                          className = "column-12 padding-none"/>
        )
      }
      );
      callback(components)
    })
  },
  renderQuestions: function () {
    var components = (<GenericBlock
        column_size = {12}
        columns = {1}
        id = {'questions'}
        hasFunctions={false}
        fetchComponentsWithCallback={this.fetchQuestionsWithCallback}
        type = {'questions'}
        noContentText = {'Ask a question and learn from your peers'}
        //contentNoneComponent = {}
        prependComponents = {this.props.addedQuestions}
        key={createReactRootIndex()}
    />);
    return (components);
  },
  render: function () {
    var questions = this.renderQuestions();
    return (
      <div className="padding-none">
          { questions }
      </div>
    )
  }
});

export var PaginatedAdvice = React.createClass({
  propTypes: {
    adviceApiFunc: React.PropTypes.func, // questionApiFunc will receive parameters:
                        // (1) page number (int)
                        // (2) sort type (one of 'recent', 'votes', 'answers')
                        // (3) callback accepting the API response as an array of questions
                        // See fetchQuestionsWithCallback for the calling code
    addedAdvice: React.PropTypes.array
  },
  fetchAdviceWithCallback: function(page, callback) {
    this.props.adviceApiFunc(this.props.subject, this.props.number, 'time', page, (advice) => {
      var components = advice.map((perAdvice) => {
        return (<Advice className = {"column-12 padding-none"}
                        key={createReactRootIndex()} {...perAdvice}
                        deleteAdvice={this.delete}
                        />);

      });
      callback(components)
    })
  },
  renderAdvice: function () {
    var components = (<GenericBlock
        column_size = {this.props.column_size}
        columns = {1}
        id = {'advice'}
        fetchComponentsWithCallback={this.fetchAdviceWithCallback}
        type = {'advice'}
        redirectURL = {'/profile'}
        noContentText = {'Be the first to contribute some advice!'}
        //contentNoneComponent = {}
        prependComponents = {this.props.addedAdvice}
        key={createReactRootIndex()}
      />);
    return (components);
  },
  render: function () {
    var advice = this.renderAdvice();
    return (
      <div>
        { advice }
      </div>
    )
  }
});

export var PaginatedCourse = React.createClass({
  propTypes: {
    courseApiFunc: React.PropTypes.func // questionApiFunc will receive parameters:

                        // (1) page number (int)
                        // (2) sort type (one of 'recent', 'votes', 'answers')
                        // (3) callback accepting the API response as an array of questions
                        // See fetchQuestionsWithCallback for the calling code
  },
  fetchCourses: function (courses) {
    var components = courses.map((course) => {
      var courseDataPoints;

      return (<cards.Template key={createReactRootIndex()}
                              {...course}
                              datapoints={[`${window.PRETTY_SESSION_BY_MONTH[course.term_month]} ${course.term_year}`,
                                  `${course.units_frmt} units`]}
                              />);
      });
    return (components);
  },
  fetchCourseWithCallback: function(page, callback=null) {
    this.props.courseApiFunc(page, (courses) => {
      callback(this.fetchCourses(courses));
    });
  },
  renderCourse: function () {
    var components = (<GenericBlock
        column_size = {this.props.column_size}
        columns = {1}
        id = {'course'}
        hasFunctions={false}
        fetchComponentsWithCallback={this.fetchCourseWithCallback}
        type = {'courses'}
        redirectURL = {'/profile'}
        noContentText = {'No courses found'}
        header = {this.props.header}
        caption = {this.props.caption}
        key={createReactRootIndex()}
      />);
    return (components);
  },
  render: function () {
    var courses = this.renderCourse();
    return (
      <div>
        { courses }
      </div>
    )
  }
});

export var Advice = React.createClass({
  getInitialState: function () {
    return ({
      isDeleted: false,
      userVoted: this.props.userVoted,
      votes: this.props.votes
    });
  },
  getDefaultProps: function () {
    return ({
      advice: null,
      subject: null,
      number: null,
      title: null,
      hideSave: false,
      userVoted: false,
      votes: 0
    })
  },
  deleteAdvice: function() {
    AdviceController.deleteAdvice(this.props.id, (payload) => {
    })
    this.setState({
      isDeleted: true
    });
  },
  voteAdvice: function () {
    var currentVote = (!this.state.userVoted);
    var votes = this.state.votes;
    this.setState({
      userVoted: currentVote,
      votes: (currentVote) ? (++votes) : (--votes)
    })

    upvote(this.props.id, 'advice');
  },
  render: function () {
    var deleteAdvice, advice, voteAdvice;
    if (this.props.is_owner)
      deleteAdvice = (<div><button type="button" className = "delete" onClick={this.deleteAdvice}>Delete</button></div>);
    else
      voteAdvice = (<Votes userVoted={this.state.userVoted} votes={this.state.votes} voteFunc={this.voteAdvice} />);

    if (!this.state.isDeleted) {
      advice = (<div className="column-12">
          <div className="column-12 qaheader paddingNoneVertical">
            <div>
              <p className="small">{this.props.timestamp_ago}</p>{(this.props.is_owner) ? <span className="dot"></span> : null}</div>
            {(this.props.is_owner) ? (<div><p className="small">by you</p><span className="dot"></span></div>) : null}
            <div>{ deleteAdvice }</div>
          </div>
          <div className="column-12"><div className = "border" style = {{paddingBottom: "15px"}}><p className="regular">{lineBreaksFromNewlines(this.props.advice)}</p></div></div>
      </div>);
    }
    return (
      <div>{advice}</div>
    );
  }
});

export var PaginatedNotifications = React.createClass({
  propTypes: {
    notificationApiFunc: React.PropTypes.func // questionApiFunc will receive parameters:
                        // (1) page number (int)
                        // (2) sort type (one of 'recent', 'votes', 'answers')
                        // (3) callback accepting the API response as an array of questions
                        // See fetchQuestionsWithCallback for the calling code
  },
  fetchNotificationWithCallback: function(page, callback) {
    this.props.notificationApiFunc((notifications) => {
      var components = notifications.map((notification) =>
          <Notification key={createReactRootIndex()} {...notification} />
      );
      callback(components)
    }, page);
  },
  renderNotifications: function () {
    var Notifications = (<GenericBlock
          column_size = {this.props.column_size}
          columns = {1}
          header = {'Notifications'}
          id = {'notifications'}
          caption = {'Updates about your content'}
          fetchComponentsWithCallback={this.fetchNotificationWithCallback}
          type = {'notifications'}
          noContentText = {'No notifications'}
          //contentNoneComponent = {}
          key={createReactRootIndex()}
    />);

    return (Notifications);
  },
  render: function () {
    var notification_list = this.renderNotifications();
    return (
      <div>
        { notification_list }
      </div>
    )
  }
});

export var Notification = React.createClass({
  getInitialState: function () {
    return ({
      isRead: false
    })
  },
  setIsRead: function () {
    this.setState({
      isRead: true
    })
  },
  render: function () {
    return (
      <div className = {(this.state.isRead) ? "column-12 card-col" : "column-12 card-col notification_unread"} onClick={this.setIsRead}>
        <h4>{this.props.notification}</h4>
        <h5>{this.props.timestamp}</h5>
      </div>
      );
  }
});

export var QAStream = React.createClass({
  getDefaultProps: function () {
    return ({
      appendedComponent: []
    })
  },
  getInitialState: function() {
    return {
      addedAdvice: [],
      addedQuestions: [],
      isAnswered: false,
    }
  },
  addAdvice: function (text) {
    var that = this;
      AdviceController.addAdvice(text, this.props.subject, this.props.number, this.props.title, (payload) => {
        const addedAdvice = (<cards.Template key={createReactRootIndex()}
                          preloadedElement = {<Advice className = {"column-12 padding-none"}
                                              key={createReactRootIndex()} {...payload}
                                              subject = {that.props.subject}
                                              number = {that.props.number}
                                              title = {that.props.title}

                          />}
                          columns = {1}
                          column_size = {12}
                          className = "column-12 padding-none"/>);
        const newAddedAdvice = this.state.addedAdvice
        newAddedAdvice.push(addedAdvice)
        that.setState({addedAdvice: newAddedAdvice, isAnswered: true})
      });

  },
  getDefaultProps: function () {
    return ({
      subject: null,
      number: null,
      title: null,
      id: null
    });
  },
  fetchPlaceHolderTextForResponse: function () {
    const course = `${this.props.subject} ${this.props.number}`
    this.setState({
      placeholder: `What is your advice to future ${course} students?`
    });
    // var that = this;
    // User.fetchRelationToCourse(this.props.subject, this.props.number, (relation) => {
    //   that.setState({
    //     placeholder: relation.placeholder
    //   })
    // });
  },
  componentDidMount: function () {
    this.fetchPlaceHolderTextForResponse();
  },
  render: function () {
    var injectedComponents = this.props.appendedComponent.map((element, index) => {
      return (<div key = {createReactRootIndex()}>{element}</div>);
    });
    return (
      <div className="column-12 padding-none">
          <Response type = {(this.props.type === 'question') ? 'question_ask' : 'advice_ask'}
                    isAnchor = {true} key={createReactRootIndex()}
                    sendResponse={this.addAdvice}
                    autoFocus={getUrlParameters()['ask']}
                    isAnswered = {this.state.isAnswered}
                    canAnswer = {true}
                    placeholder = {this.state.placeholder}
                    />
          { injectedComponents }
          <div className="column-12 paddingNoneHorizontal">
            <PaginatedAdvice adviceApiFunc={AdviceController.forCourse.bind(AdviceController)}
              addedAdvice={this.state.addedAdvice}
              subject = {this.props.subject} number = {this.props.number}/>
          </div>
      </div>
    );
  }

});

export var CourseStream = React.createClass({
  getDefaultProps: function () {
    return ({
      type: null,
      functionAPI: null,
      column_size: null,
      header: null,
      caption: null,
    });
  },
  render: function () {
      return (
        <div>
            <PaginatedCourse
                header = {this.props.header}
                caption = {this.props.caption}
                column_size = {this.props.column_size}
                courseApiFunc={this.props.courseApiFunc}
           />
        </div>
      );
    }
});

export var ToggleBody = React.createClass({
  getInitialState: function () {
    return ({
      localParams: getUrlParameters(),
      sortParam: this.accessSortToggle(this.props.liveParams, 'add')
    })
  },
  getDefaultProps: function () {
    return ({
      toggles: [],
      liveParams: getUrlParameters(),
    })
  },
  swapToggle: function (event) {
    const params = getUrlParameters();
    params[event.target.name] = event.target.value;
    refreshWithNewParam(params);

    this.setState({
      sortParam: event.target.value
    });
  },
  accessSortToggle: function (paramList, func) {
    var that = this, objToReturn = paramList;
    var tempParamList = paramList;
    var togglesToCheck = this.sortToggles();
    Object.keys(paramList).forEach((element) => {
      Object.keys(togglesToCheck).forEach((elementToCompare) => {
        if (togglesToCheck[elementToCompare] in paramList) {
          if (func === 'delete') {
              if (element !== that.state.sortParam)
                delete tempParamList[togglesToCheck[elementToCompare]]
              objToReturn = tempParamList;
          } else {
            objToReturn = element;
          }
        }
      });
    });
    return (objToReturn);
  },
  sortToggles: function () {
    var togglesToReturn;
    this.props.toggles.forEach((toggle)=> {
      if (toggle['type'] === 'dropdown') {
        togglesToReturn = toggle['toggles'];
      }
    });
    return (togglesToReturn);
  },
  determineCheck: function (key) {
    if (key && (parseInt(this.state.localParams[key]) === 1))
      return(true);
    return (false);
  },
  toggleFilter: function (event) {
    var isChecked = event.props.toggle, params = getUrlParameters();
    if (params[isChecked]) {
      delete params[isChecked];
    }
    else {
      params[isChecked] = "1"
    }

    refreshWithNewParam(params);
  },
  toggleMobileOptions: function () {

  },
  anyToggleChecked: function(toggles) {
    const urlParams = getUrlParameters()
    return Object.values(toggles).some(function(param) {
      return urlParams[param] === 1
    });
  },
  render: function () {
    var that = this;
    var components = this.props.toggles.map((section, index) => {
      return (
        <div key = {createReactRootIndex()}>
          <p className="tab heavy padding-1">{section['title']}</p>
          {(Object.keys(section['toggles']).length > 5) ? (<button className={"mobileTrue load"} onClick={
            ()=>{
              var toggle = document.getElementsByClassName('showhide');
              toggle = toggle[0];
              if (!toggle.style.display){
                toggle.style.display='block';
              }
              else {
                toggle.style.display='';
              }
            }
          }>Show areas</button>) : (null)}
          <div className={(Object.keys(section['toggles']).length > 5 && !this.anyToggleChecked(section['toggles'])) ? "showhide padding-1 paddingNoneHorizontal mobileFalse" : "padding-1 paddingNoneHorizontal"}>
            {
            (section['type'] === 'checkbox') ?
                (Object.keys(section['toggles']).map((key, innerIndex) => {
                  return (
                    <Toggle toggle={section['toggles'][key]}
                            isChecked={that.determineCheck(section['toggles'][key])}
                            toggleFilter={that.toggleFilter}
                            prettyToggle={key}
                            key = {createReactRootIndex()}
                            type = {section['type']} />
                  );
                })) : (<select key = {createReactRootIndex()}
                               name={section['name']}
                               id = "sortSelect"
                               className = "dropdown width-10 column-12 floatNone"
                               onChange={this.swapToggle}
                               value={getUrlParameters()[section['name']]}>
                          {Object.keys(section['toggles']).map((innerKey, innerIndex)=> {
                            return (<option key = {createReactRootIndex()} value={section['toggles'][innerKey]}>{innerKey}</option>);
                          })};
                      </select>)
            }
          </div>
        </div>
      );
    });
    return (<div key = {createReactRootIndex()}>
              {components}
            </div>
           )
  }
})

export var Toggle = React.createClass({
  getDefaultProps: function () {
    return ({
      toggle: null,
      isChecked: false,
      toggleFilter: () => {},
      prettyToggle: null
    })
  },
  render: function () {

    var component = (<div className = "paddingNoneHorizontal" key = {createReactRootIndex()}>
                            <input className={"column-1"}
                               type="checkbox" name={this.props.toggle}
                               id={this.props.toggle}
                               defaultChecked = {this.props.isChecked}
                               onChange={this.props.toggleFilter.bind(null, this)}/>
                            <p htmlFor={this.props.toggle} className={"small paddingNoneVertical inline"}>{this.props.prettyToggle}</p></div>);
    return (
      <div>
        { component }
      </div>
    )
  }
});

export var Warning = React.createClass({
  getDefaultProps: function () {
    return ({
      message: null,
      link: null
    })
  },
  getInitialState: function () {
    return ({
      closed: false
    });
  },
  removeWarning: function () {
    this.setState({
      closed: true
    });
  },
  render: function () {
    return (
      <div className={"width-10 padding-full-1 carousel wrapper-12 margin-3 warning"} style = {(this.state.closed) ? {display: 'none'} : {display: 'block'}}>
        <p className={"link"}><a href = {this.props.link}>{this.props.message}</a><span onClick={this.removeWarning}><i className="fa fa-times" aria-hidden="true"></i></span></p>
      </div>
    )
  }
});

export var CourseCatalog = React.createClass({
  popRandomDepartment: function(departments) {
    var idx = parseInt((Math.random() * departments.length));
    var randomDept = departments.splice(idx, 1)[0]; // Removes element in place from departments
    return randomDept;
  },
  nextDepartment: function (departments) {
    var department = this.popRandomDepartment(departments);
    var deptNumbers = department['numbers'];
    var randomNumbers = [];

    while(randomNumbers.length < 2 && department['numbers'].length > 0 ) {
      const number = department['numbers'].splice(Math.floor(Math.random()*deptNumbers.length), 1);
      randomNumbers.push(number);
    }

    department['numbers'] = randomNumbers;

    return (department);
  },
  render: function () {
    const departments = this.props.departments;
    var catalogs = (Array(50).fill(4)).map((constant, index) => {
      var item = this.nextDepartment(departments);
      var items = item['numbers'].map((element, idx) => {
        return (
          <cards.Template key={createReactRootIndex()}
          columns = {1}
          column_size = {12}
          className = "column-12 padding-none"
          subject= {item['code']}
          url = {"/course/" + item['code'] + "/" + element[0]}
          number={element[0]}
          showGrades = {false}/>
        );

      });
      return (
        <div key = {createReactRootIndex()} className="center column-4">
          <div className="column-12">
            <h2><a href={"/search?q=" + item['code']}>{item['subject_name']}</a></h2>
          </div>
          {items}
        </div>
      );
    });

    return (
      <div>{catalogs}</div>
    )
  }
});

export var SJA_activity = React.createClass({
  getDefaultProps: function () {
    grades: null
  },
  fetchY: function () {
    var SJAcount = 0;
    this.props.grades.forEach((element, index) => {
      if (element['letters'].indexOf('Y') > -1)
        SJAcount += element.counts[element['letters'].indexOf('Y')]
    });

    return (SJAcount);
  },
  render: function () {
    var count = this.fetchY();
    return (
      <p className = {(count > 50) ? "small span-logo" : "small span-green"}>{(count > 50) ? "High activity: " + count + " cases reported (Y's)" : "Low activity: " + count + " cases reported (Y's)"}</p>
    )
  }
});

export var Me = React.createClass({
  render: function () {
    var user = window.USER_META;
    var programs = user.programs.map((major, index) => {
      return (<p key = {createReactRootIndex()} className="regular">{major.name}</p>);
    });
    if(!programs.length) {
      programs = (<a href="/settings"><p className="regular">Edit major</p></a>);
    }
    var update_transcript;
    if(user.transcript_needs_update) {
      update_transcript = (<a href="/settings"><div className="column-12 load center"><p className="tab heavy" style = {{color: "white"}}>UPDATE YOUR TRANSCRIPT</p></div></a>);
    }
    return (
      <div>
        <p className="large column-12">{user.name}</p>
        <div className="column-12">
          <div className="column-12">
            <p className="heavy tab padding-1">EMAIL</p>
            <p className="regular">{user.email}</p>
          </div>
          <div className="column-12">
            <p className="heavy tab padding-1">DEGREES</p>
            <div>{programs}</div>
          </div>
          <div className="column-12">
            <p className="heavy tab padding-1">CONTRIBUTIONS</p>
            <p className="regular">{ user.answer_count } answers</p>
          </div>
        </div>
        <div className="column-12"><div className="column-12">{ update_transcript }</div></div>
      </div>
    );
  }
});

loadSassVariables();
