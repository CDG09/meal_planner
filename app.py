from flask import Flask, render_template, session
from flask_sqlalchemy import SQLAlchemy
from config import Config
import os

#Initialize SQLAlchemy
db = SQLAlchemy()

def create_app(test_config: dict | None = None):
    # Initialize Flask app
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    with app.app_context():
        from models import User, Meal, NutritionGoal

        if not app.config.get("TESTING", False) and os.getenv("AUTO_CREATE_TABLES", "1") == "1":
            db.create_all()

    # Blueprints

    # Goals routes
    from routes.goals_routes import goals
    app.register_blueprint(goals)

    # Auth routes
    from routes.auth_routes import auth
    app.register_blueprint(auth)

    # Meal routes
    from routes.meal_routes import meal
    app.register_blueprint(meal)

    # Dashboard routes
    from routes.dashboard_routes import dashboard
    app.register_blueprint(dashboard)

    # REST API routes
    from api.api_routes import api
    app.register_blueprint(api)

    # Dev / Cloud function routes
    from routes.dev_routes import dev
    app.register_blueprint(dev)

    # Context processors
    @app.context_processor
    def inject_user():
        from models import User
        user_id = session.get('user_id')
        user = User.query.get(user_id) if user_id else None
        return dict(current_user=user)

    # Routes
    @app.route('/')
    def home():
        return render_template('home.html', active_page='home')

    return app

app = None

if __name__ == "__main__":
    app = create_app()
    app.run()
