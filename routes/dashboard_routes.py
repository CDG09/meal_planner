from flask import Blueprint, render_template, session, redirect, url_for, flash
from datetime import date
from utils.auth import login_required
from utils.goals import get_daily_goal
from models import MealLog
dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard')
@login_required
def view_dashboard():
    user_id = session.get('user_id')
    today = date.today()
    # Get or create today's daily goal
    daily_goal = get_daily_goal(user_id)
    if not daily_goal:
        flash('Please set a nutrition goal first')
        return redirect(url_for('goals.new_goal'))

        # Fetch meals logged today
    logs_today = MealLog.query.filter_by(user_id=user_id,date=today).all()

    # Aggregate totals eaten today
    totals = {
        'calories': sum(log.calories for log in logs_today),
        'protein': sum(log.protein for log in logs_today),
        'fat': sum(log.fat for log in logs_today),
        'carbs': sum(log.carbs for log in logs_today)
    }

    return render_template('dashboard.html', daily_goal=daily_goal,totals=totals,log=logs_today)