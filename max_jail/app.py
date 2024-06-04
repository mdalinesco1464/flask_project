from flask import Flask, request, jsonify
import time
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

# Configure logging
handler = RotatingFileHandler('login_info.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)  # Change to DEBUG for temporary debugging
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)

# Optional: Add console logging for debugging purposes
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
app.logger.addHandler(console_handler)

# In-memory user data store
users = {
    'user1': {'password': 'password123', 'failed_attempts': 0, 'jail_until': 0}
}

MAX_RETRY = 5
JAIL_TIME = 600  # seconds

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
    app.logger.info("Login endpoint hit")
    data = request.json
    username = data.get('username')
    password = data.get('password')

    try:
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
            handler.flush()
            return jsonify({"message": "Login successful"}), 200
        else:
            increment_failed_attempts(username)
            if user['failed_attempts'] >= MAX_RETRY:
                remaining_time = int(user['jail_until'] - time.time())
                app.logger.info(f"User jailed due to too many failed attempts: {username}, remaining lock time: {remaining_time} seconds")
                handler.flush()
                return jsonify({"error": "Account is temporarily locked. Please try again later.",
                                "remaining_time": remaining_time}), 403
            app.logger.info(f"Failed login attempt for user: {username}")
            handler.flush()
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        app.logger.error(f"Error during login attempt: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/log', methods=['GET'])
def get_log():
    try:
        with open('login_attempts.log', 'r') as log_file:
            log_data = [line for line in log_file if line.strip()]  # Filter empty lines
        if not log_data:
            app.logger.info("Log file is empty")
        else:
            app.logger.info("Log file read successfully")
        return jsonify({"log": log_data}), 200
    except Exception as e:
        app.logger.error(f"Error reading log file: {e}")
        
if __name__ == '__main__':
    app.run(debug=True)
