import {User} from 'api';

function loadProfilePage() {
    window.location = '/profile'
}

export function onSignIn(googleUser) {
  const id_token = googleUser.getAuthResponse().id_token;
  const profile = googleUser.getBasicProfile();
  User.login(profile.getEmail(), id_token, loadProfilePage);
}