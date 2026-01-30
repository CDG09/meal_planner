from flask import jsonify
from app import app, db
from models import Meal
from utils.ingredients import get_ingredient_by_id, calculate_macros_from_ingredients

def recalc_meal_macros(request):
    meal_id = request.args.get("meal_id")
    if not meal_id:
        return jsonify({"error": "meal_id required"}), 400

    # Ensure SQLAlchemy has application context available
    with app.app_context():
        meal = Meal.query.get(int(meal_id))
        if not meal:
            return jsonify({"error": "meal not found"}), 404

        if not meal.ingredients_ids:
            return jsonify({"error": "meal has no ingredients_ids"}), 400

        ingredient_docs = get_ingredient_by_id(meal.ingredients_ids, meal.user_id)
        macros = calculate_macros_from_ingredients(ingredient_docs)

        meal.calories = macros["calories"]
        meal.protein = macros["protein"]
        meal.fat = macros["fat"]
        meal.carbs = macros["carbs"]

        db.session.commit()

        return jsonify({"message": "updated", "meal_id": meal.id, "macros": macros}), 200
