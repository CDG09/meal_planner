# Handles ingredient storage and retrival using MongoDB
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask import current_app

# MongoDB Connection
def mongo_connect():
    return MongoClient(current_app.config['MONGO_URI'])

def ingredient_collection():
    client = mongo_connect()
    mongo_db = client['mealplanner']
    return mongo_db['ingredients']

# Ingredient Operations
def create_ingredient(name, calories, protein, fat, carbs, user_id, source="manual"):
    ingredient = {
        "name": name,
        "calories": float(calories),
        "protein": float(protein),
        "fat": float(fat),
        "carbs": float(carbs),
        "source": source,
        "user_id": user_id
    }
    collection = ingredient_collection()
    result = collection.insert_one(ingredient)
    return result.inserted_id

def get_ingredient_by_id(ingredient_ids, user_id):
    object_ids = [ObjectId(i) for i in ingredient_ids]
    collection = ingredient_collection()
    ingredients = list(collection.find({"_id": {"$in": object_ids}, "user_id": user_id}))
    return ingredients

def get_all_ingredients(user_id):
    collection = ingredient_collection()
    return list(collection.find({"user_id": user_id}))

# Calculation Logic
def calculate_macros_from_ingredients(ingredients):
    totals = {
        "calories": 0.0,
        "protein": 0.0,
        "fat": 0.0,
        "carbs": 0.0
    }

    for ingredient in ingredients:
        totals["calories"] += ingredient.get("calories", 0)
        totals["protein"] += ingredient.get("protein", 0)
        totals["fat"] += ingredient.get("fat", 0)
        totals["carbs"] += ingredient.get("carbs", 0)

    return totals