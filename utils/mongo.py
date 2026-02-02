from pymongo import MongoClient
from flask import current_app, g

def get_mongo_client():
    client = g.get("mongo_client")
    if client is not None:
        return client

    mongo_uri = current_app.config.get("MONGO_URI")
    if not mongo_uri:
        raise RuntimeError("Missing MONGO_URI in Flask config")

    client = MongoClient(mongo_uri)
    g.mongo_client = client
    return client

def get_mongo_db():
    client = get_mongo_client()
    db_name = current_app.config.get("MONGO_DB_NAME") or "mealplanner"
    return client[db_name]

def get_collection(collection_name):
    return get_mongo_db()[collection_name]

def close_mongo_client():
    client = g.pop("mongo_client", None)
    if client is not None:
        client.close()