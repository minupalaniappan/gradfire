import * as common from 'common'
import * as graph from 'graph'
import * as profnote from 'profnote'
import * as infiniteload from 'infiniteload'
import * as constants from 'constants'
import * as profile  from 'profile'
import * as results from 'results'
import * as course from 'course'
import * as instructor from 'instructor'
import * as signup from 'modules/signup'
import * as block from 'modules/block'
import * as user_settings from 'user_settings'
import * as update from 'modules/update'
import * as cards from 'modules/cards'
import * as onboard from 'modules/onboard'
import * as index from 'modules/index'
import * as header from 'modules/header'
import {onSignIn, googleApiInit} from 'modules/init'

var initByPage = {
  'profile': profile._init,
  'results': results._init,
  'course': course._init,
  'instructor': instructor._init,
  'signup': signup._init,
  'user_settings': user_settings._init,
  'onboard': onboard._init,
  'index': index._init
};

var start = function() {
    header.headerDriver();
    var active_page = document.body.dataset.page;
    initByPage[active_page]();
}

if(typeof $ != 'undefined') {
  $(document).ready(start);
}
else {
  window.onload = start;
}



