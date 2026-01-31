from __future__ import annotations
from datetime import datetime, timezone
import os
from pymongo import MongoClient

def _get_audit_collection():
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise RuntimeError("MONGO_URI is not set")

    db_name = os.getenv("MONGO_DB_NAME", "mealplanner")
    client = MongoClient(mongo_uri)

    return client[db_name]["audit_logs"]

def log_event(*, event, user_id=None, request=None, meta=None):
    doc = {
        "event": event,
        "user_id": user_id,
        "meta": meta or {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    if request is not None:
        doc["ip"] = request.headers.get("X-Forwarded-For", request.remote_addr)
        doc["user_agent"] = request.headers.get("User-Agent")

    col = _get_audit_collection()
    col.insert_one(doc)
