import * as common from 'common'
import * as update from 'update'
import { GenericBlock } from 'block'
import { Questions, Courses, Advice, User } from 'api'
import * as cards from 'cards'
import * as header from 'header'

export function _init() {
	switch(window.USER_META['role']) {
		case 'student':
			header.studentDriver();
			break;
		default:
			break;
	}
}