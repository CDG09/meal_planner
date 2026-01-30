# Used to run cloud function before deploying
from flask import Blueprint, request, jsonify, session
from utils.auth import login_required
from cloud_functions.daily_goal_reset import daily_goal_reset_logic
from cloud_functions.recalc_meal_macros import recalc_meal_macros_logic

dev = Blueprint("dev", __name__, url_prefix="/dev")

@dev.get("/functions/daily-goal-reset")
@login_required
def run_daily_goal_reset():
    user_id = request.args.get("user_id")
    result = daily_goal_reset_logic(user_id=int(user_id) if user_id else None)
    return jsonify(result), 200

@dev.get("/functions/recalc-meal-macros")
@login_required
def run_recalc_meal_macros():
    meal_id = request.args.get("meal_id")
    if not meal_id:
        return jsonify({"error": "meal_id required"}), 400

    result = recalc_meal_macros_logic(int(meal_id))

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result), 200