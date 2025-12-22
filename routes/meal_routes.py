from flask import flask, Blueprint, render_template, redirect, url_for, flash, request, session
from models import Meal
from app import db

meal = Blueprint('meal', __name__)

@meal.route('/add_meal', methods = ['GET', 'POST'])
def add_meal():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        # Current logged-in user
        user_id = session.get('user_id')

        # Check user is logged in
        if not user_id:
            flash('Please login to add a meal')
            return redirect(url_for('auth.login'))

        # Create a new meal
        new_meal = Meal(name=name, description=description, user_id=user_id)

        # Add and Commit meal to database
        db.session.add(new_meal)
        db.session.commit()
        flash('Your meal has been added!')
        return redirect(url_for('meal.my_meals'))

    return render_template('add_meal.html')
