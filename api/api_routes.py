from flask import Blueprint, jsonify, session, request
from datetime import date, datetime
from utils.auth import login_required
from utils.ingredients import get_all_ingredients, create_ingredient, get_ingredient_by_ids, calculate_macros_from_ingredients, calculate_macros_from_portions
from utils.mongo import get_collection
from utils import fatsecret
from utils.ingredients import insert_fatsecret_ingredient
from pymongo import DESCENDING
from services.goals_service import get_or_create_daily_goal
from services.progress_service import get_progress_history
from models import Meal, MealLog, NutritionGoal
from app import db, csrf, limiter

api = Blueprint('api', __name__, url_prefix='/api') # Sets up api blueprint
csrf.exempt(api) # api doesn't need csrf


# Daily goal fetch
@api.get("/daily-goal/today")
@login_required
def api_get_todays_goal():
    user_id = session.get("user_id")

    goal = get_or_create_daily_goal(user_id)
    if not goal:
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
def api_log_meal(meal_id):
    user_id = session.get("user_id")
    today = date.today()
    meal = Meal.query.get_or_404(meal_id)

    # Check if user owns this meal — defends against IDOR's
    if meal.user_id != user_id:
        return jsonify({"error": "Forbidden"}), 403

    goal = get_or_create_daily_goal(user_id)
    if not goal:
        return jsonify({"error": "No daily goal found. Please create a nutrition goal first."}), 400

    # Skip logging if already done today
    already_logged = MealLog.query.filter_by(user_id=user_id, meal_id=meal_id, date=today).first()
    if already_logged:
        return jsonify({"error": "Meal already logged today"}), 409

    # Create log entry
    log = MealLog(
        user_id=user_id,
        meal_id=meal_id,
        date=today,
        calories=meal.calories,
        protein=meal.protein,
        fat=meal.fat,
        carbs=meal.carbs,
    )
    db.session.add(log)

    # Update goal values
    goal.remaining_calories = max(goal.remaining_calories - meal.calories, 0)
    goal.remaining_protein = max(goal.remaining_protein - meal.protein, 0)
    goal.remaining_fat = max(goal.remaining_fat - meal.fat, 0)
    goal.remaining_carbs = max(goal.remaining_carbs - meal.carbs, 0)

    db.session.commit()

    return jsonify({
        "message": "Meal logged",
        "meal_id": meal_id,
        "date": str(today),
        "remaining": {
            "calories": goal.remaining_calories,
            "protein": goal.remaining_protein,
            "fat": goal.remaining_fat,
            "carbs": goal.remaining_carbs,
        }
    }), 201

@api.get("/ingredients")
@login_required
def api_list_ingredients():
    user_id = session.get("user_id")
    ingredients = get_all_ingredients(user_id)

    # Transforming for JSON response
    return jsonify([
        {
            "id": str(ing["_id"]),
            "name": ing.get("name"),
            "calories": ing.get("calories", 0),
            "protein": ing.get("protein", 0),
            "fat": ing.get("fat", 0),
            "carbs": ing.get("carbs", 0),
            "source": ing.get("source", "manual"),
            "source_id": ing.get("source_id"),
        }
        for ing in ingredients
    ]), 200

@api.post("/ingredients")
@limiter.limit("10/minute")
@login_required
def api_create_manual_ingredient():
    user_id = session.get("user_id")
    data = request.get_json(silent=True) or {}

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

    new_id = create_ingredient(
        name=name,
        calories=calories,
        protein=protein,
        fat=fat,
        carbs=carbs,
        user_id=user_id,
        source="manual"
    )

    return jsonify({"id": str(new_id), "name": name}), 201

@api.get("/meals")
@login_required
def api_list_meals():
    user_id = session.get("user_id")
    meals = Meal.query.filter_by(user_id=user_id).order_by(Meal.id.desc()).all()

    return jsonify([
        {
            "id": m.id,
            "name": m.name,
            "description": m.description,
            "calories": m.calories,
            "protein": m.protein,
            "fat": m.fat,
            "carbs": m.carbs,
            "ingredients_ids": m.ingredients_ids,
        } for m in meals
    ]), 200

@api.get("/meals/<int:meal_id>")
@login_required
def api_get_meal(meal_id):
    user_id = session.get("user_id")
    meal = Meal.query.get_or_404(meal_id)

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
    portions = data.get("ingredients_portions")

    if isinstance(ingredient_ids, list) and ingredient_ids:
        ingredient_docs = get_ingredient_by_ids(ingredient_ids, user_id)
        if not ingredient_docs:
            return jsonify({"error": "No valid ingredients found"}), 400

        if isinstance(portions, list) and portions:
            macros = calculate_macros_from_portions(ingredient_docs, portions)
        else:
            macros = calculate_macros_from_ingredients(ingredient_docs)

        calories = macros["calories"]
        protein = macros["protein"]
        fat = macros["fat"]
        carbs = macros["carbs"]
        ingredients_ids_list = [str(ing["_id"]) for ing in ingredient_docs]
        ingredients_portions_to_store = portions if isinstance(portions, list) and portions else None
    else:
        try:
            calories = float(data.get("calories", 0))
            protein = float(data.get("protein", 0))
            fat = float(data.get("fat", 0))
            carbs = float(data.get("carbs", 0))
        except (TypeError, ValueError):
            return jsonify({"error": "macros must be numeric"}), 400

        ingredients_ids_list = None
        ingredients_portions_to_store = None

    meal = Meal(
        user_id=user_id,
        name=name,
        description=description,
        calories=calories,
        protein=protein,
        fat=fat,
        carbs=carbs,
        ingredients_ids=ingredients_ids_list,
        ingredients_portions=ingredients_portions_to_store,
    )
    db.session.add(meal)
    db.session.commit()

    return jsonify({"id": meal.id, "name": meal.name}), 201

@api.get("/audit")
@login_required
def api_get_audit_logs():
    user_id = session.get("user_id")
    limit = request.args.get("limit", "50")

    try:
        limit = min(max(int(limit), 1), 200)
    except ValueError:
        limit = 50  # fallback default

    col = get_collection("audit_logs")

    results = col.find({"user_id": user_id}).sort("created_at", DESCENDING).limit(limit)
    return jsonify([
        {
            "id": str(doc.get("_id")),
            "event": doc.get("event"),
            "user_id": doc.get("user_id"),
            "meta": doc.get("meta", {}),
            "ip": doc.get("ip"),
            "user_agent": doc.get("user_agent"),
            "created_at": doc.get("created_at"),
        } for doc in results
    ]), 200

@api.get("/progress")
@login_required
def api_progress():
    user_id = session.get("user_id")

    try:
        days = int(request.args.get("days", 14))
    except ValueError:
        days = 14  # default fallback

    data = get_progress_history(user_id, days=days)

    if "error" in data:
        return jsonify({"error": "No nutrition goal found. Create one first."}), 404

    return jsonify(data), 200

# Remove a meal entry and related logs for the day
@api.delete("/meals/<int:meal_id>")
@login_required
@limiter.limit("5/minute")
def api_delete_meal_entry(meal_id):
    uid = session.get("user_id")  # Grab current user ID from session
    meal_entry = Meal.query.get_or_404(meal_id)

    if meal_entry.user_id != uid:
        return jsonify({"error": "Forbidden"}), 403  # Basic ownership check

    today = date.today()
    today_goal = get_or_create_daily_goal(uid)  # note: might return None

    logs_today = MealLog.query.filter_by(meal_id=meal_id, user_id=uid, date=today).all()
    for log in logs_today:
        # Adjust daily goal macros if applicable
        if today_goal:
            today_goal.remaining_calories += log.calories
            today_goal.remaining_protein += log.protein
            today_goal.remaining_fat += log.fat
            today_goal.remaining_carbs += log.carbs

        db.session.delete(log)  # Removing meal log

    db.session.delete(meal_entry)  # Finally delete the meal itself
    db.session.commit()  # Save all changes to DB

    return jsonify({"message": "Meal deleted", "meal_id": meal_id}), 200


# Remove just today's log for a meal, without deleting the meal entirely
@api.post("/meals/<int:meal_id>/unlog")
@login_required
@limiter.limit("10/minute")
def unlog_meal_today(meal_id):
    uid = session.get("user_id")
    today = date.today()

    # Only one log per day per meal
    log_entry = MealLog.query.filter_by(user_id=uid, meal_id=meal_id, date=today).first()
    if not log_entry:
        return jsonify({"error": "Meal not logged today"}), 404


    goal = get_or_create_daily_goal(uid)
    if goal:
        # Restore the macros from the unlogged meal
        goal.remaining_calories += log_entry.calories
        goal.remaining_protein += log_entry.protein
        goal.remaining_fat += log_entry.fat
        goal.remaining_carbs += log_entry.carbs

    db.session.delete(log_entry)
    db.session.commit()

    return jsonify({
        "message": "Meal unlogged",
        "meal_id": meal_id,
        "date": str(today)
    }), 200


# Ingredient search endpoint
@api.get("/ingredients/search")
@login_required
@limiter.limit("30/minute")
def search_ingredient():
    user_id = session.get("user_id")
    query = (request.args.get("query") or "").strip()

    if not query:
        return jsonify(results=[]), 200

    results = []
    try:
        search_results = fatsecret.search_foods(query)

        for result in (search_results or [])[:5]:
            food_id = result.get("food_id")
            food_name = result.get("food_name")
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
                metric_serving_amount=details.get("metric_serving_amount"),
                serving_amount_unit=details.get("serving_amount_unit"),
                serving_grams=details.get("serving_grams"),
                user_id=user_id,
            )

            results.append({
                "id": str(mongo_id),
                "name": food_name,
                "calories": details.get("calories", 0),
                "protein": details.get("protein", 0),
                "fat": details.get("fat", 0),
                "carbs": details.get("carbs", 0),
                "serving_grams": details.get("serving_grams"),
            })

    except Exception as e:
        print("FatSecret search error:", e)
        return jsonify(results=[]), 200

    return jsonify(results=results), 200

# ----------------------------
# Goals API
# ----------------------------

@api.post("/goals")
@login_required
@limiter.limit("10/minute")
def api_create_goal():
    user_id = session.get("user_id")
    data = request.get_json(silent=True) or {}

    try:
        goal = NutritionGoal(
            user_id=user_id,
            weight_kg=float(data["weight"]),
            height_cm=float(data["height"]),
            age=int(data["age"]),
            sex=str(data["sex"]),
            activity_level=str(data["activity_level"]),
            goal_percent=float(data.get("goal_percent", 0)),
            created_at=datetime.now(),
        )
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Invalid goal data"}), 400

    goal.calculate_goal()
    db.session.add(goal)
    db.session.commit()

    return jsonify({"message": "Goal created", "goal_id": goal.id}), 201


@api.patch("/goals/<int:goal_id>")
@login_required
@limiter.limit("10/minute")
def api_update_goal(goal_id: int):
    user_id = session.get("user_id")
    data = request.get_json(silent=True) or {}

    original_goal = NutritionGoal.query.get_or_404(goal_id)

    # IDOR protection
    if original_goal.user_id != user_id:
        return jsonify({"error": "Forbidden"}), 403

    # Parse values
    try:
        weight = float(data["weight"])
        height = float(data["height"])
        age = int(data["age"])
        goal_percent = float(data.get("goal_percent", original_goal.goal_percent))
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Invalid goal data"}), 400


    if weight != original_goal.weight_kg or height != original_goal.height_cm or age != original_goal.age:
        new_snapshot = NutritionGoal(
            user_id=user_id,
            weight_kg=weight,
            height_cm=height,
            age=age,
            sex=original_goal.sex,
            activity_level=original_goal.activity_level,
            goal_percent=goal_percent,
            created_at=datetime.now(),
        )
        new_snapshot.calculate_goal()
        db.session.add(new_snapshot)
        db.session.commit()
        return jsonify({"message": "Goal updated (new snapshot)", "goal_id": new_snapshot.id}), 200

    if goal_percent != original_goal.goal_percent:
        original_goal.goal_percent = goal_percent
        original_goal.calculate_goal()
        db.session.commit()
        return jsonify({"message": "Goal updated", "goal_id": original_goal.id}), 200

    return jsonify({"message": "No changes made", "goal_id": original_goal.id}), 200


@api.delete("/goals/<int:goal_id>")
@login_required
@limiter.limit("10/minute")
def api_delete_goal(goal_id: int):
    user_id = session.get("user_id")
    goal = NutritionGoal.query.get_or_404(goal_id)

    if goal.user_id != user_id:
        return jsonify({"error": "Forbidden"}), 403

    db.session.delete(goal)
    db.session.commit()
    return jsonify({"message": "Goal deleted", "goal_id": goal_id}), 200


@api.delete("/goals/history")
@login_required
@limiter.limit("5/minute")
def api_delete_goal_history():
    user_id = session.get("user_id")
    goals = NutritionGoal.query.filter_by(user_id=user_id).all()

    if not goals:
        return jsonify({"message": "No goal history to delete"}), 200

    for g in goals:
        db.session.delete(g)
    db.session.commit()

    return jsonify({"message": "Goal history deleted", "deleted": len(goals)}), 200

