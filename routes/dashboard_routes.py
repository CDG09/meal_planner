from flask import Blueprint, render_template, session, redirect, url_for, flash

from utils.auth import login_required
from utils.goals import get_daily_goal

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard')
@login_required
def view_dashboard():
    user_id = session.get('user_id')

    # Get or create today's daily goal
    daily_goal = get_daily_goal(user_id)
    if not daily_goal:
        flash('Please set a nutrition goal first')
        return redirect(url_for('goals.new_goal'))

    return render_template('dashboard.html', daily_goal=daily_goal)