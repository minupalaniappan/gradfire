import * as common from 'common'
import * as update from 'update'


export var GradeDistributionBody = React.createClass({
	getInitialState: function () {
		return ({
			instructor: this.props.instructors[0],
			term: this.termFinder()
		});
	},
	termFinder: function () {
		var term = update.fetchTerms(window.COURSE['grades'], this.props.instructors[0])[0];
		term = term['term_month'] +"," + term['term_year'];
		return (term);
	},
	buildInstructors: function () {
		var instructors = this.props.instructors;
		var options = [];

		instructors.forEach(instructor => {
			options.push(<option className = {"dropdown-font-blank"} key={common.createReactRootIndex()} value = {instructor}>{instructor}</option>);
		});

		return (options);
	},
	buildTerms: function () {
		var terms = update.fetchTerms(window.COURSE['grades'], this.state.instructor);
		var options = [];

		terms.forEach(term => {
			options.push(<option key={common.createReactRootIndex()}
								 className = {"dropdown-font-blank"}
								 value = {term['term_month'] + "," + term['term_year']}>
								 {term['pretty_term_month'] + " " + term['term_year']}
						</option>);
		});

		return (options);
	},
	buildChart: function () {
		var term = this.state.term.split(",")[0];
		var year = this.state.term.split(",")[1];
		var chartObject = update.findGradeDistributionData(window.COURSE['grades'],
						 								   this.state.instructor,
						 								   term,
						 								   year);

		return (<GradeChart data={chartObject} />);
	},
	changeInstructor: function (event) {
		var newTerm = update.fetchTerms(window.COURSE['grades'], event.target.value)[0];
		var termVal = newTerm['term_month'] + "," + newTerm['term_year'];
		this.setState({
			instructor: event.target.value,
			term: termVal
		});
	},
	changeTerm: function (event) {
		this.setState({
			term: event.target.value
		});
	},
	render: function () {
		var instructors = this.buildInstructors();
		var terms = this.buildTerms();
		var chart = this.buildChart();

		return (
			<div>
				<div className = "width-5 inline padding-combo-1-2">
					<p className={"tab heavy"}>INSTRUCTOR</p>
                </div>
                <div className = "width-5 inline padding-combo-1-2">
					<p className={"tab heavy"}>TERM</p>
                </div>
				<div className = "width-5 inline paddingNoneHorizontal center padding-1 border">
					<select className= "width-10 dropdown-blank column-6" id = "select_teacher_per_term_data"
	                		onChange={this.changeInstructor}
	                		value = {this.state.instructor}
	                		style = {{paddingLeft: "20px"}}
	                		>
	                	{ instructors }
	                </select>
                </div>
                <div className = "width-5 inline paddingNoneHorizontal center padding-1 border">
					<select className= "width-10 dropdown-blank column-6" id = "select_teacher_per_term_data"
	                		onChange={this.changeTerm}
	                		value = {this.state.term}
	                		style = {{paddingLeft: "20px"}}
	                		>
	                	{ terms }
	                </select>
                </div>
	            <div className="column-12">
	            	{ chart }
	            </div>
            </div>
		)
	}
});

export var BarChartAggregate = React.createClass({
	getDefaultProps: function () {
		return ({
			labels: [],
			counts: []
		})
	},
	updateCanvas: function () {
        const ctx = this.refs.canvas.getContext('2d');
        this.loadGraph(ctx);
    },
    fetchPercentage: function (arr) {
    	var that = this;
    	arr = arr.map((elem, index)=> {
    		return ((elem*100)/(that.props.counts.reduce(function(a, b) { return a + b; }, 0)))
    	});
    	return (arr);
    },
	loadGraph: function (ctxRef) {
		var grades = {counts: this.props.counts, distributions: this.fetchPercentage(this.props.counts), letters: this.props.labels}
		var data = {
		    labels: this.props.labels,
		    datasets: [{
		        backgroundColor: "#C2D1FF",
		        borderColor: "#C2D1FF",
		        borderWidth: 1,
		        hoverBackgroundColor: "#295EFF",
		        hoverBorderColor: "#295EFF",
		        data: this.fetchPercentage(this.props.counts)
		    }],
		};
		var myBarChart = new Chart(ctxRef, {
	        type: 'bar',
	        data: data,
	        options: {
		        legend: {
		          display: false
		        },
		        animation: false,
		        scales: {
	        	  gridLines: {
                    display:false
                  },
		          yAxes: [{
		            ticks: {
		              callback: function(value, index, ticks) {
		                return (value + '%');
		              }
		            },
		          }],
		          xAxes: [{
		          	gridLines: {
						color: 'rgba(0,0,0,0)'
					}
		          }]
		        },
		        tooltips : {
		          callbacks: {
		             title: function(tooltipItems, data) {
		              return(grades['counts'][tooltipItems[0]['index']] + " students");
		            },
		             label: function(tooltipItems, data) {
		                return(grades['distributions'][tooltipItems['index']].toFixed(2) + "% " + grades['letters'][tooltipItems['index']] + "'s");
		              }
		            }
		          }
		        }
	    });
    },
    componentDidMount: function () {
	    this.updateCanvas();
    },
	render: function () {
		return (
			<div><canvas ref = "canvas" style = {{height: 'auto', width: '100%'}}/></div>
		)
	}
});

export var GradeChart = React.createClass({
	componentDidMount: function () {
	    this.updateCanvas();
    },
    componentDidUpdate: function () {
    	if (window.COURSE['gradechart'])
    		window.COURSE['gradechart'].destroy();

    	this.updateCanvas();
    },
    updateCanvas: function () {
        const ctx = this.refs.canvas.getContext('2d');
        this.loadGraph(ctx);
    },
    loadGraph: function (ctxRef) {

    	var grades = this.props.data;
    	var indexOfAverageGrade = grades['letters'].indexOf(grades['avg_letter_grade']);

    	backgroundColorArray = [];
	    hoverBackgroundColorArray = [];
	    borderColorArray = [];
	    borderColorHoverArray = [];

	    for (var i = 0; i < grades['letters'].length; i++) {
		    if(i == indexOfAverageGrade) {
		      backgroundColorArray.push("#FF4262");
		      hoverBackgroundColorArray.push("#FF4262");
		      borderColorArray.push("#FF4262");
		      borderColorHoverArray.push("#FF4262");
		    } else {
		      backgroundColorArray.push("#C2D1FF");
		      hoverBackgroundColorArray.push("#C2D1FF");
		      borderColorArray.push("#295EFF");
		      borderColorHoverArray.push("#295EFF");
		    }
		}

		var data = {
		    labels: grades['letters'],
		    datasets: [{
		        label: "Grade Distributions for " + grades['instructor'],
		        backgroundColor: backgroundColorArray,
		        borderColor: borderColorArray,
		        borderWidth: 1,
		        hoverBackgroundColor: hoverBackgroundColorArray,
		        hoverBorderColor: borderColorHoverArray,
		        data: grades['distributions']
		    }],
		};
		var myBarChart = new Chart(ctxRef, {
	        type: 'bar',
	        data: data,
	        options: {
		        legend: {
		          display: false
		        },
		        animation: false,
		        scales: {
		          gridLines: {
	                display:false
	              },
	              scaleLabel: "<%= ' ' + value%>",
		          yAxes: [{
		            ticks: {
		              callback: function(value, index, ticks) {
		                return (value + '%');
		              }
		            },
		          }],
		          xAxes: [{
		          	gridLines: {
						color: 'rgba(0,0,0,0)'
					}
		          }]
		        },
		        tooltips : {
		          callbacks: {
		             title: function(tooltipItems, data) {
		              return(grades['counts'][tooltipItems[0]['index']] + " students");
		            },
		             label: function(tooltipItems, data) {
		              if(indexOfAverageGrade == tooltipItems['index']) {
		                return(grades['distributions'][tooltipItems['index']].toFixed(2) + "% " + grades['letters'][tooltipItems['index']] + "'s (average)");
		              } else {
		                return(grades['distributions'][tooltipItems['index']].toFixed(2) + "% " + grades['letters'][tooltipItems['index']] + "'s");
		              }
		            }
		          }
		        }
	        }
	    });

	    window.COURSE['gradechart'] = myBarChart;

    },
 	render: function () {
		return (
			<div><canvas ref = "canvas" style = {{height: 'auto', width: '100%'}}/></div>
		)
	}
});

export var LineChart = React.createClass({
	getDefaultProps: function () {
		return ({
			labels: [],
			data: []
		})
	},
	componentDidMount: function () {
	    this.updateCanvas();
    },
    updateCanvas: function () {
        const ctx = this.refs.canvas.getContext('2d');
        ctx.canvas.width = 100;
		ctx.canvas.height = 30;
        this.loadGraph(ctx);
    },
    loadGraph: function (ctxRef) {

    	var data = {
		    labels: this.props.labels,
		    datasets: [{
		        borderWidth: 2,
		        borderColor: "#59ABE3",
		        backgroundColor: "#FFFFFF",
		        data: this.props.counts,
		        lineTension: 0
		    }],
		};

		var options = {
			animation: false,
			elements: {
				point: {
					radius: 0,
					borderWidth: 0
				}
			},
			legend: {
				display: false
			},
			tooltips: {
				enabled: false
			},
			scales: {
				gridLines: {
					display: false
				},
				xAxes: [{
	                display: false
	            }],
	            yAxes: [{
	                display: false
	            }]
			}
		};

		var myLineChart = new Chart(ctxRef, {
			type: 'line',
			data: data,
			options: options
		});

	},
	render: function () {
		return (
			<div style = {{height: '30px', width: '100px'}}><canvas width = "30" height = "100" ref = "canvas" style = {{height: '30px', width: '100px'}}/></div>
		)
	}

});

export var GraphWarning = React.createClass({
	propTypes: {
		url: React.PropTypes.string,
		message: React.PropTypes.string,
		imageUrl: React.PropTypes.string
	},
	render: function () {
		let image = null;
		if(this.props.imageUrl) {
			image = (<img style={{opacity: 0.5}} src={this.props.imageUrl} />)
		}
		return (
			<div><p className={"link"}><a href = {this.props.url}>{this.props.message}{ image }</a></p></div>
		)
	}
});