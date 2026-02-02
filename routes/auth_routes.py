from flask import Blueprint, render_template, request, redirect, url_for, Flask, flash, session
from models import User
from app import db, limiter
from utils.audit import log_event

auth = Blueprint('auth', __name__)

# Registration
@auth.route('/register', methods=['GET', 'POST'])
@limiter.limit("5/minute")
def register():
    if request.method == 'POST':
        username = request.form['username'].strip().lower()
        password = request.form['password']

        # Require each field to be set
        if not username or not password:
            flash('Please enter both username and password.', 'warning')
            return redirect(url_for('auth.register'))

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('User {} already exists.'.format(username), 'danger')
            return redirect(url_for('auth.register'))

        # Create new user
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('User {} created!'.format(username), 'success')
        return redirect(url_for('home'))

    return render_template('register.html', active_page='register')

# Login
@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit("10/minute")
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip().lower()
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password): # Verify hashed password
            session.clear() # Clear any previous session data
            session['user_id'] = user.id
            log_event(event="LOGIN_SUCCESS", user_id=user.id, request=request, meta={"username": username})
            session.permanent = True
            flash('Welcome {}!'.format(user.username), 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'danger')
            log_event(event="LOGIN_FAILED", user_id=None, request=request, meta={"username": username})
            return redirect(url_for('auth.login'))
    return render_template('login.html', active_page='login')

# Logout
@auth.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    log_event(event="LOGOUT", user_id=session.get("user_id"), request=request)
    return redirect(url_for('home'))