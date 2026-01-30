from datetime import date
from app import db
from models import DailyGoal, NutritionGoal

def get_or_create_daily_goal(user_id, target_date: date | None = None):
    target_date = target_date or date.today() # Retrieve data or set to today
    daily_goal = DailyGoal.query.filter_by(user_id=user_id, date=target_date).first() # Fetch daily goal to see if there is one

    if daily_goal:
        return daily_goal

    goal = (NutritionGoal.query.filter_by(user_id=user_id).order_by(NutritionGoal.calories.desc()).first()) # Create a goal based on users nutritional goal

    if not goal:
        return None

    daily_goal = DailyGoal(user_id=user_id, goal_id=goal.id, date=target_date,
    remaining_calories=goal.calories,
    remaining_protein=goal.protein,
    remaining_fat=goal.fat,
    remaining_carbs=goal.carbs,
    )

    db.session.add(daily_goal) # Add to SQLAlchemy db
    db.session.commit()
    return daily_goal