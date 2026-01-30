# Used to run cloud function before deploying
from flask import Blueprint, request
from utils.auth import login_required
from cloud_functions.daily_goal_reset import daily_goal_reset
from cloud_functions.recalc_meal_macros import recalc_meal_macros

dev = Blueprint("dev", __name__, url_prefix="/dev")

@dev.get("/functions/daily-goal-reset")
@login_required
def run_daily_goal_reset():
    return daily_goal_reset(request)

@dev.get("/functions/recalc-meal-macros")
@login_required
def run_recalc_meal_macros():
    return recalc_meal_macros(request)