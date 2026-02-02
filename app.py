from flask import Flask, render_template, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
from utils.mongo import close_mongo_client
import os

# Initialize flask extensions
db = SQLAlchemy()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)

# App factory
def create_app(test_config=None):
    # Initialize the app
    app = Flask(__name__)

    # App config
    if test_config is None:
        app.config.from_object(Config)
    else:
        app.config.update(test_config)

    # Attach extensions to current config
    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    @app.teardown_appcontext
    def _close_mongo(exception=None):
        close_mongo_client()

    # Create application context for current app
    with app.app_context():
        import models

        # Create db tables if not already existing
        if app.config.get("AUTO_CREATE_TABLES", False):
            db.create_all()

    # Initialize blueprints within the current app

    # Goals routes
    from routes.goals_routes import goals
    app.register_blueprint(goals)

    # Auth routes
    from routes.auth_routes import auth
    app.register_blueprint(auth)

    # Meal routes
    from routes.meal_routes import meal
    app.register_blueprint(meal)

    # Progress routes
    from routes.progress_routes import progress
    app.register_blueprint(progress)

    # Dashboard routes
    from routes.dashboard_routes import dashboard
    app.register_blueprint(dashboard)

    # REST API routes
    from api.api_routes import api
    app.register_blueprint(api)

    # Inject user context into jinja templates
    @app.context_processor
    def inject_user():
        from models import User
        user_id = session.get('user_id')
        user = User.query.get(user_id) if user_id else None
        return dict(current_user=user)

    # root route
    @app.route('/')
    def home():
        return render_template('home.html', active_page='home')

    # Global security headers
    @app.after_request
    def add_security_headers(response):
        # Prevent file type sniffing (Mime)
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Prevent click-jacking
        response.headers["X-Frame-Options"] = "DENY"
        # Introduce a strict Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    return app

# Run the app
if __name__ == "__main__":
    app = create_app()
    app.run()
