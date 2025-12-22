from datetime import datetime, date

from app import db
from passlib.hash import sha256_crypt
from utils.nutrition import bmr_calculation, tdee_calculation, macros_calculation

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Password handling
    def set_password(self, password):  # To hash passwords before storing
        self.password_hash = sha256_crypt.encrypt(password)

    def check_password(self, password):  # To verify password during login
        return sha256_crypt.verify(password, self.password_hash)

# Represents meals
class Meal(db.Model):
    __tablename__ = 'meals'

    id = db.Column(db.Integer, primary_key=True) # Primary key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # Foreign key linking meal to user
    name = db.Column(db.String(80), nullable=False) # Name of meal
    description = db.Column(db.String(255)) # Meal description
    added_at = db.Column(db.DateTime, default=db.func.current_timestamp()) # Time meal is stored in the app

    # Nutritional info
    calories = db.Column(db.Float, default=0.0)
    protein = db.Column(db.Float, default=0.0)
    fat = db.Column(db.Float, default=0.0)
    carbs = db.Column(db.Float, default=0.0)

    user = db.relationship('User', backref=db.backref('meals', lazy=True))


class NutritionGoal(db.Model):
    __tablename__ = 'nutrition_goals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # User input values
    weight_kg = db.Column(db.Float, nullable=False)
    height_cm = db.Column(db.Float, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    activity_level = db.Column(db.String(20), default='sedentary')

    # Slider input value
    goal_percent = db.Column(db.Float, default=0.0)

    # Calculated values
    bmr = db.Column(db.Float)
    tdee = db.Column(db.Float)
    calories = db.Column(db.Float)
    protein = db.Column(db.Float)
    fat = db.Column(db.Float)
    carbs = db.Column(db.Float)
    goal_category = db.Column(db.String(20))

    # Goal Tracking using timestamp
    created_at = db.Column(db.DateTime, default=datetime.now())

    # Relationship to 'User'
    user = db.relationship('User', backref=db.backref('goals', lazy=True))

    def calculate_goal(self):
        self.bmr = bmr_calculation(self.weight_kg, self.height_cm, self.age, self.sex)
        self.tdee = tdee_calculation(self.bmr, self.activity_level)

        # Adjust calories based on slider %
        self.calories = self.tdee * (1 + self.goal_percent / 100)

        # Macros
        macros = macros_calculation(self.weight_kg, self.calories)
        self.protein = macros['protein']
        self.fat = macros['fat']
        self.carbs = macros['carbs']

        # Determine goal category
        if self.goal_percent < 0:
            self.goal_category = 'cut'
        elif self.goal_percent == 0:
            self.goal_category = 'maintain'
        else:
            self.goal_category = 'bulk'
        return self


class DailyGoal(db.Model):
    __tablename__ = 'daily_goals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey('nutrition_goals.id'), nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)

    remaining_calories = db.Column(db.Float, nullable=False)
    remaining_protein = db.Column(db.Float, nullable=False)
    remaining_fat = db.Column(db.Float, nullable=False)
    remaining_carbs = db.Column(db.Float, nullable=False)

    user = db.relationship('User', backref=db.backref('daily_goals', lazy=True))
    goal = db.relationship('NutritionGoal', backref=db.backref('daily_snapshots', lazy=True))
