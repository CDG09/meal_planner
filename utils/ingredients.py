# Handles ingredient storage and retrieval using MongoDB
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
        "source_id": None,
        "user_id": int(user_id)
    }
    collection = ingredient_collection()
    result = collection.insert_one(ingredient)
    return result.inserted_id

# Fetch manual ingredients by MongoDB ObjectId
def get_ingredient_by_id(ingredient_ids, user_id):
    object_ids = []
    for i in ingredient_ids:
        try:
            object_ids.append(ObjectId(i))
        except Exception:
            continue

    if not object_ids:
        return []

    collection = ingredient_collection()
    return list(collection.find({
        "_id": {"$in": object_ids},
        "user_id": int(user_id)
    }))

# Fetch all ingredients for a user
def get_all_ingredients(user_id):
    collection = ingredient_collection()
    return list(collection.find({"user_id": int(user_id)}))

# Insert a FatSecret ingredient into MongoDB if it doesn't exist
def insert_fatsecret_ingredient(food_id, name, calories, protein, fat, carbs, user_id):
    collection = ingredient_collection()
    selector = {
        "user_id": int(user_id),
        "source": "fatsecret",
        "source_id": str(food_id)

    }

    update_doc = {
        "$set": {
            "name": name,
            "calories": float(calories),
            "protein": float(protein),
            "fat": float(fat),
            "carbs": float(carbs),
            "source": "fatsecret",
            "source_id": str(food_id),
            "user_id": int(user_id)
        }
    }

    result = collection.update_one(selector, update_doc, upsert=True)

    if result.upserted_id is not None:
        return result.upserted_id

    existing = collection.find_one(selector, {"_id": 1})
    return existing["_id"]

# Calculation Logic
def calculate_macros_from_ingredients(ingredients):
    totals = {
        "calories": 0.0,
        "protein": 0.0,
        "fat": 0.0,
        "carbs": 0.0
    }

    for ingredient in ingredients:
        totals["calories"] += float(ingredient.get("calories", 0) or 0)
        totals["protein"] += float(ingredient.get("protein", 0) or 0)
        totals["fat"] += float(ingredient.get("fat", 0) or 0)
        totals["carbs"] += float(ingredient.get("carbs", 0) or 0)

    return totals
