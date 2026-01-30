import os
from datetime import timedelta

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///meal_planner.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    MONGO_URI = os.environ.get('MONGO_URI')
    API_TOKEN = os.environ.get('API_TOKEN')

    # cookie flags
    SESSION_COOKIE_HTTPONLY = True # Prevents session IDs being stolen from XSS attacks
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax") # Helps prevent CSRF
    SESSION_COOKIE_SECURE = os.getenv("FLASK_ENV") == "production" # Cookies are only sent within the app engine
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60) # Expire session after inactivity