import os
from flask import Flask, render_template
from config import config
from extensions import db, migrate, bcrypt, login_manager, csrf


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    if config_name not in config:
        raise ValueError(f"Unknown config name: {config_name}")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Cache config
    app.config.setdefault("CACHE_TYPE", "SimpleCache")
    app.config.setdefault("CACHE_DEFAULT_TIMEOUT", 3600)

    # Ensure instance and upload folders exist
    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ── Initialise extensions ──
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Flask-Caching
    from flask_caching import Cache
    app.cache = Cache(app)  # accessible as current_app.cache or app.cache

    # Flask-Limiter (configurable storage; sensible global defaults)
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    app.limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["2000 per day", "500 per hour"],
        storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
    )

    with app.app_context():
        from models import (  # noqa: F401
            User, OnboardingProfile, FitnessPlan,
            Friend, FriendRequest, Message,
            Goal, Streak, PasswordReset,
            DailyRecommendation, WorkoutLog,
        )

        # Register blueprints
        from routes.auth import auth_bp
        from routes.landing import landing_bp
        from routes.onboarding import onboarding_bp
        from routes.dashboard import dashboard_bp
        from routes.ai_routes import ai_bp
        from routes.exercise import exercise_bp
        from routes.social import social_bp
        from routes.goals import goals_bp
        from routes.profile import profile_bp
        from routes.account import account_bp

        app.register_blueprint(landing_bp,     url_prefix="/")
        app.register_blueprint(auth_bp,        url_prefix="/auth")
        app.register_blueprint(onboarding_bp,  url_prefix="/onboard")
        app.register_blueprint(dashboard_bp,   url_prefix="/dashboard")
        app.register_blueprint(ai_bp,          url_prefix="/ai")
        app.register_blueprint(exercise_bp,    url_prefix="/exercise")
        app.register_blueprint(social_bp,      url_prefix="/social")
        app.register_blueprint(goals_bp,       url_prefix="/goals")
        app.register_blueprint(profile_bp,     url_prefix="/profile")
        from routes.admin import admin_bp
        app.register_blueprint(admin_bp,       url_prefix="/admin")
        app.register_blueprint(account_bp,     url_prefix="/account")

        # ── Custom error handlers ──
        @app.errorhandler(404)
        def not_found(e):
            return render_template("errors/404.html"), 404

        @app.errorhandler(500)
        def server_error(e):
            return render_template("errors/500.html"), 500

        @app.errorhandler(429)
        def rate_limited(e):
            return render_template("errors/429.html"), 429

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
