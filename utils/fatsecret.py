import os
import requests
from requests_oauthlib import OAuth1

# Environment variables
FATSECRET_BASE_URL = "https://platform.fatsecret.com/rest/server.api"
FATSECRET_CONSUMER_KEY = os.getenv("FATSECRET_CONSUMER_KEY")
FATSECRET_CONSUMER_SECRET = os.getenv("FATSECRET_CONSUMER_SECRET")

if not FATSECRET_CONSUMER_KEY or not FATSECRET_CONSUMER_SECRET:
    raise RuntimeError("FatSecret API not configured")

def check_configured():
    if not FATSECRET_CONSUMER_KEY or not FATSECRET_CONSUMER_SECRET:
        raise RuntimeError("FatSecret API not configured.")

# OAuth Details
def oauth():
    return OAuth1(
        client_key=FATSECRET_CONSUMER_KEY,
        client_secret=FATSECRET_CONSUMER_SECRET,
        signature_method='HMAC-SHA1',
    )

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
    nutrients = food.get("servings", {}).get("serving", [])
    if isinstance(nutrients, list):
        if nutrients:
            nutrients = nutrients[0]
        else:
            nutrients = {}
    return {
        "name": food.get("food_name"),
        "calories": float(nutrients.get("calories", 0)),
        "protein": float(nutrients.get("protein", 0)),
        "fat": float(nutrients.get("fat", 0)),
        "carbs": float(nutrients.get("carbohydrate", 0)),
        "source": "fatsecret"
    }
