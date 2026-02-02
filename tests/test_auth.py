import os
os.environ["UNIT_TESTING"] = "1"
import unittest
from datetime import datetime
from app import create_app, db
from models import User, NutritionGoal

class TestAuthProtection(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SQLALCHEMY_TRACK_MODIFICATIONS": False, "SECRET_KEY": "test-secret","AUTO_CREATE_TABLES": False,})

        self.client = self.app.test_client()

        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        user = User(username="testuser")
        user.set_password("password")
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

    def tearDown(self):
        # resets test db
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.ctx.pop()

    def login_session(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user_id

    def test_api_requires_login_redirects(self):
        resp = self.client.get("/api/daily-goal/today", follow_redirects=False)
        self.assertIn(resp.status_code, (302, 401))

    def test_api_allows_when_logged_in(self):
        self.login_session()
        resp = self.client.get("/api/daily-goal/today")
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.get_json())