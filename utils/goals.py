from datetime import date
from models import DailyGoal, NutritionGoal
from app import db


def get_daily_goal(user_id):
    """Return today's DailyGoal or create it from the latest NutritionGoal"""

    today = date.today()

    # Check if today's daily goal already exists
    daily_goal = DailyGoal.query.filter_by(user_id=user_id,date=today).first()

    if daily_goal:
        return daily_goal

    # Find the user's latest Goal
    goal = (
        NutritionGoal.query.filter_by(user_id=user_id).order_by(NutritionGoal.created_at.desc()).first()
    )

    if not goal:
        return None  # user has no goals yet

    # Create today's DailyGoal from that snapshot
    daily_goal = DailyGoal(
        user_id=user_id,
        goal_id=goal.id,
        date=today,
        remaining_calories=goal.calories,
        remaining_protein=goal.protein,
        remaining_fat=goal.fat,
        remaining_carbs=goal.carbs
    )

    db.session.add(daily_goal)
    db.session.commit()

    return daily_goal

