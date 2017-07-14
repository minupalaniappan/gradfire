/* For the header */
import * as common from 'common'
import { GenericBlock } from 'block'
import { Questions, Courses, Advice, User } from 'api'
import * as graph from 'graph'
import * as update from 'update'


export var renderAutoComplete = function () {
  if (document.getElementById('autocompleteSearch')) {
  const query = common.getUrlParameters()['q'];
  ReactDOM.render(<common.AutocompleteSearch
    key={common.createReactRootIndex()}
    query={query} />, document.getElementById('autocompleteSearch'));
  }

}
export var studentDriver = function () {
  var profileContent = (<common.CourseStream
                    column_size = {12}
                    id = {'completed'}
                    type = {'completed'}
                    courseApiFunc={Courses.completedCourses}
                    />);
  var profileMe = (
    <common.Me />
  )

  User.surveyPrompt((survey) => {
    console.log(survey)
    var responseBar = (<common.Response
                        containStarBar={true}
                        subject={survey['subject']}
                        number={ survey['number']}
                        placeholder={survey['prompt']}
                        sendResponse={function(advice) {
                          Advice.addAdvice(advice,
                            survey['subject'],
                            survey['number'],
                            survey['title'], function(posted) {
                              window.location = survey['course_url'];
                            });
                        }}
                        readerCount={survey['reader_count']}
                        instructorCount={survey['instructor_count']}
                        studentCount={survey['student_count']}
                        isAnswered = {false}
                        canAnswer = {true}
                      />);
      ReactDOM.render(responseBar, document.getElementById('promptBar'));
    });

  ReactDOM.render(profileContent, document.getElementById('dataCompleted'));
  ReactDOM.render(profileMe, document.getElementById('profileProvider'));
}


/* For the course header */

export var courseCommunityTabs = function () {

  var graphElement = null;

  if (!window.USER_META) {
    graphElement = (<graph.GraphWarning url={'/'}
      message={'Make an account to view grade statistics history'}
      imageUrl={'/static/imgs/grades.png'} />);
  } else if (!window.COURSE['grades'].length) {
    graphElement = (<graph.GraphWarning url={'/about'} message={'This class does not have data'}/>);
  } else if (window.USER_META['transcript_needs_update']) {
    graphElement = (<graph.GraphWarning url={'/settings?ref=course'}
      message={'Upload your classes to view grade distributions'}
      imageUrl={'/static/imgs/grades.png'} />);
  }
  else {
    var instructors = update.fetchInstructorsForGradeDistribution(window.COURSE['grades']);
    graphElement = (<graph.GradeDistributionBody key={common.createReactRootIndex()} instructors={instructors}/>);
  }

  ReactDOM.render(<common.QAStream
                    type = {'advice'}
                    key={common.createReactRootIndex()}
                    subject = {window.COURSE['subject']}
                    column_size = {12}
                    appendedComponent = {[graphElement]}
                    id = {window.COURSE['id']}
                    number = {window.COURSE['number']}
                    title = {window.COURSE['title']}/>, document.getElementById('dataReviews'));

  ReactDOM.render(<common.SJA_activity grades={window.COURSE['grades']} />, document.getElementById('sja_activity'));


}

export var headerDriver = function () {
  renderAutoComplete()
}
