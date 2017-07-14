import {Programs} from 'api'
import Autocomplete from 'autocomplete';

const InstructorVerification = React.createClass({
    render: function() {
        return (<div className="padding-2">
                <h3 className="padding-1">Help us identify you</h3>
                  <div className="padding-1">
                      <p className="regular padding-1">See your teaching history</p>
                      <p className="regular padding-1">Contribute to your classes' instructor notes and help students prepare</p>
                      <p className="regular padding-1">Read and answer questions about your classes</p>
                      <p className="regular padding-1">Endorse student answers</p>
                  </div>
                  <div className = "load margin-2 padding-full-1 center"><p className = "regular" style = {{color: 'white'}}>Currently still in development</p></div>
                </div>
                // Autocomplete
                );
    }
});

function tokenize(text) {
    const nonAlphaNum = text.replace(/[^0-9a-z \t\r\n\f]/gi, '');

    return nonAlphaNum.toLowerCase().split(/\s+/)
}

function matchingDegreeTracks(query, programs) {
    // Fetch and cache degree tracks from API onload
    // Filter & sort to matches relevant to query (tokenize, strip special chars, check for start/match wordwise)
    // Handle case where degree tracks not loaded? Cancel/retry?
    const queryTokens = tokenize(query);
    const rankedPrograms = programs.map((program) => {
        const programTokens = tokenize(program.long_name);
        const wordMatches = queryTokens.filter((queryToken) => {
            programTokens.indexOf(queryToken) !== -1
        });
        const partialWordMatches = queryTokens.filter((queryToken) => {
            const isNotWordMatch = programTokens.indexOf(queryToken) == -1
            const isPartialWordMatch = programTokens.some((programToken) => {
                return programToken.indexOf(queryToken) == 0
            });
            return isNotWordMatch && isPartialWordMatch
        });

        return {program: program,
                ranking: 5 * wordMatches.length + Math.ceil(partialWordMatches.length / 2)}
    });
    return (rankedPrograms.filter(p => p['ranking'] > 0)
            .sort((p1, p2) => p1['ranking'] - p2['ranking']))
            .map(programAndRanking => programAndRanking['program'])
            .slice(0, 5);
}

const ProgramSelect = React.createClass({
  getInitialState: function() {
    return {programs: []}
  },
  addProgram: function(program) {
    if(this.state.programs.map(p => p['id']).indexOf(program['id']) != -1) {
      return;
    }
    this.setState({programs: this.state.programs.concat([program])});
  },
  removeProgram: function(program_id) {
    console.log(program_id)
    this.setState({programs: this.state.programs.filter(p => p['id'] != program_id)})
  },
  componentDidMount: function () {
    if (this.props.user)
      this.setState({programs: this.props.user.programs})
  },
  render: function() {
    const programComponents = this.state.programs.map((program) => {
      return <Program key={program['id']}
                      onRemove={this.removeProgram.bind(this, program['id'])}
                      program_id={program['id']}
                      {...program} />;
    });
    return (
      <div>
        <AutocompletePrograms onSelect={this.addProgram} />
        {programComponents}
      </div>
    );
  }
});

const Program = React.createClass({
  propTypes: {
    onRemove: React.PropTypes.func.isRequired,
    program_id: React.PropTypes.number,
    name: React.PropTypes.string,
    variant: React.PropTypes.string,
    type: React.PropTypes.string,
    long_name: React.PropTypes.string
  },
  render: function() {
    return (
      <div>
        <p className="regular inline">{(this.props.long_name) ? this.props.long_name : this.props.name}</p>
        <input className = "inline" type="hidden" name="programs" value={this.props.program_id} />
        <p onClick={this.props.onRemove} className="inline"><i className="fa fa-times" aria-hidden="true"></i></p>
      </div>
    );
  }
});
const AutocompletePrograms = React.createClass({
    propTypes: {
      onSelect: React.PropTypes.func.isRequired
    },
    getInitialState: function () {
      return ({
        query: '',
        results: [],
        loading: false,
      });
    },
    render:  function() {
        var queryInputContainer  = (
        <div className="foundation-form padding-1" id="autocompleteProgram">
          <Autocomplete
            inputProps={{name: "q", id: "query_input_large", className: "", placeholder: "Psychology, B.S."}}
            ref="autocomplete"
            value={this.state.query}
            resize={this.state.resize}
            items={this.state.results}
            getItemValue={(item) => item.name}
            onSelect={(value, item) => {
              this.props.onSelect(item);
              this.setState({query: ''});
            }}
            onChange={(event, value) => {
              event.persist();
              this.setState({ query: event.target.value })
              this.setState({ value, loading: true })
              Programs.programsForUniversity((programs) => {
                const tracks = matchingDegreeTracks(event.target.value, programs)
                this.setState({results: tracks, loading: false})
              });
            }}
            renderItem={(item, isHighlighted, index) => (
              <div style={{display: "block", backgroundColor: (!index || !(index%2)) ? "#FAFAFA" : "white",
                                                 borderTop: (!index || !(index%2)) ? "1px solid #EBEBEB" : "none",
                                                 borderBottom: (!index || !(index%2)) ? "1px solid #EBEBEB" : "none"}} className="padding-1">
                <div
                  key={item.id}
                  className="autocomplete-item padding-1 column-12 wrapper-12"
                  style={{display: "block"}}
                  >
                    <a href="#">
                      <div>
                        <span>{item.long_name}</span>
                      </div>
                    </a>
                  </div>
              </div>
            )}
          />
        </div>);

        return (<div>{queryInputContainer}</div>);
    }
});
const DegreeTrackSelect = React.createClass({
    propTypes: {
        degreeTracks: React.PropTypes.arrayOf(React.PropTypes.object)
    },
    render: function() {

    }
});
const TranscriptUpload = React.createClass({
    getInitialState: function () {
      return ({
        transcript: ''
      });
    },
    handleChange(event) {
      this.setState({transcript: event.target.value});
    },
    render: function() {
        return (<div id="transcript-upload" >
            <div className="padding-2 center">
            <h3 className="regular padding-1 left">What are you studying?</h3>
              <ProgramSelect />
            </div>
            <div>
              <h3 className="regular padding-1 left">Upload your classes</h3>
              <p class="regular">Personalize your Gradfire experience in 3 easy steps</p>

              <div className="padding-1">
                <p className="regular">1. <a target="_blank" className="link" href="https://students.ucdavis.edu/student/courses.aspx?sv=true">Visit Oasis</a></p>
              </div>
              <div className="padding-1">
                <p className="regular">2. Login, and copy the whole page.</p>
                <p class="regular">Mac: Command-A, Command-C</p>
              <p class="regular">Windows: Ctrl-A, Ctrl-C</p>
              </div>
              <div className="padding-1">
                <p className="regular">3. Paste your transcript into the input box below.</p>
              </div>
            </div>
            <div className = "upload_privacy"></div>
          <div className="padding-1 center">
              <textarea id = "transcript_upload"
                        name="transcript"
                        placeholder={"Paste transcript here"}
                        value = {this.state.transcript}
                        className = "width-10 padding-full-1"
                        style = {{border: 'none', color: '#AAADAD', border: '1px solid #F5F5F5', fontSize: '18px'}}
                        onChange={this.handleChange} />
              <input className = "load margin-2 padding-full-1" disabled={(this.state.transcript === '') ? 'disabled' : ''} type="submit" value = {(this.state.transcript) ? 'Finish' : 'Fill in all fields'}/>
          </div>
        </div>);
    }
});

const UserRoleChoices = React.createClass({
    propTypes: {
        userRoles: React.PropTypes.arrayOf(React.PropTypes.object)
    },
    getInitialState: function () {
      return ({
        selected: 'student'
      })
    },
    setRole: function (role) {
      var tempRole = role;
      this.setState({
        selected: tempRole
      });

      switch(role) {
        case 'student':
          showTranscriptUpload();
          break;
        case 'instructor':
          showInstructorVerification();
          break;
        default:
          break;
      }
    },
    componentDidMount: function () {
      this.setRole(this.state.selected);
    },
    render: function() {
        const choices = this.props.userRoles.map((role) => {
            return <UserRoleChoice onclick = {this.setRole} key={role.role} {...role} selected={this.state.selected === role.role}/>
        });
        return (<div>{choices}</div>);
    }
});

const UserRoleChoice = React.createClass({
    propTypes: {
        role: React.PropTypes.string,
        rolePretty: React.PropTypes.string,
        onclick: React.PropTypes.func
    },
    render: function() {
        return <div
             className={"user-role-choice width-absolute-10 inline padding-full-1 width-10 bg-card"
             }
             data-role={this.props.role}
             onClick={this.props.onclick.bind(null, this.props.role)}
             ><p className={(this.props.selected) ? "hover regular selected" : "hover regular"}>{this.props.rolePretty}</p></div>
    }
});

const transcriptUpload = <TranscriptUpload />
const showTranscriptUpload = () => {
    ReactDOM.render(transcriptUpload, document.getElementById('user-role-detail'))
};

const instructorVerification = <InstructorVerification />
const showInstructorVerification = () => {
    ReactDOM.render(instructorVerification, document.getElementById('user-role-detail'))
};

const userRoles = [
    {'role': 'student',
     'rolePretty': 'Student'
    },
    {'role': 'instructor',
     'rolePretty': 'Instructor'
    }
];

export const MajorSelect = ProgramSelect;

export function _init() {
    ReactDOM.render(<UserRoleChoices userRoles={userRoles} />, document.getElementById('user-role-choices'));
}