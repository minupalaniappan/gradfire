import * as common from 'common'
import * as graph from 'graph'

export var _init = function() {
	let CHE2ADATA = {
		'A+': 18,
		'A': 16,
		'A-': 17,
		'B+': 35,
		'B': 35,
		'B-': 35,
		'C+': 74,
		'C': 71,
		'C-': 33,
		'D+': 17
	}




	ReactDOM.render(<graph.BarChartAggregate labels={Object.keys(CHE2ADATA)} counts={Object.values(CHE2ADATA)}/>, document.getElementById('example-chart'));
	ReactDOM.render(<common.AutocompleteSearch key={common.createReactRootIndex()} />, document.getElementById('homeSearch'));
	ReactDOM.render(<common.CourseCatalog departments={window.SUBJECTS_AND_CLASSES} />, document.getElementById('subjectsandcourses'));
}