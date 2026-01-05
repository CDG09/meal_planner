import os
from urllib import response

import requests
from requests_oauthlib import OAuth1

# Environment variables
FATSECRET_BASE_URL = "https://platform.fatsecret.com/rest/server.api"
FATSECRET_CONSUMER_KEY = os.getenv("FATSECRET_CONSUMER_KEY")
FATSECRET_CONSUMER_SECRET = os.getenv("FATSECRET_CONSUMER_SECRET")

if not FATSECRET_CONSUMER_KEY or not FATSECRET_CONSUMER_SECRET:
    raise RuntimeError("FatSecret API not configured")

# OAuth Details
def oauth():
    return OAuth1(
        client_key=FATSECRET_CONSUMER_KEY,
        client_secret=FATSECRET_CONSUMER_SECRET,
        signature_method='HMAC-SHA1',
    )

# API Calls
def search_foods(query, max_results=10, page=0):
    url = f"{FATSECRET_BASE_URL}/foods/search"
    params = {
        "search_expression": query,
        "page_number": page,
        "max_results": max_results,
        "format": "json"
    }
    response = requests.get(
        url,
        params=params,
        auth=oauth(),
        timeout=10
    )
    response.raise_for_status()
    return response.json()

def get_food(food_id):
    url = f"{FATSECRET_BASE_URL}/food/v4"
    params = {
        "food_id": food_id,
        "format": "json"
    }

    response = requests.get(
        url,
        params=params,
        auth=oauth(),
        timeout=10
    )
    response.raise_for_status()
    return response.json()