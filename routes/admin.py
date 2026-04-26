from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from extensions import db
from models.user import User
from models.workout_log import WorkoutLog
from models.streak import Streak
from models.goal import Goal
from datetime import date, timedelta

admin_bp = Blueprint("admin", __name__)


def _admin_required(f):
    """Decorator: only allow users with is_admin flag."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            flash("Admin access required.", "error")
            return redirect(url_for("dashboard.index"))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/")
@login_required
@_admin_required
def index():
    # User stats
    total_users    = User.query.count()
    active_today   = (
        Streak.query
        .filter(Streak.last_activity_date == date.today())
        .count()
    )
    total_workouts = db.session.query(db.func.sum(Streak.total_workouts)).scalar() or 0
    total_goals    = Goal.query.count()
    goals_done     = Goal.query.filter_by(is_completed=True).count()

    # Recent signups
    recent_users = (
        User.query
        .order_by(User.created_at.desc())
        .limit(20)
        .all()
    )

    # Top streaks
    top_streaks = (
        Streak.query
        .order_by(Streak.current_streak.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "admin/index.html",
        total_users=total_users,
        active_today=active_today,
        total_workouts=total_workouts,
        total_goals=total_goals,
        goals_done=goals_done,
        recent_users=recent_users,
        top_streaks=top_streaks,
    )


@admin_bp.route("/users")
@login_required
@_admin_required
def users():
    page  = request.args.get("page", 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=25)
    return render_template("admin/users.html", users=users)


@admin_bp.route("/reset-streak/<int:user_id>", methods=["POST"])
@login_required
@_admin_required
def reset_streak(user_id):
    streak = Streak.query.filter_by(user_id=user_id).first()
    if streak:
        streak.current_streak = 0
        db.session.commit()
        flash(f"Streak reset for user {user_id}.", "success")
    return redirect(url_for("admin.users"))
