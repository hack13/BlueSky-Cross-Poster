from flask import Flask, request, jsonify
from functools import wraps
from dotenv import load_dotenv
from waitress import serve
from crossposter import *
import os

app = Flask(__name__)
API_KEY = os.environ.get('API_KEY')

# Load the .env file
load_dotenv()

# Define api key decorator
def require_api_key(view_func):
    @wraps(view_func)
    def decorated_func(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401
        # Check if the API key is valid
        if api_key != API_KEY:
            return jsonify({'error': 'Invalid API key'}), 403
        # API key is valid, proceed to the route handler
        return view_func(*args, **kwargs)
    return decorated_func

@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'An Application By Hack13', 'developer': 'https://hack13.me'}), 200

# Route for getting a key
@app.route('/api/v1/createKey', methods=['GET'])
@require_api_key
def createKey():
    key = Fernet.generate_key()
    return jsonify({'key': key.decode('utf-8')}), 200

# Route for creating a new user
@app.route('/api/v1/createUser', methods=['POST'])
@require_api_key
def createUserPost():
    atProtoUser = request.form.get('atProtoUser')
    atAppPassword = request.form.get('atAppPassword')
    mastodonToken = request.form.get('mastodonToken')
    mastodonInstance = request.form.get('mastodonInstance')
    resp = createUser(atProtoUser, atAppPassword, mastodonToken, mastodonInstance)
    if resp == 'success':
        return jsonify({'message': 'User created successfully'}), 200
    else:
        return jsonify({'error': resp}), 400
    
# Route for running Mastodon Fetcher
@app.route('/api/v1/runMastoFetcher', methods=['GET'])
@require_api_key
def runMastoFetcher():
    resp = getMastoPosts()
    if resp == 'success':
        return jsonify({'message': 'Mastodon Fetcher ran successfully'}), 200
    else:
        return jsonify({'error': resp}), 400
    
# Route for running atProto Fetcher
@app.route('/api/v1/runAtProtoFetcher', methods=['GET'])
@require_api_key
def runAtProtoFetcher():
    resp = getATPosts()
    if resp == 'success':
        return jsonify({'message': 'atProto Fetcher ran successfully'}), 200
    else:
        return jsonify({'error': resp}), 400
    
# Route for Posting to Mastodon
@app.route('/api/v1/postToMastodon', methods=['GET'])
@require_api_key
def postToMastodon():
    resp = postToMasto()
    if resp == 'success':
        return jsonify({'message': 'Post to Mastodon ran successfully'}), 200
    else:
        return jsonify({'error': resp}), 400
    
# Route for Posting to atProto
@app.route('/api/v1/postToAtProto', methods=['GET'])
@require_api_key
def postToAtProto():
    resp = postToAtproto()
    if resp == 'success':
        return jsonify({'message': 'Post to atProto ran successfully'}), 200
    else:
        return jsonify({'error': resp}), 400

if __name__ == '__main__':
    serve(app, listen=f'*:{os.environ.get("PORT")}')
