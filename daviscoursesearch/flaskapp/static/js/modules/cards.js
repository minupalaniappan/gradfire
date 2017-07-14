import * as common from 'common'
import * as update from 'update'
import * as graph from 'graph'

export var Template = React.createClass({
  getDefaultProps: function () {
    return ({
      datapoints: [],
      number: null,
      url: null,
      title: null,
      subject: null,
      type: 'course',
      instructor: null,
      instructorurl: null,
      appendedComponent: null,
      preloadedElement: null
    });
  },
  render: function () {
    var element;
    if (this.props.preloadedElement === null) {
      element = (<Row datapoints = {this.props.datapoints}
                        url = {this.props.url}
                        subject = {this.props.subject}
                        number = {this.props.number}
                        title = {this.props.title}
                        type = {this.props.type}
                        instructor = {this.props.instructor}
                        instructorurl = {this.props.instructorurl}
                        appendedComponent = {this.props.appendedComponent}
                         />);
    }
    else {
      element = this.props.preloadedElement;
    }

    return (
      <div key = {common.createReactRootIndex()} className={"column-12 padding-none"}>{ element }</div>
    );
    }
});

export var Row = React.createClass({
  getDefaultProps: function () {
    return ({
      type: 'course',
      appendedComponent: null
    });
  },
  buildDataBlock: function () {
    var subdata = (<div>
                    {this.props.datapoints.map((datapoint, index) => {
                      if (this.props.datapoints[index+1])
                        return (<div key = {common.createReactRootIndex()}><p key = {common.createReactRootIndex()} className="small inline middle">{datapoint}</p><span className="dot"></span></div>);
                      else
                        return (<div key = {common.createReactRootIndex()}><p key = {common.createReactRootIndex()} className="small inline middle">{datapoint}</p></div>);

                    })}
                  </div>);
    return (subdata);
  },
  render: function () {
    var subdata = this.buildDataBlock();
    var content;
    if (this.props.type === 'instructor') {
      content = (<a href = {this.props.instructorurl} className = "inline large no-wrap">{this.props.instructor}</a>);
    } else {
      content = (<a href = {this.props.url} className = "inline large no-wrap">{this.props.subject} {this.props.number.replace(/\b0+/g, '')}&nbsp;{this.props.title}</a>);
    }
    return (
      <div className="column-12 list_caption padding-combo-3-1">
        <div className = {"inline middle"}>
          <div>
            { content }
          </div>
          <div className="qaheader padding-vert-none inline middle" style = {common.posCreate("2px")}>
            { subdata }
          </div>
        </div>
        <div className = "inline middle float-right center">
          { this.props.appendedComponent }
        </div>
      </div>
    );
  }
});
