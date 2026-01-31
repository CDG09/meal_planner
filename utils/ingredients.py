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
def insert_fatsecret_ingredient(food_id, name, calories, protein, fat, carbs, user_id,metric_serving_amount=None, serving_amount_unit=None, serving_grams=None):
    collection = ingredient_collection()
    selector = {
        "user_id": int(user_id),
        "source": "fatsecret",
        "source_id": str(food_id)

    }

    try:
        metric_serving_amount = float(metric_serving_amount) if metric_serving_amount is not None else None
    except (TypeError, ValueError):
        metric_serving_amount = None

    serving_amount_unit = (serving_amount_unit or "g").lower().strip()

    try:
        serving_grams = float(serving_grams) if serving_grams is not None else None
    except (TypeError, ValueError):
        serving_grams = None

    update_doc = {
        "$set": {
            "name": name,
            "calories": float(calories),
            "protein": float(protein),
            "fat": float(fat),
            "carbs": float(carbs),
            "metric_serving_amount": metric_serving_amount,
            "serving_amount_unit": serving_amount_unit,
            "serving_grams": serving_grams,
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

def calculate_macros_from_portions(ingredient_docs, portions):
    totals = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}

    grams_map = {}
    for p in portions or []:
        ing_id = str(p.get("ingredient_id"))
        try:
            grams_used = float(p.get("grams_used", 0))
        except (TypeError, ValueError):
            grams_used = 0.0
        grams_map[ing_id] = max(grams_used, 0.0)

    for ing in ingredient_docs:
        ing_id = str(ing.get("_id"))
        grams_used = grams_map.get(ing_id, 0.0)


        try:
            serving_grams = float(ing.get("serving_grams", 100) or 100)
        except (TypeError, ValueError):
            serving_grams = 100.0

        multiplier = (grams_used / serving_grams) if serving_grams > 0 else 0.0

        totals["calories"] += float(ing.get("calories", 0) or 0) * multiplier
        totals["protein"] += float(ing.get("protein", 0) or 0) * multiplier
        totals["fat"] += float(ing.get("fat", 0) or 0) * multiplier
        totals["carbs"] += float(ing.get("carbs", 0) or 0) * multiplier

    return totals

