from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app import db
from models import Meal, MealLog
from datetime import datetime, date
from utils.auth import login_required
from utils.goals import get_daily_goal

meal = Blueprint('meal', __name__)

@meal.route('/add_meal', methods=['GET', 'POST'])
@login_required
def add_meal():
    user_id = session.get('user_id')

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
@login_required
def my_meals():
    user_id = session.get('user_id')

    # Fetch current user's meals
    meals = Meal.query.filter_by(user_id=user_id).order_by(Meal.id.desc()).all()

    return render_template('my_meals.html', meals=meals)

@meal.route('/meal/<int:meal_id>/delete', methods=['POST'])
@login_required
def delete_meal(meal_id):
    user_id = session.get('user_id')

    meal_delete = Meal.query.get_or_404(meal_id)

    # IDOR check: make sure user owns this meal
    if meal_delete.user_id != user_id:
        flash('You cannot delete this meal')
        return redirect(url_for('meal.my_meals'))

    # Add meal's calories/macros back to daily goal
    daily_goal = get_daily_goal(user_id)
    if daily_goal:
        daily_goal.remaining_calories += meal_delete.calories
        daily_goal.remaining_protein += meal_delete.protein
        daily_goal.remaining_fat += meal_delete.fat
        daily_goal.remaining_carbs += meal_delete.carbs

    db.session.delete(meal_delete)
    db.session.commit()
    flash('You have successfully deleted this meal and updated today\'s goal')
    return redirect(url_for('meal.my_meals'))

@meal.route('/meal/<int:meal_id>/log', methods=['POST'])
@login_required
def log_meal(meal_id):
    user_id = session.get('user_id')

    meal_log = Meal.query.get_or_404(meal_id)

    # IDOR protection
    if meal_log.user_id != user_id:
        flash('You cannot log this meal')
        return redirect(url_for('meal.my_meals'))

    if not get_daily_goal(user_id):
        flash('No daily goal found')
        return redirect(url_for('dashboard.view_dashboard'))


    today = date.today()

    # Prevent duplicate logs for same day
    existing_log = MealLog.query.filter_by(
        user_id=user_id,
        meal_id=meal_id,
        date=today
    ).first()

    if existing_log:
        flash('You already logged this meal today')
        return redirect(url_for('meal.my_meals'))

    # Create log entry
    log = MealLog(
        user_id=user_id,
        meal_id=meal_id,
        date=today,
        calories=meal_log.calories,
        protein=meal_log.protein,
        fat=meal_log.fat,
        carbs=meal_log.carbs
    )

    db.session.add(log)

    # Update daily goal
    daily_goal = get_daily_goal(user_id)
    if daily_goal:
        daily_goal.remaining_calories = max(daily_goal.remaining_calories - meal_log.calories, 0)
        daily_goal.remaining_protein = max(daily_goal.remaining_protein - meal_log.protein, 0)
        daily_goal.remaining_fat = max(daily_goal.remaining_fat - meal_log.fat, 0)
        daily_goal.remaining_carbs = max(daily_goal.remaining_carbs - meal_log.carbs, 0)

    db.session.commit()
    flash('Meal logged for today')
    return redirect(url_for('meal.my_meals'))


