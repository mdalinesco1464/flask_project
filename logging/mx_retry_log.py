from flask import Flask, request, jsonify
import time
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)


# Configure logging (using the first part as base)
app.logger.setLevel(logging.INFO)  # Set the logging level (e.g., DEBUG, INFO, WARNING)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('app_mx_retry.log')  # Log to file
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)

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
    app.logger.info("A user accessed the home page")

    return "Welcome to the Flask application!"

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = users.get(username)

    if not user:
        app.logger.info(f"Login attempt for non-existent user: {username}")
        return jsonify({"error": "User not found"}), 404

    if user['jail_until'] > time.time():
        remaining_time = int(user['jail_until'] - time.time())
        app.logger.info(f"Login attempt for jailed user: {username}, remaining lock time: {remaining_time} seconds")
        return jsonify({"error": "Account is temporarily locked. Please try again later.",
                        "remaining_time": remaining_time}), 403

    if authenticate(username, password):
        reset_failed_attempts(username)
        app.logger.info(f"Successful login for user: {username}")
        return jsonify({"message": "Login successful"}), 200
    else:
        increment_failed_attempts(username)
        if user['failed_attempts'] >= MAX_RETRY:
            remaining_time = int(user['jail_until'] - time.time())
            app.logger.info(f"User jailed due to too many failed attempts: {username}, remaining lock time: {remaining_time} seconds")
            return jsonify({"error": "Account is temporarily locked. Please try again later.",
                            "remaining_time": remaining_time}), 403
        app.logger.info(f"Failed login attempt for user: {username}")
        return jsonify({"error": "Invalid credentials"}), 401

"""@app.route('/log', methods=['GET'])
def get_log():
    try:
        with open('app_mx_retry.log', 'r') as log_file:
            log_data = [line for line in log_file if line.strip()]  # Filter empty lines
        if not log_data:
            app.logger.info("Log file is empty")
        else:
            app.logger.info("Log file read successfully")
        return jsonify({"log": log_data}), 200
    except Exception as e:
        app.logger.error(f"Error reading log file: {e}")"""
        
if __name__ == '__main__':
    app.run(debug=True)
