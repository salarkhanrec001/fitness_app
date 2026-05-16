import os
from flask import Flask, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from config import config
from extensions import db, migrate, bcrypt, login_manager, csrf, mail


def _load_secret_key(app):
    secret_key = os.environ.get("SECRET_KEY") or app.config.get("SECRET_KEY")
    if secret_key:
        app.config["OPENAI_API_KEY"] = secret_key
        return

    instance_dir = os.path.join(app.root_path, "instance")
    secret_key_path = os.path.join(instance_dir, "secret_key.txt")

    if os.path.exists(secret_key_path):
        with open(secret_key_path, "r", encoding="utf-8") as secret_file:
            secret_key = secret_file.read().strip()
            if secret_key:
                app.config["SECRET_KEY"] = secret_key
                return

    secret_key = os.urandom(32).hex()
    with open(secret_key_path, "w", encoding="utf-8") as secret_file:
        secret_file.write(secret_key)

    app.config["SECRET_KEY"] = secret_key
    app.logger.warning(
        "SECRET_KEY was missing; generated a fallback secret key in instance/secret_key.txt"
    )


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    if config_name not in config:
        raise ValueError(f"Unknown config name: {config_name}")

    app = Flask(__name__)
    
    # Configure ProxyFix for cPanel/Phusion Passenger
    # This ensures url_for(_external=True) uses https:// instead of http://
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    app.config.from_object(config[config_name])

    # Cache config
    app.config.setdefault("CACHE_TYPE", "SimpleCache")
    app.config.setdefault("CACHE_DEFAULT_TIMEOUT", 3600)

    # Ensure instance and upload folders exist
    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    _load_secret_key(app)

    # ── Initialise extensions ──
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

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
            DailyRecommendation, WorkoutLog, WeightLog,
            # Motivaura feature models
            Habit, HabitLog,
            Timetable, TimeSlot, JournalEntry, Achievement,
            Notification,
            Challenge, ChallengeParticipant,
        )

        # Register existing blueprints
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
        from routes.monk_mode import monk_mode_bp

        app.register_blueprint(landing_bp,     url_prefix="/")
        app.register_blueprint(auth_bp,        url_prefix="/auth")
        app.register_blueprint(onboarding_bp,  url_prefix="/onboard")
        app.register_blueprint(monk_mode_bp,  url_prefix="/dashboard/monk")
        app.register_blueprint(dashboard_bp,   url_prefix="/dashboard")
        app.register_blueprint(ai_bp,          url_prefix="/ai")
        app.register_blueprint(exercise_bp,    url_prefix="/exercise")
        app.register_blueprint(social_bp,      url_prefix="/social")
        app.register_blueprint(goals_bp,       url_prefix="/goals")
        app.register_blueprint(profile_bp,     url_prefix="/profile")
        from routes.admin import admin_bp
        app.register_blueprint(admin_bp,       url_prefix="/admin")
        app.register_blueprint(account_bp,     url_prefix="/account")

        # ── Register Motivaura feature blueprints ──
        from routes.habits import habits_bp
        from routes.timetable import timetable_bp
        from routes.journal import journal_bp
        from routes.achievements import achievements_bp
        from routes.notifications import notifications_bp
        from routes.focus import focus_bp

        app.register_blueprint(habits_bp,         url_prefix="/habits")
        app.register_blueprint(timetable_bp,      url_prefix="/timetable")
        app.register_blueprint(journal_bp,        url_prefix="/journal")
        app.register_blueprint(achievements_bp,   url_prefix="/achievements")
        app.register_blueprint(notifications_bp,  url_prefix="/notifications")
        app.register_blueprint(focus_bp,          url_prefix="/focus")


        # ── Custom error handlers ──
        @app.errorhandler(404)
        def not_found(e):
            return render_template("errors/404.html"), 404

        @app.errorhandler(500)
        def server_error(e):
            import traceback
            app.logger.error(f"500 Internal Server Error: {e}")
            traceback.print_exc()
            return render_template("errors/500.html"), 500

        @app.errorhandler(429)
        def rate_limited(e):
            return render_template("errors/429.html"), 429

        # ── Jinja globals for Motivaura features ──
        from datetime import datetime, timezone

        @app.template_global()
        def now():
            return datetime.now(timezone.utc)

        @app.template_global()
        def current_year():
            return datetime.now(timezone.utc).year

        @app.context_processor
        def inject_day_names():
            return {'day_names': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
