from ...common.config import GOOGLE_OAUTH_CLIENT_ID
import requests
import json
TOKEN_INFO_URL_FRMT = 'https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={}'
def get_token_info(id_token):
    url = TOKEN_INFO_URL_FRMT.format(id_token)
    resp = requests.get(url)
    return json.loads(resp.text)

def is_google_token_valid(token_info):
    # https://developers.google.com/identity/sign-in/web/backend-auth

    client_id_matches = (token_info['aud'] == GOOGLE_OAUTH_CLIENT_ID)
    return (not token_info.get('error_description')) and token_info.get('email', '').endswith('@ucdavis.edu')

