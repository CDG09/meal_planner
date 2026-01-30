from flask import jsonify
from app import create_app, db
from utils.ingredients import get_ingredient_by_id, calculate_macros_from_ingredients

def recalc_meal_macros_logic(meal_id):
    app = create_app()
    with app.app_context():
        from models import Meal

    meal = Meal.query.get(int(meal_id))
    if not meal:
        return {"error": "meal not found", "meal_id": meal_id}

    if not meal.ingredients_ids:
        return {"error": "meal has no ingredients_ids", "meal_id": meal_id}

    ingredient_docs = get_ingredient_by_id(meal.ingredients_ids, meal.user_id)
    if not ingredient_docs:
        return {"error": "no valid ingredients found for this meal", "meal_id": meal_id}

    macros = calculate_macros_from_ingredients(ingredient_docs)

    meal.calories = macros["calories"]
    meal.protein = macros["protein"]
    meal.fat = macros["fat"]
    meal.carbs = macros["carbs"]

    db.session.commit()

    return {"message": "updated", "meal_id": meal.id, "macros": macros}

# Cloud function
def recalc_meal_macros(request):
    meal_id = request.args.get('meal_id')
    if not meal_id:
        return jsonify({"error": "meal id required"}), 400

    result = recalc_meal_macros_logic(int(meal_id))

    if "error" in result:
        if result["error"] == "meal not found":
            return jsonify(result), 404
        return jsonify(result), 400

    return jsonify(result), 200