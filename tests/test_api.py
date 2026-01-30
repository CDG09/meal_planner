import os
os.environ["UNIT_TESTING"] = "1"
import unittest
from datetime import datetime
from unittest.mock import patch
from bson import ObjectId
from app import create_app, db
from models import User, NutritionGoal, Meal


class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SQLALCHEMY_TRACK_MODIFICATIONS": False, "SECRET_KEY": "test-secret",})
        self.client = self.app.test_client()
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

        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user_id

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.ctx.pop()

    @patch("api.api_routes.get_all_ingredients")
    def test_ingredients_list_endpoint_returns_data(self, mock_get_all):
        mock_get_all.return_value = [
            {
                "_id": ObjectId(),
                "user_id": self.user_id,
                "name": "Milk",
                "calories": 100,
                "protein": 7,
                "fat": 4,
                "carbs": 10,
                "source": "manual",
                "source_id": None,
            }
        ]

        resp = self.client.get("/api/ingredients")
        self.assertEqual(resp.status_code, 200)

        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Milk")
        self.assertIn("id", data[0])

    def test_ingredients_post_validation(self):
        resp = self.client.post("/api/ingredients", json={"calories": 10})
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertEqual(data.get("error"), "Name is required")

    @patch("api.api_routes.create_ingredient")
    def test_ingredients_post_creates_when_valid(self, mock_create):
        mock_create.return_value = ObjectId()

        resp = self.client.post("/api/ingredients", json={
            "name": "Oats",
            "calories": 150,
            "protein": 5,
            "fat": 3,
            "carbs": 27
        })
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertIn("id", data)
        self.assertEqual(data["name"], "Oats")

    @patch("api.api_routes.calculate_macros_from_ingredients")
    @patch("api.api_routes.get_ingredient_by_id")
    def test_create_meal_with_ingredients(self, mock_get_by_ids, mock_calc):
        fake_docs = [
            {"_id": ObjectId(), "user_id": self.user_id, "calories": 200, "protein": 4, "fat": 1, "carbs": 45},
            {"_id": ObjectId(), "user_id": self.user_id, "calories": 300, "protein": 40, "fat": 7, "carbs": 0},
        ]

        mock_get_by_ids.return_value = fake_docs
        mock_calc.return_value = {
            "calories": 500,
            "protein": 44,
            "fat": 8,
            "carbs": 45,
        }

        resp = self.client.post("/api/meals", json={
            "name": "Chicken and Rice",
            "ingredient_ids": [
                str(fake_docs[0]["_id"]),
                str(fake_docs[1]["_id"]),
            ]
        })

        self.assertEqual(resp.status_code, 201)

        data = resp.get_json()
        self.assertIn("id", data)

        meal = Meal.query.get(data["id"])
        self.assertEqual(meal.calories, 500)
        self.assertEqual(meal.protein, 44)
        self.assertEqual(meal.fat, 8)
        self.assertEqual(meal.carbs, 45)

        mock_get_by_ids.assert_called_once()
        mock_calc.assert_called_once()
