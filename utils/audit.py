from datetime import datetime, timezone
import os
from utils.mongo import get_collection
# Fetches the logs from MongoDB
def fetch_audit_log_collection():
    return get_collection("audit_logs")

def log_event(*, event, user_id=None, request=None, meta=None):
    # Log structure
    log_record = {
        "event": event,
        "user_id": user_id,
        "meta": meta or {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    if request:
        # Grab ip
        forwarded_ip = request.headers.get("X-Forwarded-For")
        log_record["ip"] = forwarded_ip or request.remote_addr

        # Useful for security
        log_record["user_agent"] = request.headers.get("User-Agent")

    # Insert the audit record into MongoDB
    collection = fetch_audit_log_collection()

    try:
        collection.insert_one(log_record)
    except Exception as e:
        print(f"[audit] Failed to write event: {e}")
