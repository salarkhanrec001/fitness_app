from datetime import date, timedelta
from flask import Blueprint, render_template, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models.goal import Goal
from models.streak import Streak
from models.workout_log import WorkoutLog
from models.weight_log import WeightLog

dashboard_bp = Blueprint("dashboard", __name__)


def _weekly_workout_data(streak, weeks=8):
    """Build last-N-weeks workout-day counts from real WorkoutLog entries."""
    from datetime import datetime, timezone
    labels, counts = [], []
    # Use UTC date to ensure consistency across different server locations
    today = datetime.now(timezone.utc).date()
    current_week_start = today - timedelta(days=today.weekday())
    first_week_start = current_week_start - timedelta(weeks=weeks - 1)
    last_week_end = current_week_start + timedelta(days=6)

    logs = (
        WorkoutLog.query.filter(
            WorkoutLog.user_id == current_user.id,
            WorkoutLog.logged_date >= first_week_start,
            WorkoutLog.logged_date <= last_week_end,
        )
        .all()
    )

    workout_days_by_week = [set() for _ in range(weeks)]
    for log in logs:
        week_index = (log.logged_date - first_week_start).days // 7
        if 0 <= week_index < weeks:
            workout_days_by_week[week_index].add(log.logged_date)

    for i in range(weeks):
        week_start = first_week_start + timedelta(weeks=i)
        
        # Make labels more intuitive
        if i == weeks - 1:
            label = "This Week"
        elif i == weeks - 2:
            label = "Last Week"
        else:
            label = week_start.strftime("%b %d")
            
        labels.append(label)
        counts.append(len(workout_days_by_week[i]))

    return labels, counts


def _weekly_workout_plan(active_plan, user_id=None):
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    experience = (getattr(active_plan, "experience_level", "") or "beginner").strip().lower()

    templates = {
        "beginner": [
            ("Full body", "Build a strong foundation", "workout"),
            ("Mobility", "Recovery and light movement", "recovery"),
            ("Lower body", "Focus on legs and core", "workout"),
            ("Mobility", "Stretch and reset", "recovery"),
            ("Cardio", "A short conditioning session", "workout"),
            ("Active recovery", "Easy walk or mobility flow", "recovery"),
            ("Rest", "Recharge for next week", "rest"),
        ],
        "intermediate": [
            ("Push strength", "Chest, shoulders, and triceps", "workout"),
            ("Conditioning", "Cardio and intervals", "workout"),
            ("Pull strength", "Back and biceps focus", "workout"),
            ("Mobility", "Let your body recover", "recovery"),
            ("Leg day", "Lower-body strength work", "workout"),
            ("Core + finishers", "Short high-energy session", "workout"),
            ("Rest", "Full recovery day", "rest"),
        ],
        "advanced": [
            ("Strength", "Heavy compound lifts", "workout"),
            ("HIIT", "Fast-paced conditioning", "workout"),
            ("Upper body", "Volume and control", "workout"),
            ("Lower body", "Strength and power", "workout"),
            ("Conditioning", "Athletic endurance work", "workout"),
            ("Mobility", "Recovery and joint health", "recovery"),
            ("Rest", "Full recovery day", "rest"),
        ],
        "six_pack": [
            ("Core ignition", "High-rep crunches and planks", "workout"),
            ("HIIT Abs", "Cardio bursts with core work", "workout"),
            ("Lower abs focus", "Leg raises and mountain climbers", "workout"),
            ("Mobility", "Stretch and recover", "recovery"),
            ("Oblique blast", "Russian twists and bicycles", "workout"),
            ("Core endurance", "Long-hold planks and holds", "workout"),
            ("Rest", "Full core recovery", "rest"),
        ],
    }

    from datetime import datetime, timezone
    schedule = templates.get(experience, templates["beginner"])
    # Use UTC date for consistent "Today" marker
    today = datetime.now(timezone.utc).date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    completed_dates = set()

    if user_id is not None:
        logs = (
            WorkoutLog.query.filter(
                WorkoutLog.user_id == user_id,
                WorkoutLog.logged_date >= week_start,
                WorkoutLog.logged_date <= week_end,
            )
            .all()
        )
        completed_dates = {log.logged_date.isoformat() for log in logs}

    roadmap = []
    for idx, day in enumerate(weekdays):
        session_date = week_start + timedelta(days=idx)
        title, note, kind = schedule[idx]
        roadmap.append(
            {
                "day": day,
                "date_label": session_date.strftime("%b %d"),
                "date_iso": session_date.isoformat(),
                "title": title,
                "note": note,
                "kind": kind,
                "is_today": session_date == today,
                "is_completed": session_date.isoformat() in completed_dates,
            }
        )

    today_focus = next((day for day in roadmap if day["is_today"]), roadmap[0])
    next_workout = next(
        (
            day
            for day in roadmap[today.weekday() :]
            if day["kind"] != "rest" and not day["is_completed"]
        ),
        None,
    )
    if next_workout is None:
        next_workout = next((day for day in roadmap if day["kind"] != "rest"), today_focus)

    completed_sessions = sum(1 for day in roadmap if day["kind"] != "rest" and day["is_completed"])
    scheduled_sessions = sum(1 for day in roadmap if day["kind"] != "rest")

    return roadmap, today_focus, next_workout, completed_sessions, scheduled_sessions


@dashboard_bp.route("/")
@login_required
def index():
    if not current_user.onboarding_complete:
        return redirect(url_for("onboarding.step1"))

    profile      = current_user.profile
    active_plan  = current_user.get_active_plan()
    streak       = Streak.query.filter_by(user_id=current_user.id).first()
    goals        = Goal.query.filter_by(user_id=current_user.id, is_completed=False).limit(4).all()
    completed_goals = Goal.query.filter_by(user_id=current_user.id, is_completed=True).count()

    # Analytics data for Chart.js
    chart_labels, chart_workouts = _weekly_workout_data(streak)
    weekly_roadmap, weekly_today, weekly_next_workout, weekly_completed_sessions, weekly_scheduled_sessions = _weekly_workout_plan(active_plan, current_user.id)
    weekly_progress_percent = round((weekly_completed_sessions / weekly_scheduled_sessions) * 100) if weekly_scheduled_sessions else 0

    # Weight trend — real measurements from WeightLog
    weight_logs = WeightLog.recent_for_user(current_user.id, limit=8)
    weight_labels = [log.recorded_at.strftime("%b %d") for log in weight_logs]
    weight_data = [float(log.weight_kg) for log in weight_logs]

    # Phase 2: Proactive AI Insights
    from services.gemini_service import get_proactive_insight
    coach_insight = get_proactive_insight(current_user, profile)

    # Lightweight Monk Mode status for dashboard card only
    monk_status = "not_started"
    monk_current_day = 1
    monk_streak = 0
    try:
        from models.monk_mode import MonkModeProgress
        progress = MonkModeProgress.query.filter_by(user_id=current_user.id).first()
        if progress:
            monk_status = progress.status
            monk_current_day = progress.current_day or 1
            monk_streak = progress.streak or 0
    except Exception:
        pass

    return render_template(
        "dashboard.html",
        profile=profile,
        active_plan=active_plan,
        streak=streak,
        goals=goals,
        completed_goals=completed_goals,
        chart_labels=chart_labels,
        chart_workouts=chart_workouts,
        weight_labels=weight_labels,
        weight_data=weight_data,
        weekly_roadmap=weekly_roadmap,
        weekly_today=weekly_today,
        weekly_next_workout=weekly_next_workout,
        weekly_completed_sessions=weekly_completed_sessions,
        weekly_scheduled_sessions=weekly_scheduled_sessions,
        weekly_progress_percent=weekly_progress_percent,
        monk_status=monk_status,
        monk_current_day=monk_current_day,
        monk_streak=monk_streak,
    )
