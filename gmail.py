import base64
import datetime
from flask import Flask, request, redirect, send_from_directory, abort, jsonify
import google.oauth2.credentials
import google.auth.transport.requests
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import os
from uuid import uuid4
from Redpie.redpie import Redpie


SERVER_URL = os.environ['SERVER_URL']
API_SCOPE = ['https://www.googleapis.com/auth/gmail.readonly']
JSON_FILE = 'oauth_client.json'
REDIRECT_URI = f'{SERVER_URL}/oauth2/callback/'
app = Flask(__name__)
db = Redpie(1, 'redis')


def get_email_body(message):
    new_element = {}
    if 'attachmentId' not in message['payload']['body']:
        if 'parts' not in message['payload']:
            decoded_body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
            new_element[message['payload']['mimeType']] = decoded_body
        else:
            for each in message['payload']['parts']:
                if 'parts' not in each['body']:
                    new_element = get_email_body({'payload': each})
                else:
                    decoded_body = base64.urlsafe_b64decode(each['body']['data']).decode('utf-8')
                    new_element[each['mimeType']] = decoded_body

    return new_element


def do_refresh_token(id):
    auth = db[id]
    credentials = google.oauth2.credentials.Credentials.from_authorized_user_info(auth)
    request = google.auth.transport.requests.Request()
    try:
        credentials.refresh(request)
    except Exception as e:
        print(e)
        return 0

    auth = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'id_token': credentials.id_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes,
        'expiry': datetime.datetime.strftime(credentials.expiry,'%Y-%m-%d %H:%M:%S')
    }
    db[id] = auth
    return auth


@app.route('/oauth2/callback/')
def oauth2_callback():
    state = request.args.get('state', None)
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        JSON_FILE,
        scopes=API_SCOPE,
        state=state)
    flow.redirect_uri = REDIRECT_URI
    flow.fetch_token(authorization_response=request.url.replace('http://', 'https://'))
    credentials = flow.credentials
    auth = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'id_token': credentials.id_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes,
        'expiry': datetime.datetime.strftime(credentials.expiry,'%Y-%m-%d %H:%M:%S')
    }
    id = str(uuid4())
    db[id] = auth
    return id


@app.route('/oauth2')
def oauth2_start():
    new_email = request.args.get('e')
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(JSON_FILE, scopes=API_SCOPE)
    flow.redirect_uri = REDIRECT_URI

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        login_hint=new_email,
        include_granted_scopes='true',
        prompt='consent')
    return redirect(authorization_url)


@app.route('/delete')
def delete_token():
    id = request.args.get('t')
    if id not in db:
        return abort(401)

    del(db[id])
    return 'OK'


@app.route('/get')
def get_last_email():
    id = request.args.get('t')
    search_term = request.args.get('q')
    no_results = int(request.args.get('n', 1))
    if no_results > 10:
        no_results = 10

    if id not in db:
        return abort(401)

    auth = do_refresh_token(id)
    if auth == 0:
        return abort(401)

    credentials = google.oauth2.credentials.Credentials.from_authorized_user_info(auth)
    service = build('gmail', 'v1', credentials=credentials)

    message_list = service.users().messages().list(userId='me', maxResults=no_results, q=search_term).execute()
    message_ids = [m['id'] for m in message_list['messages']]
    messages = []
    for m_id in message_ids:
        message = service.users().messages().get(userId='me', id=m_id).execute()

        new_element = get_email_body(message)
        messages.append(new_element)

    return jsonify(messages)

@app.route('/')
def redirect_to_oauth():
    return redirect('/oauth2')


if __name__ == '__main__':
    app.run('0.0.0.0', 8000, debug=True)
