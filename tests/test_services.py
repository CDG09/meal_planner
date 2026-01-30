import os
os.environ["UNIT_TESTING"] = "1"
import unittest
from datetime import datetime, date
from app import create_app, db
from models import User, NutritionGoal, DailyGoal
from services.goals_service import get_or_create_daily_goal

class TestGoalsService(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SQLALCHEMY_TRACK_MODIFICATIONS": False, "SECRET_KEY": "test-secret",})
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        user = User(username="testuser")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        self.user_id = user.id
        goal = NutritionGoal(
            user_id=self.user_id,
            weight_kg=80, height_cm=180, age=22, sex="male",
            activity_level="sedentary", goal_percent=0.0,
            bmr=1800, tdee=2200,
            calories=2200, protein=160, fat=70, carbs=250,
            goal_category="maintain",
            created_at=datetime.utcnow()
        )
        db.session.add(goal)
        db.session.commit()

    # Reset the db
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.ctx.pop()

    def test_get_or_create_daily_goal_creates(self):
        dg = get_or_create_daily_goal(self.user_id, date.today())
        self.assertIsNotNone(dg)
        self.assertEqual(dg.user_id, self.user_id)
        self.assertEqual(dg.remaining_calories, 2200)

        saved = DailyGoal.query.filter_by(user_id=self.user_id, date=date.today()).first()
        self.assertIsNotNone(saved)


def test_get_or_create_daily_goal_idempotent(self):
    dg1 = get_or_create_daily_goal(self.user_id)
    dg2 = get_or_create_daily_goal(self.user_id)
    self.assertEqual(dg1.id, dg2.id)