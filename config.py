import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///meal_planner.db'
    SQLALCHEMY_TRACK_MODIFICATION = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    MONGO_URI = os.environ.get('MONGO_URI')