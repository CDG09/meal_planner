from flask import Flask, render_template, session
from flask_sqlalchemy import SQLAlchemy
from config import Config
import os
# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

#Initialize SQLAlchemy
db = SQLAlchemy(app)

# Model Imports
from models import User, Meal, NutritionGoal

# Create tables (if they don't exist)
with app.app_context():
    db.create_all()

# Blueprints

# Goals routes
from routes.goals_routes import goals
app.register_blueprint(goals)

# Auth routes

from routes.auth_routes import auth
app.register_blueprint(auth)

app.config.from_object(Config)

# Meal routes
from routes.meal_routes import meal
app.register_blueprint(meal)

# Dashboard routes
from routes.dashboard_routes import dashboard
app.register_blueprint(dashboard)

# Context processors
@app.context_processor
def inject_user():
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None
    return dict(current_user=user)
# Routes
@app.route('/')
def home():
    return render_template('home.html', active_page='home')


if __name__ == '__main__':
    app.run()
