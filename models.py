from datetime import datetime, date as dt_date
from app import db
from sqlalchemy import String, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from passlib.hash import sha256_crypt
from utils.nutrition import calc_bmr, estimate_tdee, breakdown_macros

class User(db.Model):
    __tablename__ = 'users'

    # Columns
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Password handling functions

    # Used to hash passwords before storing
    def set_password(self, password):
        self.password_hash = sha256_crypt.encrypt(password)

    # Used to verify password during login
    def check_password(self, password):
        return sha256_crypt.verify(password, self.password_hash)

class Meal(db.Model):
    __tablename__ = 'meals'

    # Keys
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False) # Link between meal and user

    # Meal metadata
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    added: Mapped[datetime] = mapped_column(server_default=db.func.current_timestamp(), nullable=False)

    # Meal ingredient info
    ingredients_ids: Mapped[dict | list | None] = mapped_column(db.JSON, nullable=True)
    ingredients_portions: Mapped[dict | list | None] = mapped_column(db.JSON, nullable=True)

    # Nutritional macros
    calories: Mapped[float] = mapped_column(default=0.0, nullable=False)
    protein: Mapped[float] = mapped_column(default=0.0, nullable=False)
    fat: Mapped[float] = mapped_column(default=0.0, nullable=False)
    carbs: Mapped[float] = mapped_column(default=0., nullable=False)

    # Table relationship between users and meals
    user: Mapped[User] = relationship("User", backref=db.backref('meals', lazy=True))

class MealLog(db.Model):
    __tablename__ = 'meal_logs'

    # Keys
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    meal_id: Mapped[int] = mapped_column(ForeignKey("meals.id"), nullable=False)

    # Log date
    date: Mapped[dt_date] = mapped_column(Date, default=dt_date.today, nullable=False)

    # Nutritional Macros at logging time
    calories: Mapped[float] = mapped_column(nullable=False)
    protein: Mapped[float] = mapped_column(nullable=False)
    fat: Mapped[float] = mapped_column(nullable=False)
    carbs: Mapped[float] = mapped_column(nullable=False)

class NutritionGoal(db.Model):
    __tablename__ = 'nutrition_goals'

    # Keys
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # User goal inputs
    weight_kg: Mapped[float] = mapped_column(nullable=False)
    height_cm: Mapped[float] = mapped_column(nullable=False)
    age: Mapped[int] = mapped_column(nullable=False)
    sex: Mapped[str] = mapped_column(String(10), nullable=False)
    activity_level: Mapped[str] = mapped_column(String(20), default="sedentary")
    goal_percent: Mapped[float] = mapped_column(default=0.0)

    # Calculated values
    bmr: Mapped[float | None] = mapped_column(nullable=True)
    tdee: Mapped[float | None] = mapped_column(nullable=True)
    calories: Mapped[float | None] = mapped_column(nullable=True)
    protein: Mapped[float | None] = mapped_column(nullable=True)
    fat: Mapped[float | None] = mapped_column(nullable=True)
    carbs: Mapped[float | None] = mapped_column(nullable=True)
    goal_category: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # timestamp
    created_at: Mapped[datetime] = mapped_column(server_default=db.func.now())

    # Relationship to user and their goals
    user: Mapped[User] = relationship("User", backref=db.backref("goals", lazy=True))

    # Calculate user goal based on user inputs
    def calculate_goal(self):
        self.bmr = calc_bmr(self.weight_kg, self.height_cm, self.age, self.sex)
        self.tdee = estimate_tdee(self.bmr, self.activity_level)

        # Adjust calories based on slider %
        self.calories = self.tdee * (1 + self.goal_percent / 100)

        # Calculate macros
        macros = breakdown_macros(self.weight_kg, self.calories)
        self.protein = macros["protein_g"]
        self.fat = macros["fat_g"]
        self.carbs = macros["carbs_g"]

        # Determine goal category (cut/maintain/bulk)
        if self.goal_percent < 0:
            self.goal_category = "cut"
        elif self.goal_percent == 0:
            self.goal_category = "maintain"
        else:
            self.goal_category = "bulk"

        return self

class DailyGoal(db.Model):
    __tablename__ = 'daily_goals'

    # Keys
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    goal_id: Mapped[int] = mapped_column(ForeignKey("nutrition_goals.id"), nullable=False)

    # timestamp
    date: Mapped[dt_date] = mapped_column(Date, default=dt_date.today, nullable=False)

    # Remaining macros for target
    remaining_calories: Mapped[float] = mapped_column(nullable=False)
    remaining_protein: Mapped[float] = mapped_column(nullable=False)
    remaining_fat: Mapped[float] = mapped_column(nullable=False)
    remaining_carbs: Mapped[float] = mapped_column(nullable=False)

    # Relationship with user
    user: Mapped[User] = relationship("User", backref=db.backref("daily_goals", lazy=True))

    # Relationship with goal
    goal: Mapped[NutritionGoal] = relationship("NutritionGoal", backref=db.backref('daily_snapshots', lazy=True,cascade='all, delete-orphan'))