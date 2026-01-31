import os
import requests
from requests_oauthlib import OAuth1

# Environment variables
UNIT_TESTING = os.getenv("UNIT_TESTING") == "1"
FATSECRET_BASE_URL = "https://platform.fatsecret.com/rest/server.api"


def check_configured():
    if UNIT_TESTING:
        return

    FATSECRET_CONSUMER_KEY = os.getenv("FATSECRET_CONSUMER_KEY")
    FATSECRET_CONSUMER_SECRET = os.getenv("FATSECRET_CONSUMER_SECRET")

    if not FATSECRET_CONSUMER_KEY or not FATSECRET_CONSUMER_SECRET:
        raise RuntimeError("FatSecret API not configured.")
    return FATSECRET_CONSUMER_KEY, FATSECRET_CONSUMER_SECRET

# OAuth Details
def oauth():
    if UNIT_TESTING:
        return OAuth1(client_key="test", client_secret="test", signature_method="HMAC-SHA1")

    FATSECRET_CONSUMER_KEY, FATSECRET_CONSUMER_SECRET = check_configured()
    return OAuth1(
        client_key=FATSECRET_CONSUMER_KEY,
        client_secret=FATSECRET_CONSUMER_SECRET,
        signature_method='HMAC-SHA1',
    )

def convert_to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def _serving_to_grams(metric_amount, unit):
    if metric_amount is None:
        return None

    unit = (unit or "g").lower().strip()

    if unit == "g":
        return metric_amount
    if unit == "oz":
        return metric_amount * 28
    if unit == "ml":
        return metric_amount
    else:
        return None



# API Calls
def search_foods(query, max_results=10, page=0):
    params = {
        "method": "foods.search",
        "search_expression": query,
        "page_number": page,
        "max_results": max_results,
        "format": "json"
    }
    response = requests.get(
        FATSECRET_BASE_URL,
        params=params,
        auth=oauth(),
        timeout=10
    )
    response.raise_for_status()
    data = response.json()

    foods = data.get("foods", {}).get("food", [])
    if isinstance(foods, dict):
        foods = [foods]
    return [
        {
            "food_id": food["food_id"],
            "food_name": food["food_name"],
            "food_description": food.get("food_description", ""),
        }
        for food in foods
    ]

def get_food_by_id(food_id):
    params = {
        "method": "food.get.v4",
        "food_id": food_id,
        "format": "json"
    }

    response = requests.get(
        FATSECRET_BASE_URL,
        params=params,
        auth=oauth(),
        timeout=10
    )
    response.raise_for_status()

    food = response.json().get("food", {})
    serving = food.get("servings", {}).get("serving", [])
    if isinstance(serving, list):
        serving = serving[0] if serving else {}
    if not isinstance(serving, dict):
        serving = {}

    # Macros returned from Fatsecret
    calories = convert_to_float(serving.get("calories")) or 0.0
    protein = convert_to_float(serving.get("protein")) or 0.0
    fat = convert_to_float(serving.get("fat")) or 0.0
    carbs = convert_to_float(serving.get("carbohydrate")) or 0.0

    # Metric serving size
    metric_amount = convert_to_float(serving.get("metric_amount"))
    metric_unit = (serving.get("serving_amount_unit") or "g").lower().strip()
    serving_grams = _serving_to_grams(metric_amount, metric_unit)
    serving_ml = metric_amount if metric_unit == "ml" else None


    return {
        "name": food.get("food_name"),
        "calories": float(calories),
        "protein": float(protein),
        "fat": float(fat),
        "carbs": float(carbs),
        "metric_serving_amount": metric_amount,
        "serving_amount_unit": metric_unit,
        "serving_grams": serving_grams,
        "serving_ml": serving_ml,
        "source": "fatsecret"
    }
