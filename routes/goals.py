from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.goal import Goal

goals_bp = Blueprint("goals", __name__)


@goals_bp.route("/")
@login_required
def index():
    active_goals = Goal.query.filter_by(user_id=current_user.id, is_completed=False).order_by(Goal.created_at.desc()).all()
    completed_goals = Goal.query.filter_by(user_id=current_user.id, is_completed=True).order_by(Goal.completed_at.desc()).all()
    return render_template("goals.html", active_goals=active_goals, completed_goals=completed_goals)


@goals_bp.route("/create", methods=["POST"])
@login_required
def create():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    target_value = request.form.get("target_value", "").strip()
    current_value = request.form.get("current_value", "0").strip()
    unit = request.form.get("unit", "").strip()
    category = request.form.get("category", "habit").strip()
    deadline_str = request.form.get("deadline", "").strip()

    if not title:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "error": "Goal title is required."}), 400
        flash("Goal title is required.", "error")
        return redirect(url_for("goals.index"))

    deadline = None
    if deadline_str:
        try:
            # datetime-local format: YYYY-MM-DDTHH:MM
            deadline = datetime.fromisoformat(deadline_str)
        except ValueError:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": False, "error": "Invalid deadline format."}), 400
            flash("Invalid deadline format.", "error")
            return redirect(url_for("goals.index"))

    try:
        target_value = float(target_value) if target_value else None
        current_value = float(current_value) if current_value else 0.0
    except ValueError:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "error": "Values must be numbers."}), 400
        flash("Values must be numbers.", "error")
        return redirect(url_for("goals.index"))

    goal = Goal(
        user_id=current_user.id,
        title=title,
        description=description,
        target_value=target_value,
        current_value=current_value,
        unit=unit,
        category=category,
        deadline=deadline,
    )
    db.session.add(goal)
    db.session.commit()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({
            "success": True,
            "goal": {
                "id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "target_value": goal.target_value,
                "current_value": goal.current_value,
                "unit": goal.unit,
                "category": goal.category,
                "deadline": goal.deadline.isoformat() if goal.deadline else None,
                "progress_percent": goal.progress_percent
            }
        })

    flash("Goal created! Let's crush it! 🎯", "success")
    return redirect(url_for("goals.index"))


@goals_bp.route("/update/<int:goal_id>", methods=["POST"])
@login_required
def update(goal_id):
    goal = db.get_or_404(Goal, goal_id)
    if goal.user_id != current_user.id:
        flash("Not authorised.", "error")
        return redirect(url_for("goals.index"))

    new_value = request.form.get("current_value", "").strip()
    try:
        goal.current_value = float(new_value)
    except ValueError:
        flash("Invalid value.", "error")
        return redirect(url_for("goals.index"))

    if goal.target_value and goal.current_value >= goal.target_value:
        goal.mark_complete()
        flash(f"🎉 Goal '{goal.title}' completed!", "success")
    else:
        flash("Progress updated!", "success")

    db.session.commit()
    return redirect(url_for("goals.index"))


@goals_bp.route("/complete/<int:goal_id>", methods=["POST"])
@login_required
def complete(goal_id):
    goal = db.get_or_404(Goal, goal_id)
    if goal.user_id != current_user.id:
        flash("Not authorised.", "error")
        return redirect(url_for("goals.index"))
    goal.mark_complete()
    db.session.commit()
    flash(f"🎉 Goal '{goal.title}' marked complete!", "success")
    return redirect(url_for("goals.index"))


@goals_bp.route("/delete/<int:goal_id>", methods=["POST"])
@login_required
def delete(goal_id):
    goal = db.get_or_404(Goal, goal_id)
    if goal.user_id != current_user.id:
        flash("Not authorised.", "error")
        return redirect(url_for("goals.index"))
    db.session.delete(goal)
    db.session.commit()
    flash("Goal deleted.", "info")
    return redirect(url_for("goals.index"))
