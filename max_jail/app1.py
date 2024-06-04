from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# In-memory user data store
users = {
    'user1': {'password': 'password123', 'failed_attempts': 0, 'jail_until': 0},
    'user2': {'password': 'password456', 'failed_attempts': 0, 'jail_until': 0},
    'user3': {'password': 'password789', 'failed_attempts': 0, 'jail_until': 0}


}

MAX_RETRY = 3
JAIL_TIME = 120  # seconds

def authenticate(username, password):
    user = users.get(username)
    if user and user['password'] == password:
        return True
    return False

def reset_failed_attempts(username):
    users[username]['failed_attempts'] = 0
    users[username]['jail_until'] = 0

def increment_failed_attempts(username):
    user = users[username]
    user['failed_attempts'] += 1
    if user['failed_attempts'] >= MAX_RETRY:
        user['jail_until'] = time.time() + JAIL_TIME

@app.route('/')
def index():
    return "Welcome to the Flask application!"

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = users.get(username)

    if not user:
        return jsonify({"error": "User not found"}), 404

    if user['jail_until'] > time.time():
        return jsonify({"error": "Account is temporarily locked. Please try again later."}), 403

    if authenticate(username, password):
        reset_failed_attempts(username)
        return jsonify({"message": "Login successful"}), 200
    else:
        increment_failed_attempts(username)
        return jsonify({"error": "Invalid credentials"}), 401

if __name__ == '__main__':
    app.run(debug=True)
