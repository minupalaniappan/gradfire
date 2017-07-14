
// Google settings
window.__gcfg = {
  lang: 'en-US',
  parsetags: 'onload'
};

function signOut(event) {
  event.preventDefault()
  gapi.auth2.getAuthInstance().signOut().then(function() {
    window.location = '/logout';
  });
}
function redirectToOnboard() {
    window.location = '/onboard'
}

function sendSignIn(email, id_token, callback) {
  var formData = new FormData();
  formData.append('email', email);
  formData.append('id_token', id_token);

  var xhr = new XMLHttpRequest();
  xhr.addEventListener("load", callback);
  xhr.open('POST', '/api/web/login');
  xhr.send(formData);
}

window.GAuth = {
  onSignIn: function(googleUser) {
    var id_token = googleUser.getAuthResponse().id_token;
    var profile = googleUser.getBasicProfile();
    if(referringUrl == null) {
      sendSignIn(profile.getEmail(), id_token, redirectToOnboard);
    }
    else {
      sendSignIn(profile.getEmail(), id_token, function() {
        window.location = referringUrl;
      });
    }
  }
}
// platform.js?onload=googleApiInit
function googleApiInit() {
  var params = {
      client_id: '1075641739653-20ki5bp29jhremd95dl13jhgf6lpimdj.apps.googleusercontent.com',
      fetch_basic_profile: true,
      scope: 'profile email',
      hosted_domain: 'ucdavis.edu',
      cookiepolicy: 'single_host_origin'
  };
  var signinButtons = Array.prototype.slice.call(document.getElementsByClassName('customGoogleSignin'));
  gapi.load('auth2', function() {
    window.gapi_auth2 = gapi.auth2.init(params)
    window.gapi_auth2.then(function() {
      for(var i = 0; i < signinButtons.length; i++) {
        window.gapi_auth2.attachClickHandler(signinButtons[i],
          {},
          window.GAuth.onSignIn,
          console.log.bind(null, 'fail'));

      }
    });
  });

  var signoutButtons = Array.prototype.slice.call(document.getElementsByClassName('logout'));
  for(var i = 0; i < signoutButtons.length; i++) {
    var signoutBtn = signoutButtons[i];
    signoutBtn.addEventListener('click', signOut);
  }
}
