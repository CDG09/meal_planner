from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app import db
from models import Meal
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

@meal.route('/meal/<int:meal_id>/toggle', methods=['POST'])
@login_required
def toggle_meal(meal_id):
    user_id = session.get('user_id')

    meal_obj = Meal.query.get_or_404(meal_id)
    if meal_obj.user_id != user_id:  # IDOR protection
        flash('You cannot modify this meal')
        return redirect(url_for('meal.my_meals'))

    daily_goal = get_daily_goal(user_id)
    if not daily_goal:
        flash('Daily goal not found')
        return redirect(url_for('meal.my_meals'))

    # Toggle eaten state
    if meal_obj.eaten_today:
        # Unmark: add back macros to daily goal
        daily_goal.remaining_calories += meal_obj.calories
        daily_goal.remaining_protein += meal_obj.protein
        daily_goal.remaining_fat += meal_obj.fat
        daily_goal.remaining_carbs += meal_obj.carbs
        meal_obj.eaten_today = False
    else:
        # Mark as eaten: subtract macros from daily goal
        daily_goal.remaining_calories = max(daily_goal.remaining_calories - meal_obj.calories, 0)
        daily_goal.remaining_protein = max(daily_goal.remaining_protein - meal_obj.protein, 0)
        daily_goal.remaining_fat = max(daily_goal.remaining_fat - meal_obj.fat, 0)
        daily_goal.remaining_carbs = max(daily_goal.remaining_carbs - meal_obj.carbs, 0)
        meal_obj.eaten_today = True

    db.session.commit()
    return redirect(url_for('meal.my_meals'))

