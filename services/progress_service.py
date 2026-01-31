from datetime import date, timedelta
from sqlalchemy import func
from app import db
from models import MealLog, NutritionGoal


def _status_for_day(goal_category, consumed_cal, target_cal):
    goal_category = (goal_category or "maintain").lower().strip()

    # Avoid divide-by-zero and weird goals
    if target_cal <= 0:
        return {"label": "No target", "on_track": False, "rule": "target_calories<=0"}

    if goal_category == "cut":
        return {
            "label": "On track" if consumed_cal <= target_cal else "Over target",
            "on_track": consumed_cal <= target_cal,
            "rule": "cut: consumed<=target"
        }

    if goal_category == "bulk":
        return {
            "label": "On track" if consumed_cal >= target_cal else "Under target",
            "on_track": consumed_cal >= target_cal,
            "rule": "bulk: consumed>=target"
        }

    # maintain default
    tol = max(target_cal * 0.05, 100.0)
    low = target_cal - tol
    high = target_cal + tol

    on_track = low <= consumed_cal <= high
    return {
        "label": "On track" if on_track else "Off track",
        "on_track": on_track,
        "rule": f"maintain: within±{round(tol)}"
    }


def _pct(consumed: float, target: float) -> float:
    if target <= 0:
        return 0.0
    return round((consumed / target) * 100, 1)


def get_progress_history(user_id: int, days: int = 14):
    if days < 1:
        days = 1
    if days > 90:
        days = 90

    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    # Latest goal
    goal = (
        NutritionGoal.query
        .filter_by(user_id=user_id)
        .order_by(NutritionGoal.created_at.desc())
        .first()
    )
    if not goal:
        return {"error": "no_goal"}

    # Sum MealLogs per day (ONLY days that have logs will appear)
    rows = (
        db.session.query(
            MealLog.date.label("d"),
            func.sum(MealLog.calories).label("calories"),
            func.sum(MealLog.protein).label("protein"),
            func.sum(MealLog.fat).label("fat"),
            func.sum(MealLog.carbs).label("carbs"),
        )
        .filter(
            MealLog.user_id == user_id,
            MealLog.date >= start_date,
            MealLog.date <= end_date,
        )
        .group_by(MealLog.date)
        .all()
    )

    target = {
        "calories": float(goal.calories or 0),
        "protein": float(goal.protein or 0),
        "fat": float(goal.fat or 0),
        "carbs": float(goal.carbs or 0),
    }

    # Build history ONLY from the aggregated rows
    history = []
    for r in sorted(rows, key=lambda x: x.d):
        consumed = {
            "calories": float(r.calories or 0),
            "protein": float(r.protein or 0),
            "fat": float(r.fat or 0),
            "carbs": float(r.carbs or 0),
        }

        remaining = {
            "calories": round(target["calories"] - consumed["calories"], 1),
            "protein": round(target["protein"] - consumed["protein"], 1),
            "fat": round(target["fat"] - consumed["fat"], 1),
            "carbs": round(target["carbs"] - consumed["carbs"], 1),
        }

        status = _status_for_day(goal.goal_category, consumed["calories"], target["calories"])

        history.append({
            "date": str(r.d),
            "target": target,
            "consumed": {
                "calories": round(consumed["calories"], 1),
                "protein": round(consumed["protein"], 1),
                "fat": round(consumed["fat"], 1),
                "carbs": round(consumed["carbs"], 1),
            },
            "remaining": remaining,
            "percent": {
                "calories": _pct(consumed["calories"], target["calories"]),
                "protein": _pct(consumed["protein"], target["protein"]),
                "fat": _pct(consumed["fat"], target["fat"]),
                "carbs": _pct(consumed["carbs"], target["carbs"]),
            },
            "status": status,
            "goal_category": goal.goal_category,
        })

    # Summary stats (based on days that actually have logs)
    on_track_days = sum(1 for d in history if d["status"]["on_track"])
    avg_cal_pct = round(sum(d["percent"]["calories"] for d in history) / len(history), 1) if history else 0.0

    # Report the actual range that has data (instead of the requested window)
    if history:
        actual_start = history[0]["date"]
        actual_end = history[-1]["date"]
    else:
        actual_start = str(start_date)
        actual_end = str(end_date)

    return {
        "goal_id": goal.id,
        "goal_category": goal.goal_category,
        "days": days,
        "start": actual_start,
        "end": actual_end,
        "summary": {
            "on_track_days": on_track_days,
            "total_days": len(history),
            "avg_calorie_percent": avg_cal_pct,
        },
        "history": history,
    }

