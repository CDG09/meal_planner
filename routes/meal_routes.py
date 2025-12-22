from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app import db
from models import Meal
from utils.goals import get_daily_goal  # <-- import your helper

meal = Blueprint('meal', __name__)

@meal.route('/add_meal', methods=['GET', 'POST'])
def add_meal():
    """Add a meal and update today's remaining daily goal"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login to add a meal')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        # Get data from form
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            calories = float(request.form.get('calories', 0))
            protein = float(request.form.get('protein', 0))
            fat = float(request.form.get('fat', 0))
            carbs = float(request.form.get('carbs', 0))
        except ValueError:
            flash('Please enter a numeric value')
            return redirect(url_for('meal.add_meal'))

        # Create the meal record
        new_meal = Meal(
            name=name,
            description=description,
            calories=calories,
            protein=protein,
            fat=fat,
            carbs=carbs,
            user_id=user_id
        )
        db.session.add(new_meal)

        # Update today's daily goal
        daily_goal = get_daily_goal(user_id)
        if daily_goal:
            daily_goal.remaining_calories = max(daily_goal.remaining_calories - calories, 0)
            daily_goal.remaining_protein = max(daily_goal.remaining_protein - protein, 0)
            daily_goal.remaining_fat = max(daily_goal.remaining_fat - fat, 0)
            daily_goal.remaining_carbs = max(daily_goal.remaining_carbs - carbs, 0)

        db.session.commit()
        flash('Your meal has been added and today\'s goal updated!')
        return redirect(url_for('meal.my_meals'))

    return render_template('add_meal.html')

@meal.route('/my_meals')
def my_meals():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login to view your meals')
        return redirect(url_for('auth.login'))

    # Fetch current user's meals
    meals = Meal.query.filter_by(user_id=user_id).order_by(Meal.id.desc()).all()
    return render_template('my_meals.html', meals=meals)

@meal.route('/meal/<int:meal_id>/delete', methods=['POST'])
def delete_meal(meal_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login to add a meal')
        return redirect(url_for('auth.login'))

    meal_delete = Meal.query.get_or_404(meal_id)

    if meal_delete.user_id != user_id: # IDOR handling
        flash('You cannot delete this meal')
        return redirect(url_for('meal.my_meals'))

    db.session.delete(meal_delete)
    db.session.commit()
    flash('You have successfully deleted this meal')
    return redirect(url_for('meal.my_meals'))

