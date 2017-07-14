import * as common from 'common'
import { GenericBlock } from 'block'
import * as cards from 'cards'

export var _init = function() {
	var binaryToggles;
	if (window.USER_META && window.USER_META['role'] === 'student')
		binaryToggles = {Grades: 'grades', 'Hide my completed': 'pslz_no_cc'};
	else
		binaryToggles = {Grades: 'grades'};
	var sortToggles = {Popularity: 'size', Grades: 'avg_grade', 'Available Seats': 'seats_avail', 'Number': 'number'}
	var courseFilters = {'Seats available': 'seats_avail', 'Upper Division': 'ud', 'Lower Division': 'ld'}
	var courseToggles = [
		{title: 'SORT BY', name: 'sort', toggles: sortToggles, type: 'dropdown'},
		{title: 'TOGGLES', toggles: binaryToggles, type: 'checkbox'},
		{title: 'AREAS', toggles: window.AREAS, type: 'checkbox'},
		{title: 'COURSE FILTERS', toggles: courseFilters, type: 'checkbox'}
	]

	var searchTools=(<common.ToggleBody key = {common.createReactRootIndex()}
						toggles={courseToggles}
						/>);

	var results = window.RESULTS.map((result, index) => {
		var avgGradeString;
		if (result.avg_grade_letter)
			avgGradeString = result.avg_grade_letter;
		else
			avgGradeString = 'tba';

		return (
			<cards.Template key={common.createReactRootIndex()}
							data = {result}
                            className = "column-12"
                            {...result}
                           	datapoints={[`Average grade: ${avgGradeString}`,
                                  `${result.units_frmt} units`, `${result.drop_time} days to drop`]}/>
		)
	});
	var instructors = window.INSTRUCTORS.map((result, index) => {
		return (
			<cards.Template key={common.createReactRootIndex()}
                className = "column-12"
                instructor = {result[1]}
                instructorurl = {result[3]}
                type = {'instructor'}
            />
		)
	});
	var resultsWrapper = (<div className="column-12 card-col">
							{instructors}
							{results}
						</div>);
	ReactDOM.render(searchTools, document.getElementById('searchTools'));
	ReactDOM.render(resultsWrapper, document.getElementById('results_list'));
};
