import * as common from 'common'
import * as cards from 'cards'


export var CoursesTaught = React.createClass({
	fetchCourses: function () {
		var courses = window.taught.map((course, index) => {			
			return ({
				subject: course[0][0], 
				number: course[0][1], 
				title: course[0][2],
				frequency: course[1].length, 
				current: (_.where(course[1], {is_current: true}).length > 0),
				url: course[1][0].url
			})
		}); 
		return (courses);
	}, 
	render: function () {
		var rows = this.fetchCourses(); 
		var renderedRows = rows.map((result, index) => {
			var isTeaching = (result.current) ? ("Currently teaching") : (null);
			return (
				<cards.Template key={common.createReactRootIndex()}
								{...result}
	                            datapoints={[`Taught ${result.frequency} times`, isTeaching]}/>
			)
		});
		return (
			<div>{renderedRows}</div>
		)
	}
}); 

export var _init = function() { 
	ReactDOM.render(<CoursesTaught />, document.getElementById('term-list'));
}