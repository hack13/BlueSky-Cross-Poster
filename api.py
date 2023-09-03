from flask import Flask, request, jsonify
from functools import wraps
from dotenv import load_dotenv
import os

app = Flask(__name__)
API_KEY = os.environ.get('API_KEY')

# Load the .env file
load_dotenv()


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

if __name__ == '__main__':
    app.run(debug=True,port=4002)
