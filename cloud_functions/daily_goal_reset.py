# Cloud function to be added when later deployed
from datetime import date
from app import create_app, db
from flask import jsonify
from services.goals_service import get_or_create_daily_goal

def daily_goal_reset_logic(user_id=None, target_date=None):
    target_date = target_date or date.today()

    app = create_app()
    with app.app_context():
        from models import User, NutritionGoal

        reset_users_count = 0
        users_without_nutrition_goal = 0

        def reset_daily_goal_for_user(user_id):
            nonlocal reset_users_count, users_without_nutrition_goal

            # Ensure a DailyGoal exists for this user and date
            daily_goal = get_or_create_daily_goal(user_id, target_date)
            if not daily_goal:
                users_without_nutrition_goal += 1
                return

            # Fetch the NutritionGoal this DailyGoal is based on
            nutrition_goal = NutritionGoal.query.get(daily_goal.goal_id)
            if not nutrition_goal:
                users_without_nutrition_goal += 1
                return

            # Reset remaining macros back to target values
            daily_goal.remaining_calories = nutrition_goal.calories
            daily_goal.remaining_protein = nutrition_goal.protein
            daily_goal.remaining_fat = nutrition_goal.fat
            daily_goal.remaining_carbs = nutrition_goal.carbs

            reset_users_count += 1

        # Run for one user or all users
        if user_id is not None:
            reset_daily_goal_for_user(user_id)
        else:
            users = User.query.all()
            for user in users:
                reset_daily_goal_for_user(user.id)

        # Persist all changes
        db.session.commit()

        return {
            "function": "daily_goal_reset",
            "date": str(target_date),
            "users_reset": reset_users_count,
            "users_without_nutrition_goal": users_without_nutrition_goal,
            "message": "DailyGoal remaining values reset to NutritionGoal targets."
        }




# Cloud Function
def daily_goal_reset(request):
    user_id = request.args.get('user_id')

    result = daily_goal_reset_logic(
        user_id=int(user_id) if user_id else None,
        target_date=date.today()
    )

    return jsonify(result), 200
