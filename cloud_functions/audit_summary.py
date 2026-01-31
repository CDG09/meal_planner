from datetime import datetime, timedelta, timezone
from flask import jsonify
from utils.audit import _get_audit_collection

def audit_summary_logic(days=7, user_id=None):
    try:
        days = int(days)
    except (TypeError, ValueError):
        days = 7

    days = min(max(days, 1), 90)  # reasonable bounds

    since_dt = datetime.now(timezone.utc) - timedelta(days=days)
    since_iso = since_dt.isoformat()

    col = _get_audit_collection()

    match = {"created_at": {"$gte": since_iso}}
    if user_id is not None:
        match["user_id"] = user_id

    pipeline = [
        {"$match": match},
        {"$group": {"_id": "$event", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]

    grouped = list(col.aggregate(pipeline))

    counts = {g["_id"]: g["count"] for g in grouped}
    total = sum(counts.values())

    return {
        "function": "audit_summary",
        "days": days,
        "since": since_iso,
        "user_id": user_id,
        "total_events": total,
        "counts_by_event": counts,
    }

def audit_summary(request):
    days = request.args.get("days", "7")
    user_id = request.args.get("user_id")

    result = audit_summary_logic(
        days=days,
        user_id=int(user_id) if user_id else None
    )

    return jsonify(result), 200
