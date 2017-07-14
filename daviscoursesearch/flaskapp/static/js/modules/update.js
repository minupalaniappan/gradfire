import * as common from 'common'

export function deleteItem (items, id) {
	items = items.filter(item => {
		item['deleted'] = true;
		return (item['id'] !== id)
	});
	return (items);
}

export function fetchAnswerById (answers, id) {
	var answerValue;
	answers.forEach(answer => {
		if (answer['id'] === id) {
			answerValue = answer;
		}
	});
	return (answerValue);
}

export function voteAnswer (user, obj, id) {
	obj.forEach(answer => {
		if (answer['id'] === id) {
			answer['votes']++;
			answer['user_voted'] = true;
			if (user['role'] !== 'student')
				answer['endorsements'].push(user['name']);
		}
	});
	return (obj);
}

export function constructAnswer (user, response, course, id, questionid, timestamp) {
	return (
		{
			answer: response,
			answerer: user.name,
			deleted: false,
			endorsements: [],
			id: id,
			question_id: questionid,
			role: user.role,
			role_desc: user.role_desc,
			timestamp: timestamp,
			url: "",
			user_id: user.id,
			user_voted: false,
			votes: 0,
			major: 'Design',
			is_owner: true
		}
	)
}

export function addItem (arr, obj) {
	if (!Array.isArray(arr))
		arr = [];
	arr.push(obj);
	return (arr);
}

export function mapElementTextToState (type, state, state2) {
    switch (type) {
      case 'reply':
        if (state)
          return 'Replied';
        else if (state2)
          return 'Close';
        else
          return 'Reply';
        break;
      case 'userVoted':
        if (state)
          return 'Voted';
        return 'Vote';
        break;
      case 'isSkipped':
        if (state)
          return 'Skipped';
        return 'Skip';
        break;
      case 'prompt':
        if (state)
          return 'Cancel';
        return 'Ask a question';
      case 'advice':
      	if (state)
      		return 'Close'
      	else if (state && state2)
      		return 'Advice sent!'
      	else
      		return 'Give advice'
      case 'isSaved':
      	if (state)
      		return ("Saved")
      	return ("Save")
      default:
        break;
    }
}


export function determineWordCountClass (wordcount) {
	if (wordcount > 350)
		return ({ color: '#56B68B' });
	else if (wordcount > 150)
		return ({ color: '#4593ED' });
	else if (wordcount > 0)
		return ({ color: '#ED4577' });
	else
		return ({ color: '#595959' });
}

export function fetchTerm (key, terms) {
	var termToReturn;
	terms.forEach(term => {
		if (key == term['term']) {
			termToReturn = term['days'];
			termToReturn.forEach(day => {
				if (!day['meetings'].length)
					termToReturn.splice(termToReturn.indexOf(day), 1);
			})
		}
	});
	return (termToReturn);
}

export function filterQA (content, filterby) {
	if (filterby === 'all')
		return (content);
	content = content.filter(item => {
		return (item['subject'] === filterby);
	});

	return (content);
}

export function sortQA (content, filterby) {
	content = _.sortBy(content, item => {
		switch (filterby) {
			case 'recent':
				return (item['timestamp']);
				break;
			case 'votes':
				return (item['votes']);
				break;
			case 'answers':
				return (item['id']);
				break;
			default:
				break;
		}
	});

	return (content);
}

export function hasCourse (subject, number, content) {
	return ((_.uniq(_.pluck(content, 'subject')))[0] === subject &&
			(_.uniq(_.pluck(content, 'number')))[0] === number)
}

export function fetchInstructorsForGradeDistribution (grades) {
	return (_.uniq(_.pluck(grades, 'instructor')));
}

export function fetchCourses (content) {
	return (_.uniq(_.pluck(content, 'subject')))
}

export function fetchTerms (grades, ins) {
	var instructorTerms = _.where(grades, {instructor : ins});
	var results = _.map(instructorTerms, term => {
	    return _.pick(term, 'pretty_term_month', 'term_month', 'term_year');
	});

	return (results);
}

export function findGradeDistributionData (grades, ins, term, year) {
	var key = {
		instructor: ins,
		term_month: parseInt(term),
		term_year: parseInt(year)
	}
	return(_.findWhere(grades, key));
}



