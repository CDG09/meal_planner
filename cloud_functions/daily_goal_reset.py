# Cloud function to be added when later deployed
from datetime import date
from flask import jsonify
from models import User
from services.goals_service import get_or_create_daily_goal

def daily_goal_reset(request):
    today = date.today()
    user_id = request.args.get('user_id')

    created_or_found = 0
    skipped_no_goal = 0

    if user_id:
        goal = get_or_create_daily_goal(int(user_id), today)
        if goal:
            created_or_found += 1
        else:
            skipped_no_goal += 1
    else:
        users = User.query.all()
        for user in users:
            goal = get_or_create_daily_goal(user.id, today)
            if goal:
                created_or_found += 1
            else:
                skipped_no_goal += 1

    return jsonify({
        "function": "daily_goal_reset",
        "date": str(today),
        "created_or_found": created_or_found,
        "skipped_no_goal": skipped_no_goal,
    }), 200