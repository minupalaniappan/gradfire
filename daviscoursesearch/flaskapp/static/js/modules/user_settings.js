import {MajorSelect} from 'onboard'

export var _init = function () {
    ReactDOM.render(<MajorSelect user={window.USER_META}/>, document.getElementById('major_update'));
}