from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_required, login_user, current_user, logout_user
import secrets
import logging
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)  # Generate a random 32-character string
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure logging
app.logger.setLevel(logging.INFO)  # Set the logging level (e.g., DEBUG, INFO, WARNING)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('app.log')  # Log to file
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

MAX_RETRY = 2
JAIL_TIME = 120  # seconds

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)  # Add email field
    password = db.Column(db.String(100), nullable=False)
    failed_attempts = db.Column(db.Integer, default=0)
    jail_until = db.Column(db.DateTime, default=None)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']  # Retrieve email from the form
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()  # Check if email already exists
        if existing_user:
            flash('Username already exists!', 'error')
        elif existing_email:  # If email already exists, prevent registration
            flash('Email already exists!', 'error')
        else:
            new_user = User(username=username, email=email, password=password)  # Include email when creating new user
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            app.logger.info(f"Created a new account with username: {username}")
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if not user:
            flash('Invalid username or password!', 'error')
            app.logger.info(f"Login attempt for non-existent user: {username}")
            return redirect(url_for('login'))

        if user.jail_until and user.jail_until > datetime.utcnow():
            flash('Account is temporarily locked. Please try again later.', 'error')
            app.logger.info(f"Locked account login attempt: {username}")
            return render_template('locked.html')

        if user.password == password:
            user.failed_attempts = 0
            user.jail_until = None
            db.session.commit()
            login_user(user)
            app.logger.info(f"Successful login for user: {username}")
            return redirect(url_for('profile'))
        else:
            user.failed_attempts += 1
            if user.failed_attempts >= MAX_RETRY:
                user.jail_until = datetime.utcnow() + timedelta(seconds=JAIL_TIME)
            db.session.commit()  # Make sure to commit the changes to the database
            flash('Invalid username or password!', 'error')
            app.logger.info(f"Failed login attempt for user: {username}")
    return render_template('login.html')



@app.route('/locked')
def locked():
    app.logger.info("A user account locked page visit")
    return render_template('locked.html', username=current_user.username)
    return redirect(url_for("login"))


@app.route('/profile')
@login_required
def profile():
    app.logger.info("A user accessed the profile page")
    return render_template('profile.html', username=current_user.username)

@app.route('/logout')
@login_required
def logout():
    username = session.get('username')  # Assuming username is stored in session
    app.logger.info(f"Successful logout for user: {username}")
    
    session.pop('username', None)  # Remove username from session
    logout_user()  # Add this line to log out the user using Flask-Login

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
