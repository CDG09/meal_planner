from flask import Blueprint, render_template, request, redirect, url_for, Flask, flash, session
from models import User
from app import db

auth = Blueprint('auth', __name__)

# Registration
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Require each field to be set
        if not username or not password:
            flash('Please enter both username and password.')
            return redirect(url_for('auth.register'))

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('User {} already exists.'.format(username))
            return redirect(url_for('auth.register'))

        # Create new user
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('User {} created!'.format(username))
        return redirect(url_for('home'))

    return render_template('register.html', active_page='register')

# Login
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password): # Verify hashed password
            session['user_id'] = user.id
            flash('Welcome {}!'.format(user.username))
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.')
            return redirect(url_for('auth.login'))
    return render_template('login.html', active_page='login')

# Logout
@auth.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out')
    return redirect(url_for('home'))