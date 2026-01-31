from flask import Blueprint, render_template, session, request
from utils.auth import login_required
from utils.audit import log_event
from services.progress_service import get_progress_history

progress = Blueprint("progress", __name__)

@progress.route("/progress")
@login_required
def view_progress():
    user_id = session.get("user_id")

    try:
        days = int(request.args.get("days", 14))
    except ValueError:
        days = 14

    data = get_progress_history(user_id, days=days)

    if "error" not in data:
        log_event(event="PROGRESS_VIEWED", user_id=user_id, request=request, meta={"days": days})

    return render_template("progress.html", data=data)
