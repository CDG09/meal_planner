from flask import Blueprint, jsonify, session, request, current_app
from datetime import date
from utils.auth import login_required
from utils.ingredients import get_all_ingredients, create_ingredient, get_ingredient_by_id, calculate_macros_from_ingredients
from utils.audit import _get_audit_collection
from pymongo import DESCENDING
from services.goals_service import get_or_create_daily_goal
from services.progress_service import get_progress_history
from models import Meal, MealLog
from app import db, csrf, limiter



api = Blueprint('api', __name__, url_prefix='/api') # Creates API blueprint to be separated from HTML routes
csrf.exempt(api)

@api.before_request
def api_auth_guard():
    token = request.headers.get("X-API-Token", "").strip()
    expected = (current_app.config.get("API_TOKEN") or "").strip()
    if not expected:
        return jsonify({"error": "API token not configured"}), 500
    if token != expected:
        return jsonify({"error": "Unauthorized"}), 401

# Ingredient routes
@api.get("/daily-goal/today")
@login_required
def api_daily_goal_today():
    user_id = session.get("user_id")

    goal = get_or_create_daily_goal(user_id)
    if not goal:
        # no goal exists for this user yet
        return jsonify({"error": "No nutrition goal found. Create one first."}), 404

    # Convert values to JSON-friendly format
    return jsonify({
        "date": str(goal.date),
        "user_id": goal.user_id,
        "goal_id": goal.goal_id,
        "remaining": {
            "calories": goal.remaining_calories,
            "protein": goal.remaining_protein,
            "fat": goal.remaining_fat,
            "carbs": goal.remaining_carbs,
        }
    }), 200

@api.post("/meals/<int:meal_id>/log")
@login_required
@limiter.limit("15/minute")
def api_log_meal(meal_id: int):
    user_id = session.get("user_id")
    today = date.today()
    meal = Meal.query.get_or_404(meal_id) # Get the meal

    #IDOR protection
    if meal.user_id != user_id:
        return jsonify({"error": "Forbidden"}), 403

    daily_goal = get_or_create_daily_goal(user_id)
    if not daily_goal:
        return jsonify({"error": "No daily goal found. Please create a nutrition goal first."}), 400

    # Prevent duplicate logging
    existing = MealLog.query.filter_by(user_id=user_id, meal_id=meal_id, date=today).first()
    if existing:
        return jsonify({"error": "Meal already logged today"}), 409

    # Create log entry
    log_entry = MealLog(
        user_id=user_id,
        meal_id=meal_id,
        date=today,
        calories=meal.calories,
        protein=meal.protein,
        fat=meal.fat,
        carbs=meal.carbs,
    )

    db.session.add(log_entry)

    # Update goal values
    daily_goal.remaining_calories = max(daily_goal.remaining_calories - meal.calories, 0)
    daily_goal.remaining_protein = max(daily_goal.remaining_protein - meal.protein, 0)
    daily_goal.remaining_fat = max(daily_goal.remaining_fat - meal.fat, 0)
    daily_goal.remaining_carbs = max(daily_goal.remaining_carbs - meal.carbs, 0)

    db.session.commit()

    return jsonify({
        "message": "Meal logged",
        "meal_id": meal_id,
        "date": str(today),
        "remaining": {
            "calories": daily_goal.remaining_calories,
            "protein": daily_goal.remaining_protein,
            "fat": daily_goal.remaining_fat,
            "carbs": daily_goal.remaining_carbs,
        }
    }), 201

@api.get("/ingredients")
@login_required
def api_list_ingredients(): # Returns all ingredients for the current user
    user_id = session.get("user_id")
    ingredients = get_all_ingredients(user_id)

    out = []
    for ing in ingredients:
        out.append({
            "id": str(ing["_id"]),  # convert ObjectId to string
            "name": ing.get("name"),
            "calories": ing.get("calories", 0),
            "protein": ing.get("protein", 0),
            "fat": ing.get("fat", 0),
            "carbs": ing.get("carbs", 0),
            "source": ing.get("source", "manual"),  # manual vs fatsecret
            "source_id": ing.get("source_id"),  # fatsecret food_id if applicable
        })


    return jsonify(out), 200

@api.post("/ingredients")
@limiter.limit("10/minute")
@login_required
def api_create_manual_ingredient():  # Creates a manual ingredient in MongoDB
    user_id = session.get("user_id")
    data = request.get_json(silent=True) or {} # Returns None if there isn't valid JSON

    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400

    try:
        calories = float(data.get("calories", 0))
        protein = float(data.get("protein", 0))
        fat = float(data.get("fat", 0))
        carbs = float(data.get("carbs", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "macros must be numeric"}), 400

    mongo_id = create_ingredient(
        name=name,
        calories=calories,
        protein=protein,
        fat=fat,
        carbs=carbs,
        user_id=user_id,
        source="manual"
    )
    return jsonify({"id": str(mongo_id), "name": name}), 201

# Meal routes
@api.get("/meals")
@login_required
def api_list_meals():
    user_id = session.get("user_id")
    meals = Meal.query.filter_by(user_id=user_id).order_by(Meal.id.desc()).all()

    # Convert SQLAlchemy -> JSON
    return jsonify([{
        "id": m.id,
        "name": m.name,
        "description": m.description,
        "calories": m.calories,
        "protein": m.protein,
        "fat": m.fat,
        "carbs": m.carbs,
        "ingredients_ids": m.ingredients_ids,
    } for m in meals]), 200

@api.get("/meals/<int:meal_id>")
@login_required
def api_get_meal(meal_id: int):
    user_id = session.get("user_id")
    meal = Meal.query.get_or_404(meal_id)

    # IDOR protection
    if meal.user_id != user_id:
        return jsonify({"error": "Forbidden"}), 403

    return jsonify({
        "id": meal.id,
        "name": meal.name,
        "description": meal.description,
        "calories": meal.calories,
        "protein": meal.protein,
        "fat": meal.fat,
        "carbs": meal.carbs,
        "ingredients_ids": meal.ingredients_ids,
    }), 200

@api.post("/meals")
@login_required
@limiter.limit("10/minute")
def api_create_meal():
    user_id = session.get("user_id")
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()

    if not name:
        return jsonify({"error": "name is required"}), 400

    ingredient_ids = data.get("ingredient_ids")

    # Computed Macros

    if isinstance(ingredient_ids, list) and ingredient_ids:
        ingredient_docs = get_ingredient_by_id(ingredient_ids, user_id) # Fetch ingredients from MongoDB

        if not ingredient_docs:
            return jsonify({"error": "No valid ingredients found"}), 400

        macros = calculate_macros_from_ingredients(ingredient_docs) # Compute totals

        calories = macros["calories"]
        protein = macros["protein"]
        fat = macros["fat"]
        carbs = macros["carbs"]

        ingredients_ids_list = [str(ing["_id"]) for ing in ingredient_docs] # Update Mongo IDs in SQL db
    else:
        try:
            calories = float(data.get("calories", 0))
            protein = float(data.get("protein", 0))
            fat = float(data.get("fat", 0))
            carbs = float(data.get("carbs", 0))
        except (TypeError, ValueError):
            return jsonify({"error": "macros must be numeric"}), 400
        ingredients_ids_list = None

    # Create SQL meal row
    meal = Meal(
        user_id=user_id,
        name=name,
        description=description,
        calories=calories,
        protein=protein,
        fat=fat,
        carbs=carbs,
        ingredients_ids=ingredients_ids_list,
        )

    db.session.add(meal)
    db.session.commit()

    return jsonify({"id": meal.id, "name": meal.name}), 201

# Audit endpoints
@api.get("/audit")
@login_required
def api_get_audit_logs():
    user_id = session.get("user_id")
    limit = request.args.get("limit", "50")
    try:
        limit = min(max(int(limit), 1), 200)
    except ValueError:
        limit = 50

    col = _get_audit_collection()

    cursor = col.find({"user_id": user_id}).sort("created_at", DESCENDING).limit(limit)

    out = []
    for doc in cursor:
        out.append({
            "id": str(doc.get("_id")),
            "event": doc.get("event"),
            "user_id": doc.get("user_id"),
            "meta": doc.get("meta", {}),
            "ip": doc.get("ip"),
            "user_agent": doc.get("user_agent"),
            "created_at": doc.get("created_at"),
        })

    return jsonify(out), 200

from services.progress_service import get_progress_history

@api.get("/progress")
@login_required
def api_progress():
    user_id = session.get("user_id")

    try:
        days = int(request.args.get("days", 14))
    except ValueError:
        days = 14

    data = get_progress_history(user_id, days=days)

    if "error" in data:
        return jsonify({"error": "No nutrition goal found. Create one first."}), 404

    return jsonify(data), 200
