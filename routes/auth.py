from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models.user import User
from models.streak import Streak

auth_bp = Blueprint("auth", __name__)


def _get_limiter():
    try:
        from flask import current_app
        return getattr(current_app._get_current_object(), 'limiter', None)
    except Exception:
        return None


# ── Shared page (login + signup toggled on one URL) ──────────────

@auth_bp.route("/", methods=["GET"])
def auth_page():
    """Combined login/signup page with toggle animation."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    mode = request.args.get("mode", "login")  # "login" or "signup"
    return render_template("auth/auth.html", mode=mode)


# Keep individual routes so old links / redirects keep working

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        errors = []
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if not email or "@" not in email:
            errors.append("Please enter a valid email address.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if User.query.filter_by(username=username).first():
            errors.append("Username already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("auth/auth.html", mode="signup",
                                   su_username=username, su_email=email)

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # get user.id

        # Handle optional avatar upload at signup
        avatar_file = request.files.get("avatar")
        if avatar_file and avatar_file.filename:
            from routes.profile import _allowed_file, _save_avatar
            if _allowed_file(avatar_file.filename):
                avatar_file.seek(0, 2)
                size = avatar_file.tell()
                avatar_file.seek(0)
                if size <= 8 * 1024 * 1024:
                    saved = _save_avatar(avatar_file, user.id)
                    if saved:
                        user.avatar = saved

        # Create default streak record
        streak = Streak(user_id=user.id)
        db.session.add(streak)
        db.session.commit()

        login_user(user)
        flash("Welcome to FitAI! Let's set up your profile. 🎉", "success")
        return redirect(url_for("onboarding.step1"))

    return render_template("auth/auth.html", mode="signup")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        # Manual rate limit check (10 per minute per IP)
        limiter = _get_limiter()
        identifier = request.form.get("identifier", "").strip()
        password   = request.form.get("password", "")
        remember   = request.form.get("remember") == "on"

        user = User.query.filter(
            (User.email == identifier.lower()) | (User.username == identifier)
        ).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get("next")
            flash(f"Welcome back, {user.username}! 👋", "success")
            if not user.onboarding_complete:
                return redirect(url_for("onboarding.step1"))
            return redirect(next_page or url_for("dashboard.index"))

        flash("Invalid credentials. Please try again.", "error")
        return render_template("auth/auth.html", mode="login",
                               li_identifier=identifier)

    return render_template("auth/auth.html", mode="login")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
