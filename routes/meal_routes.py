from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from app import db, limiter
from models import Meal, MealLog
from datetime import datetime, date
from utils.auth import login_required
from utils.goals import get_daily_goal
from utils.ingredients import get_ingredient_by_id, calculate_macros_from_ingredients, get_all_ingredients, insert_fatsecret_ingredient
from utils import fatsecret
import json
meal = Blueprint('meal', __name__)

@meal.route('/add_meal', methods=['GET', 'POST'])
@login_required
def add_meal():
    user_id = session.get('user_id')
    ingredients = get_all_ingredients(user_id)  # Fetch existing MongoDB ingredients

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        # Get selected ingredient IDs from hidden input
        ingredients_ids_raw = request.form.get('ingredient_ids', '').strip()
        ingredient_ids = [i for i in ingredients_ids_raw.split(',') if i]

        # If ingredients selected, calculate macros from MongoDB
        if ingredient_ids:
            # Fetch existing ingredients from MongoDB
            ingredient_docs = get_ingredient_by_id(ingredient_ids, user_id)

            # Calculate macros from all selected ingredients
            macros = calculate_macros_from_ingredients(ingredient_docs)
            calories = macros['calories']
            protein = macros['protein']
            fat = macros['fat']
            carbs = macros['carbs']

            # Store MongoDB ingredient IDs in SQL Meal
            ingredient_ids_list = [str(ing["_id"]) for ing in ingredient_docs]

        # If no ingredients selected, use manual macros
        else:
            try:
                calories = float(request.form.get('calories', 0))
                protein = float(request.form.get('protein', 0))
                fat = float(request.form.get('fat', 0))
                carbs = float(request.form.get('carbs', 0))
            except ValueError:
                flash('Please enter numeric values!', 'danger')
                return redirect(url_for('meal.add_meal'))
            ingredient_ids_list = None

        # Create SQL meal record
        new_meal = Meal(
            name=name,
            description=description,
            calories=calories,
            protein=protein,
            fat=fat,
            carbs=carbs,
            ingredients_ids=ingredient_ids_list,
            user_id=user_id
        )
        db.session.add(new_meal)
        db.session.commit()
        flash('Your meal has been added!', 'success')
        return redirect(url_for('meal.my_meals'))

    return render_template('add_meal.html', ingredients=ingredients)



@meal.route('/my_meals')
@login_required
def my_meals():
    user_id = session.get('user_id')
    today = date.today()

    # Fetch current user's meals
    meals = Meal.query.filter_by(user_id=user_id).order_by(Meal.id.desc()).all()

    # Meal already logged
    logged_meal_ids = {log.meal_id for log in MealLog.query.filter_by(user_id=user_id, date=today).all()}

    for meal in meals:
        meal.eaten_today = meal.id in logged_meal_ids

        if meal.ingredients_ids:
            try:
                ingredient_ids = meal.ingredients_ids
                ingredient_docs = get_ingredient_by_id(ingredient_ids, user_id)
                meal.ingredient_names = [ing.get('name') for ing in ingredient_docs]
            except Exception as e:
                meal.ingredient_names = []
        else:
            meal.ingredient_names = []

    # Fetch daily goal for summary
    daily_goal = get_daily_goal(user_id)
    return render_template('my_meals.html', meals=meals, logged_meal_ids=logged_meal_ids,daily_goal=daily_goal)

@meal.route('/meal/<int:meal_id>/delete', methods=['POST'])
@login_required
@limiter.limit("5/minute")
def delete_meal(meal_id):
    user_id = session.get('user_id')

    meal_delete = Meal.query.get_or_404(meal_id)

    # IDOR check: make sure user owns this meal
    if meal_delete.user_id != user_id:
        flash('You cannot delete this meal', 'warning')
        return redirect(url_for('meal.my_meals'))

    # Get daily goal
    daily_goal = get_daily_goal(user_id)

    # Delete logs and restore intake
    logs = MealLog.query.filter_by(meal_id=meal_id, user_id=user_id, date=date.today()).all()

    for log in logs:
        if daily_goal:
            daily_goal.remaining_calories += log.calories
            daily_goal.remaining_protein += log.protein
            daily_goal.remaining_fat += log.fat
            daily_goal.remaining_carbs += log.carbs
        db.session.delete(log)

    db.session.delete(meal_delete)
    db.session.commit()
    flash('You have successfully deleted this meal and updated today\'s goal', 'success')
    return redirect(url_for('meal.my_meals'))

@meal.route('/meal/<int:meal_id>/log', methods=['POST'])
@login_required
@limiter.limit("10/minute")
def log_meal(meal_id):
    user_id = session.get('user_id')

    meal_log = Meal.query.get_or_404(meal_id)

    # IDOR protection
    if meal_log.user_id != user_id:
        flash('You cannot log this meal', 'warning')
        return redirect(url_for('meal.my_meals'))


    today = date.today()
    daily_goal = get_daily_goal(user_id)
    if not daily_goal:
        flash("No daily goal found. Please set one first!", 'warning')
        return redirect(url_for('dashboard.view_dashboard'))

    # Prevent duplicate logs for same day
    existing_log = MealLog.query.filter_by(
        user_id=user_id,
        meal_id=meal_id,
        date=today
    ).first()

    if existing_log:
        flash('You already logged this meal today', 'warning')
        return redirect(url_for('meal.my_meals'))

    # Create log entry
    log_entry = MealLog(
        user_id=user_id,
        meal_id=meal_id,
        date=today,
        calories=meal_log.calories,
        protein=meal_log.protein,
        fat=meal_log.fat,
        carbs=meal_log.carbs
    )

    db.session.add(log_entry)

    # Update daily goal
    daily_goal = get_daily_goal(user_id)
    if daily_goal:
        daily_goal.remaining_calories = max(daily_goal.remaining_calories - meal_log.calories, 0)
        daily_goal.remaining_protein = max(daily_goal.remaining_protein - meal_log.protein, 0)
        daily_goal.remaining_fat = max(daily_goal.remaining_fat - meal_log.fat, 0)
        daily_goal.remaining_carbs = max(daily_goal.remaining_carbs - meal_log.carbs, 0)

    db.session.commit()
    flash('Meal logged for today', 'success')
    return redirect(url_for('meal.my_meals'))

@meal.route('/meal/<int:meal_id>/unlog', methods=['POST'])
@login_required
@limiter.limit("10/minute")
def unlog_meal(meal_id):
    user_id = session.get('user_id')
    today = date.today()

    # Today's log
    log = MealLog.query.filter_by(user_id=user_id, meal_id=meal_id, date=today).first()
    if not log:
        flash('This meal was not logged today', 'success')
        return redirect(url_for('meal.my_meals'))
    daily_goal = get_daily_goal(user_id)
    if daily_goal:
        daily_goal.remaining_calories += log.calories
        daily_goal.remaining_protein += log.protein
        daily_goal.remaining_fat += log.fat
        daily_goal.remaining_carbs += log.carbs

    db.session.delete(log)
    db.session.commit()
    flash('You have successfully unlogged this meal for today', 'success')
    return redirect(url_for('meal.my_meals'))

@meal.route('/search_ingredient', methods=['GET'])
@login_required
@limiter.limit("30/minute")
def search_ingredient():
    user_id = session.get('user_id')
    query = request.args.get('query','').strip()

    if not query:
        return jsonify(results=[])
    results = []
    try:
        search_results = fatsecret.search_foods(query)
        for result in search_results[:5]:
            food_id = result.get('food_id')
            food_name = result.get('food_name')

            if not food_id or not food_name:
                continue

            details = fatsecret.get_food_by_id(food_id)

            mongo_id = insert_fatsecret_ingredient(
                food_id=food_id,
                name=food_name,
                calories=details.get("calories", 0),
                protein=details.get("protein", 0),
                fat=details.get("fat", 0),
                carbs=details.get("carbs", 0),
                user_id=user_id,
            )

            results.append({
                "id": str(mongo_id),
                "name": food_name,
                "calories": details.get("calories", 0),
                "protein": details.get("protein", 0),
                "fat": details.get("fat", 0),
                "carbs": details.get("carbs", 0),
            })

    except Exception as e:
        print("FatSecret search error:", e)
        return jsonify(results=[])

    return jsonify(results=results)

