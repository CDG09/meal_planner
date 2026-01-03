import os
import pymongo

Mongo = os.getenv("MONGO_URI")
client = pymongo.MongoClient(Mongo)
mongo_db = client["meal_planner"]
get_nutrition =mongo_db["nutrition"]