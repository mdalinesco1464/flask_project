from flask import Flask, request, jsonify
import logging

app = Flask(__name__)

# Configure logging
app.logger.setLevel(logging.INFO)  # Set the logging level (e.g., DEBUG, INFO, WARNING)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()  # Log to console
handler.setFormatter(formatter)
app.logger.addHandler(handler)

# Sample route
@app.route('/')
def index():
    app.logger.info("A user accessed the home page")
    return "Welcome to the Flask application!"

if __name__ == '__main__':
    app.run(debug=True)
