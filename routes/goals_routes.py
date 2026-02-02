from flask import Blueprint, render_template, redirect, url_for, session, flash
from models import NutritionGoal
from utils.auth import login_required

goals = Blueprint('goals', __name__)

@goals.route('/goals')
@login_required
def view_goals():
    user_id = session.get('user_id')
    user_goals = NutritionGoal.query.filter_by(user_id=user_id).order_by(NutritionGoal.created_at.desc()).all()
    return render_template('goals.html', goals=user_goals)


@goals.route('/goals/new', methods=['GET'])
@login_required
def new_goal():
    user_id = session.get('user_id')
    return render_template("add_goal.html")


@goals.route('/goals/<int:goal_id>/edit', methods=['GET'])
@login_required
def edit_goal(goal_id):
    user_id = session.get('user_id')

    # Load the original goal for pre-filling the form
    goal = NutritionGoal.query.get_or_404(goal_id)
    if goal.user_id != user_id: # IDOR check
        flash('You cannot edit this goal.', 'danger')
        return redirect(url_for('goals.view_goals'))


    return render_template('edit_goal.html', goal=goal)






