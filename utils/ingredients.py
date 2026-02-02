# Handles ingredients operations (storing & retrieving from MongoDB)
from bson.objectid import ObjectId
from utils.mongo import get_collection

# Return the ingredient collection from the db
def ingredient_collection():
    return get_collection("ingredients")

# Add ingredient based on manual inputs
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

# Fetch ingredients based on MongoDB ObjectId
def get_ingredient_by_ids(ingredient_ids, user_id):
    valid_ids = []
    for _id in ingredient_ids:
        try:
            valid_ids.append(ObjectId(_id))
        except Exception:
            # Skip any invalid ids
            continue

    if not valid_ids:
        return []

    ingredients = ingredient_collection()
    query = {
        "_id": {"$in": valid_ids},
        "user_id": int(user_id)
    }

    return list(ingredients.find(query))

# Return all ingredients belonging to a user
def get_all_ingredients(user_id):
    return list(ingredient_collection().find({"user_id": int(user_id)}))

# Insert an ingredient sourced from the fatsecret API
def insert_fatsecret_ingredient(food_id, name, calories, protein, fat, carbs, user_id, metric_serving_amount=None, serving_amount_unit=None, serving_grams=None):
    ingredients = ingredient_collection()

    # Used to identify individual ingredients which belong to users
    identifier = {
        "user_id": int(user_id),
        "source": "fatsecret",
        "source_id": str(food_id)
    }

    # Cleanup values
    try:
        metric_serving_amount = float(metric_serving_amount)
    except (TypeError, ValueError):
        metric_serving_amount = None

    if not serving_amount_unit:
        serving_amount_unit = "g"
    serving_amount_unit = serving_amount_unit.lower().strip()

    try:
        serving_grams = float(serving_grams)
    except (TypeError, ValueError):
        serving_grams = None

    # Insert or update fields in db
    update_data = {
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

    outcome = ingredients.update_one(identifier, update_data, upsert=True)

    # return the new _id if ingredient is inserted
    if outcome.upserted_id:
        return outcome.upserted_id

    existing = ingredients.find_one(identifier, {"_id": 1})
    return existing["_id"]

# Calculates macros from ingredients presuming one serving
def calculate_macros_from_ingredients(ingredients):
    macro_totals = {
        "calories": 0.0,
        "protein": 0.0,
        "fat": 0.0,
        "carbs": 0.0
    }

    for ing in ingredients:
        macro_totals["calories"] += float(ing.get("calories", 0) or 0)
        macro_totals["protein"] += float(ing.get("protein", 0) or 0)
        macro_totals["fat"] += float(ing.get("fat", 0) or 0)
        macro_totals["carbs"] += float(ing.get("carbs", 0) or 0)

    return macro_totals

# Calculate macros from ingredients where a portion size is specified
def calculate_macros_from_portions(ingredient_docs, portions):
    totals = {
        "calories": 0.0,
        "protein": 0.0,
        "fat": 0.0,
        "carbs": 0.0
    }

    grams_lookup = {}

    for portion in portions or []:
        try:
            ing_id = str(portion.get("ingredient_id"))
            grams_value = float(portion.get("grams_used", 0))
        except (TypeError, ValueError):
            grams_value = 0.0
        # Ensures grams is never negative
        grams_lookup[ing_id] = max(0.0, grams_value)

    for ingredient in ingredient_docs:
        ing_id = str(ingredient.get("_id"))
        grams_used = grams_lookup.get(ing_id, 0.0)

        # If portion isn't provided default to 100g
        try:
            serving_size = float(ingredient.get("serving_grams", 100) or 100)
        except (TypeError, ValueError):
            serving_size = 100.0

        # Avoid bad data (0 division)
        multiplier = grams_used / serving_size if serving_size > 0 else 0.0

        # Scale each macro by how much was used
        totals["calories"] += float(ingredient.get("calories", 0) or 0) * multiplier
        totals["protein"] += float(ingredient.get("protein", 0) or 0) * multiplier
        totals["fat"] += float(ingredient.get("fat", 0) or 0) * multiplier
        totals["carbs"] += float(ingredient.get("carbs", 0) or 0) * multiplier

    return totals