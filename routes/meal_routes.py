from flask import Blueprint, render_template, session
from datetime import date
from models import Meal, MealLog
from utils.auth import login_required
from utils.goals import get_daily_goal
from utils.ingredients import get_ingredient_by_ids

meal = Blueprint("meal", __name__)

@meal.route("/add_meal", methods=["GET"])
@login_required
def add_meal():
    return render_template("add_meal.html")

@meal.route("/my_meals", methods=["GET"])
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
                ingredient_docs = get_ingredient_by_ids(ingredient_ids, user_id)
                meal.ingredient_names = [ing.get('name') for ing in ingredient_docs]
            except Exception as e:
                meal.ingredient_names = []
        else:
            meal.ingredient_names = []

    # Fetch daily goal for summary
    daily_goal = get_daily_goal(user_id)
    return render_template('my_meals.html', meals=meals, logged_meal_ids=logged_meal_ids,daily_goal=daily_goal)