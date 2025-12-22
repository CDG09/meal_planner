from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from app import db
from models import NutritionGoal
from datetime import datetime

goals = Blueprint('goals', __name__)

@goals.route('/goals')
def view_goals():
    """View current goals"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to view your goals.')
        return redirect(url_for('auth.login'))

    user_goals = NutritionGoal.query.filter_by(user_id=user_id).order_by(NutritionGoal.created_at.desc()).all()
    return render_template('goals.html', goals=user_goals)


@goals.route('/goals/new', methods=['GET', 'POST'])
def new_goal():
    """Create a new goal"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to create a goal.')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        try:
            goal = NutritionGoal(
                user_id=user_id,
                weight_kg=float(request.form['weight']),
                height_cm=float(request.form['height']),
                age=int(request.form['age']),
                sex=request.form['sex'],
                activity_level=request.form['activity_level'],
                goal_percent=float(request.form['goal_percent']),
                created_at=datetime.now()
            )
        except (ValueError,KeyError):
            flash('Please provide valid values for all fields.')
            return redirect(url_for('goals.new_goal'))

        goal.calculate_goal()
        db.session.add(goal)
        db.session.commit()

        flash('You have successfully created a new goal.')
        return redirect(url_for('goals.view_goals'))

    return render_template('add_goal.html')


@goals.route('/goals/<int:goal_id>/edit', methods=['GET', 'POST'])
def edit_goal(goal_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to edit your goals.')
        return redirect(url_for('auth.login'))

    # Load the original goal for pre-filling the form
    original_goal = NutritionGoal.query.get_or_404(goal_id)
    if original_goal.user_id != user_id: # IDOR check
        flash('You cannot edit this goal.')
        return redirect(url_for('goals.view_goals'))

    if request.method == 'POST':
        # Wrap input parsing in try/except
        try:
            weight = float(request.form['weight'])
            height = float(request.form['height'])
            age = int(request.form['age'])
            goal_percent = float(request.form['goal_percent'])
        except (ValueError, KeyError):
            flash('Please provide valid values for all fields.')
            return redirect(url_for('goals.edit_goal', goal_id=goal_id))

        if weight != original_goal.weight_kg or height != original_goal.height_cm or age != original_goal.age:
            # Create a new snapshot instead of overwriting
            new_snapshot = NutritionGoal(
                user_id=user_id,
                weight_kg=weight,
                height_cm=height,
                age=age,
                sex=original_goal.sex,  # keep the original sex
                activity_level=original_goal.activity_level,
                goal_percent=goal_percent,
                created_at=datetime.now()
            )
            new_snapshot.calculate_goal()

            db.session.add(new_snapshot)
            db.session.commit()
            flash('Your goal has been updated.')
        # Only goal_percent being changed means the current snapshot is adjusted instead
        elif goal_percent != original_goal.goal_percent:
            original_goal.goal_percent = goal_percent
            original_goal.calculate_goal()
            db.session.commit()
            flash('Your goal has been updated.')
        else:
            flash('No changes have been made.')

        return redirect(url_for('goals.view_goals'))

    # GET request: show the edit form prefilled with original values
    return render_template('edit_goal.html', goal=original_goal)

@goals.route('/goals/<int:goal_id>/delete', methods=['GET', 'POST'])
def delete_goal(goal_id):
    # Deletes users current goal
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to delete your goals.')
        return redirect(url_for('auth.login'))

    goal = NutritionGoal.query.get_or_404(goal_id)

    # User can only delete their own goals (IDOR handling)
    if goal.user_id != user_id:
        flash('You cannot delete this goal.')
        return redirect(url_for('goals.view_goals'))

    db.session.delete(goal)
    db.session.commit()
    flash('You have successfully deleted this goal.')
    return redirect(url_for('goals.view_goals'))

@goals.route('/goals/delete_history', methods=['POST'])
def delete_history(): # Deletes users entire goal history
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to delete your goal history.')
        return redirect(url_for('auth.login'))

    user_goals = NutritionGoal.query.filter_by(user_id=user_id).all()

    if not user_goals:
        flash('No goal history to delete.')
        return redirect(url_for('goals.view_goals'))

    for goal in user_goals:
        db.session.delete(goal)

    db.session.commit()
    flash('Your goal history has been deleted.')
    return redirect(url_for('goals.view_goals'))


