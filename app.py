import os

from flask import Flask, render_template, session
from flask_sqlalchemy import SQLAlchemy
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

#Initialize SQLAlchemy
db = SQLAlchemy(app)

# Model Imports
from models import User

# Create tables (if they don't exist)
with app.app_context():
    db.create_all()

# Blueprints
from auth_routes import auth
app.register_blueprint(auth)

app.config.from_object(Config)

# Context processors
@app.context_processor
def inject_user():
    from models import User
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None
    return dict(current_user=user)
# Routes
@app.route('/')
def home():
    return render_template('home.html', active_page='home')


if __name__ == '__main__':
    app.run()
