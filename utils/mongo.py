import os
import pymongo
from pymongo import MongoClient


Mongo = os.getenv("MONGO_URI")
client = pymongo.MongoClient(Mongo)
mongo_db = client["mealplanner"]
ingredients = mongo_db["ingredients"]