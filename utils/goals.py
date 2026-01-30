from services.goals_service import get_or_create_daily_goal


def get_daily_goal(user_id):
   return get_or_create_daily_goal(user_id)
