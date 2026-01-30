from functools import wraps
from flask import request, jsonify, current_app

def require_api_token(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-API-Token", "").strip()
        expected = (current_app.config.get("API_TOKEN") or "").strip()

        # If no token configured, fail closed in production, but allow in testing/dev if you want.
        if not expected:
            return jsonify({"error": "API token not configured"}), 500

        if token != expected:
            return jsonify({"error": "Unauthorized"}), 401

        return fn(*args, **kwargs)
    return wrapper