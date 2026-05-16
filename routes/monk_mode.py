"""
MONK MODE routes — isolated module.

Security goals:
- Enforce completion server-side with UTC deadline windows.
- Prevent duplicate day submissions.
- Detect "missed even one day" by checking today's completion against the previous day.
- No frontend-only validation is trusted.

This module does NOT modify existing auth, workout, goals, or badge systems.
It only uses the new monk_mode_* tables.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta, date
from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, jsonify, redirect, render_template, request, url_for, current_app
from flask_login import current_user, login_required

from extensions import db
from models.monk_mode import (
    MonkModeProgress,
    MonkModeDay,
    MonkModeTask,
    MonkModeBadge,
    MonkModeLog,
    MonkModeReset,
    MonkModeLevel,
)

monk_mode_bp = Blueprint("monk_mode", __name__)


UTC = timezone.utc
MONK_TOTAL_DAYS = 90


# ----------------------------
# Helpers (UTC-safe)
# ----------------------------
def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_date(d: Optional[datetime] = None):
    dt = d or utc_now()
    return dt.date()


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def clamp_day_index(day_index: int) -> int:
    if day_index < 1:
        return 1
    if day_index > MONK_TOTAL_DAYS:
        return MONK_TOTAL_DAYS
    return day_index


def get_or_create_progress(user_id: int) -> MonkModeProgress:
    progress = MonkModeProgress.query.filter_by(user_id=user_id).first()
    if progress is None:
        progress = MonkModeProgress(user_id=user_id, status="not_started", current_day=1, streak=0)
        db.session.add(progress)
        db.session.commit()
    return progress


def compute_today_deadline_window(progress: MonkModeProgress) -> Tuple[datetime, datetime]:
    """
    We anchor each day's completion window to its own MonkModeDay.deadline_at.
    For "today", we pick the MonkModeDay row whose scheduled_date == today's UTC date.
    That row's deadline_at defines completion must occur before deadline_at+24h.

    If the row doesn't exist (fresh start not generated), it will be created on start.
    """
    today = utc_date()
    day = (
        MonkModeDay.query.join(MonkModeProgress, MonkModeDay.progress_id == MonkModeProgress.id)
        .filter(MonkModeProgress.user_id == progress.user_id, MonkModeDay.scheduled_date == today)
        .first()
    )
    if not day:
        raise ValueError("Monk Mode days not initialized (start required).")
    start = ensure_utc(day.deadline_at)
    end = start + timedelta(hours=24)
    return start, end


def get_day_row(progress: MonkModeProgress) -> MonkModeDay:
    today = utc_date()
    day = MonkModeDay.query.filter_by(progress_id=progress.id, scheduled_date=today).first()
    if not day:
        raise ValueError("Monk Mode day not found for today. (start/initialize required)")
    return day


def generate_daily_tasks_for_day(day_index: int) -> List[Tuple[str, bool]]:
    """
    Default mandatory tasks.
    Task keys are stable identifiers used for backend validation.
    """
    required_tasks = [
        ("workout_completed", True),
        ("cardio_completed", True),
        ("water_intake", True),
        ("protein_goal", True),
        ("calorie_target", True),
        ("sleep_target", True),
        ("meditation", True),
        ("reading", True),
        ("mindset_training", True),
        ("no_junk_food", True),
        ("no_sugary_drinks", True),
        ("no_smoking", True),
        ("no_alcohol", True),
        ("no_pornography", True),
        ("no_skipped_meals", True),
        ("social_media_limit", True),
    ]
    return required_tasks


def level_for_day(day_index: int) -> Tuple[str, int, int]:
    thresholds = [13, 26, 39, 52, 65, 78, 90]
    level_keys = [
        "weak_mind",
        "discipline_initiate",
        "focused_warrior",
        "iron_mind",
        "relentless",
        "ascended",
        "unrecognizable",
    ]
    level_index = 1
    for i, t in enumerate(thresholds):
        if day_index <= t:
            level_index = i + 1
            break
    level_key = level_keys[level_index - 1]

    prev_end = 0 if level_index == 1 else thresholds[level_index - 2]
    within = day_index - prev_end
    level_len = thresholds[level_index - 1] - prev_end
    progress_percent = int(round((within / level_len) * 100)) if level_len > 0 else 0
    return level_key, level_index, progress_percent


def award_monk_badges_for_day(progress: MonkModeProgress, day_completed_index: int) -> None:
    milestone_map = {
        7: ("day_7_survivor", "common", "Day 7 Survivor"),
        14: ("no_excuse_warrior", "common", "No Excuse Warrior"),
        30: ("silent_grinder", "rare", "Silent Grinder"),
        60: ("iron_discipline", "rare", "Iron Discipline"),
        75: ("reborn_mindset", "epic", "Reborn Mindset"),
        90: ("ascended_monk", "legend", "Ascended Monk"),
    }

    final_badge = (90, ("monk_mode_legend", "legend", "Monk Mode Legend"))

    targets = []
    if day_completed_index in milestone_map:
        targets.append(milestone_map[day_completed_index])
    if day_completed_index == final_badge[0]:
        targets.append(final_badge[1])

    for badge_key, rarity, _title in targets:
        existing = MonkModeBadge.query.filter_by(progress_id=progress.id, badge_key=badge_key).first()
        if existing:
            continue
        badge = MonkModeBadge(
            progress_id=progress.id,
            badge_key=badge_key,
            rarity=rarity,
            status="unlocked",
            earned_at=utc_now(),
        )
        db.session.add(badge)


def reset_moniker(progress: MonkModeProgress, reason: str) -> None:
    previous_current_day = progress.current_day
    previous_streak = progress.streak

    reset_row = MonkModeReset(
        progress_id=progress.id,
        reset_reason=reason[:200],
        previous_current_day=previous_current_day,
        previous_streak=previous_streak,
        triggered_at=utc_now(),
    )
    db.session.add(reset_row)

    MonkModeDay.query.filter_by(progress_id=progress.id).update(
        {"status": "reset", "completed_at": None, "failed_reason": None}
    )
    MonkModeTask.query.filter_by(progress_id=progress.id).update(
        {"status": "reset", "completed_at": None, "notes": None}
    )

    MonkModeBadge.query.filter_by(progress_id=progress.id).delete()

    progress.current_day = 1
    progress.streak = 0
    progress.status = "reset"
    progress.updated_at = utc_now()

    db.session.commit()


def ensure_days_and_tasks_initialized(progress: MonkModeProgress) -> None:
    existing_days = MonkModeDay.query.filter_by(progress_id=progress.id).count()
    if existing_days >= MONK_TOTAL_DAYS:
        return

    # Prevent IntegrityError if partial setup exists
    if existing_days > 0:
        MonkModeTask.query.filter_by(progress_id=progress.id).delete()
        MonkModeDay.query.filter_by(progress_id=progress.id).delete()
        db.session.commit()

    start_date = utc_date()
    today_midnight = datetime(start_date.year, start_date.month, start_date.day, tzinfo=UTC)

    for i in range(1, MONK_TOTAL_DAYS + 1):
        scheduled = start_date + timedelta(days=i - 1)
        deadline_at = datetime(scheduled.year, scheduled.month, scheduled.day, tzinfo=UTC)

        status = "pending" if i == 1 else "locked"
        day = MonkModeDay(
            progress_id=progress.id,
            day_index=i,
            deadline_at=deadline_at,
            scheduled_date=scheduled,
            status=status,
        )
        db.session.add(day)

    db.session.commit()

    days = MonkModeDay.query.filter_by(progress_id=progress.id).order_by(MonkModeDay.day_index.asc()).all()
    for day in days:
        tasks = generate_daily_tasks_for_day(day.day_index)
        for task_key, is_required in tasks:
            t = MonkModeTask(
                progress_id=progress.id,
                day_index=day.day_index,
                task_key=task_key,
                is_required=is_required,
                status="pending" if day.day_index == 1 else "locked",
            )
            db.session.add(t)

    db.session.commit()

    level = MonkModeLevel.query.filter_by(progress_id=progress.id).first()
    if level is None:
        level_key, level_index, pct = level_for_day(1)
        level = MonkModeLevel(
            progress_id=progress.id,
            level_key=level_key,
            level_index=level_index,
            progress_percent=pct,
        )
        db.session.add(level)
        db.session.commit()


@monk_mode_bp.route("/", methods=["GET"])
@login_required
def monk_board():
    progress = get_or_create_progress(current_user.id)

    if progress.status == "not_started":
        return render_template(
            "monk_mode/monk_board.html",
            monk={"status": "not_started", "current_day": 1, "streak": 0},
        )

    if MonkModeDay.query.filter_by(progress_id=progress.id).count() < MONK_TOTAL_DAYS:
        ensure_days_and_tasks_initialized(progress)

    today_day = None
    try:
        today_day = get_day_row(progress)
    except Exception:
        today_day = None

    days = MonkModeDay.query.filter_by(progress_id=progress.id).order_by(MonkModeDay.day_index.asc()).all()
    current_day_idx = progress.current_day

    level = MonkModeLevel.query.filter_by(progress_id=progress.id).first()
    if level is None:
        level_key, level_index, pct = level_for_day(progress.current_day)
        level = MonkModeLevel(
            progress_id=progress.id,
            level_key=level_key,
            level_index=level_index,
            progress_percent=pct,
        )
        db.session.add(level)
        db.session.commit()

    today_tasks = []
    if today_day:
        today_tasks = MonkModeTask.query.filter_by(progress_id=progress.id, day_index=today_day.day_index).order_by(
            MonkModeTask.task_key.asc()
        ).all()

    return render_template(
        "monk_mode/monk_board.html",
        monk={
            "status": progress.status,
            "current_day": current_day_idx,
            "streak": progress.streak,
            "today_day": {
                "day_index": today_day.day_index if today_day else None,
                "scheduled_date": today_day.scheduled_date.isoformat() if today_day and today_day.scheduled_date else None,
                "status": today_day.status if today_day else None,
                "deadline_at": today_day.deadline_at.isoformat() if today_day and today_day.deadline_at else None,
            }
            if today_day
            else None,
            "days": [
                {
                    "day_index": d.day_index,
                    "status": d.status,
                    "completed_at": d.completed_at.isoformat() if d.completed_at else None,
                    "failed_reason": d.failed_reason,
                    "scheduled_date": d.scheduled_date.isoformat() if d.scheduled_date else None,
                }
                for d in days
            ],
            "tasks": [
                {
                    "task_key": t.task_key,
                    "is_required": t.is_required,
                    "status": t.status,
                    "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                    "notes": t.notes,
                }
                for t in today_tasks
            ],
            "level": {
                "level_key": level.level_key,
                "level_index": level.level_index,
                "progress_percent": level.progress_percent,
            },
        },
    )


@monk_mode_bp.route("/embed", methods=["GET"])
@login_required
def monk_embed():
    """
    Dashboard-embedded fragment.
    Avoids changing routes/dashboard.py by fetching this HTML block via include-free render.
    """
    progress = get_or_create_progress(current_user.id)
    if progress.status == "not_started":
        return render_template("monk_mode/monk_embed.html", monk={"status": "not_started"})
    if MonkModeDay.query.filter_by(progress_id=progress.id).count() < MONK_TOTAL_DAYS:
        ensure_days_and_tasks_initialized(progress)

    try:
        today_day = get_day_row(progress)
    except Exception:
        today_day = None

    days = MonkModeDay.query.filter_by(progress_id=progress.id).order_by(MonkModeDay.day_index.asc()).all()

    today_tasks = []
    if today_day:
        today_tasks = MonkModeTask.query.filter_by(progress_id=progress.id, day_index=today_day.day_index).order_by(
            MonkModeTask.task_key.asc()
        ).all()

    level = MonkModeLevel.query.filter_by(progress_id=progress.id).first()
    if level is None:
        level_key, level_index, pct = level_for_day(progress.current_day)
        level = MonkModeLevel(
            progress_id=progress.id,
            level_key=level_key,
            level_index=level_index,
            progress_percent=pct,
        )
        db.session.add(level)
        db.session.commit()

    return render_template(
        "monk_mode/monk_embed.html",
        monk={
            "status": progress.status,
            "current_day": progress.current_day,
            "streak": progress.streak,
            "today_day": {
                "day_index": today_day.day_index if today_day else None,
                "deadline_at": today_day.deadline_at.isoformat() if today_day and today_day.deadline_at else None,
                "status": today_day.status if today_day else None,
            }
            if today_day
            else None,
            "days": [
                {"day_index": d.day_index, "status": d.status, "completed_at": d.completed_at.isoformat() if d.completed_at else None}
                for d in days
            ],
            "tasks": [
                {
                    "task_key": t.task_key,
                    "status": t.status,
                    "notes": t.notes,
                }
                for t in today_tasks
            ],
            "level": {
                "level_key": level.level_key,
                "level_index": level.level_index,
                "progress_percent": level.progress_percent,
            },
        },
    )


@monk_mode_bp.route("/start", methods=["POST"])
@login_required
def monk_start():
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    user_id = current_user.id

    progress = get_or_create_progress(user_id)

    if progress.status == "active":
        return jsonify({"ok": True, "status": "already_active"}), 200

    MonkModeBadge.query.filter_by(progress_id=progress.id).delete()
    MonkModeTask.query.filter_by(progress_id=progress.id).delete()
    MonkModeDay.query.filter_by(progress_id=progress.id).delete()

    progress.status = "active"
    progress.current_day = 1
    progress.streak = 0
    progress.started_at = utc_now()
    progress.updated_at = utc_now()

    level = MonkModeLevel.query.filter_by(progress_id=progress.id).first()
    if level:
        level.level_key, level.level_index, level.progress_percent = level_for_day(1)
        db.session.add(level)

    db.session.commit()
    ensure_days_and_tasks_initialized(progress)

    db.session.add(MonkModeLog(progress_id=progress.id, action="start", message="Monk Mode started"))
    db.session.commit()

    return jsonify({"ok": True, "status": "started", "current_day": 1, "streak": 0}), 200


@monk_mode_bp.route("/complete-day", methods=["POST"])
@login_required
def complete_day():
    progress = get_or_create_progress(current_user.id)
    if progress.status != "active":
        return jsonify({"ok": False, "error": "Monk Mode not active"}), 409

    try:
        today_day = get_day_row(progress)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 409

    if today_day.status not in ("pending", "reset", "locked", "completed"):
        today_day.status = "pending"
    if today_day.day_index != progress.current_day:
        reset_moniker(progress, reason="Out-of-order completion attempt")
        db.session.add(MonkModeLog(progress_id=progress.id, action="fail", message="Out-of-order completion attempt"))
        db.session.commit()
        return jsonify({"ok": False, "error": "Failed: out-of-order day"}), 400

    _, deadline_end = compute_today_deadline_window(progress)
    now = utc_now()
    if now >= deadline_end:
        reset_moniker(progress, reason="Missed 24h deadline for today")
        db.session.add(MonkModeLog(progress_id=progress.id, action="fail", message="Missed 24h deadline"))
        db.session.commit()
        return jsonify({"ok": False, "error": "Failed: missed deadline"}), 400

    if today_day.status == "completed":
        return jsonify({"ok": False, "error": "Already completed today"}), 409

    if progress.current_day > 1:
        prev_scheduled = utc_date(today_day.deadline_at) - timedelta(days=1)
        prev_day = MonkModeDay.query.filter_by(progress_id=progress.id, scheduled_date=prev_scheduled).first()
        if not prev_day or prev_day.status != "completed":
            reset_moniker(progress, reason="Missed previous day (contract broken)")
            db.session.add(MonkModeLog(progress_id=progress.id, action="fail", message="Missed previous day"))
            db.session.commit()
            return jsonify({"ok": False, "error": "Failed: missed a previous day"}), 400

    required_tasks = MonkModeTask.query.filter_by(
        progress_id=progress.id, day_index=today_day.day_index, is_required=True
    ).all()
    if not required_tasks:
        return jsonify({"ok": False, "error": "No tasks configured for today"}), 500

    incomplete = [t.task_key for t in required_tasks if t.status != "completed"]
    if incomplete:
        return jsonify({"ok": False, "error": "Incomplete mandatory tasks", "incomplete": incomplete}), 400

    today_day.mark_completed(completed_at=now)
    progress.streak += 1
    progress.current_day = clamp_day_index(progress.current_day + 1) if progress.current_day < MONK_TOTAL_DAYS else MONK_TOTAL_DAYS

    today_level_key, today_level_index, today_pct = level_for_day(progress.current_day)
    level = MonkModeLevel.query.filter_by(progress_id=progress.id).first()
    if not level:
        level = MonkModeLevel(progress_id=progress.id, level_key=today_level_key, level_index=today_level_index, progress_percent=today_pct)
        db.session.add(level)
    else:
        level.level_key = today_level_key
        level.level_index = today_level_index
        level.progress_percent = today_pct

    next_day_index = today_day.day_index + 1
    if next_day_index <= MONK_TOTAL_DAYS:
        next_day = MonkModeDay.query.filter_by(progress_id=progress.id, day_index=next_day_index).first()
        if next_day:
            next_day.status = "pending"
        MonkModeTask.query.filter_by(progress_id=progress.id, day_index=next_day_index).update({"status": "pending"})

    db.session.add(MonkModeLog(progress_id=progress.id, action="complete_day", message=f"Completed day {today_day.day_index}"))
    db.session.commit()

    award_monk_badges_for_day(progress, day_completed_index=today_day.day_index)
    db.session.commit()

    return jsonify(
        {
            "ok": True,
            "completed_day": today_day.day_index,
            "next_current_day": progress.current_day,
            "streak": progress.streak,
            "level": {"level_key": level.level_key, "level_index": level.level_index, "progress_percent": level.progress_percent},
        }
    )


@monk_mode_bp.route("/complete-task", methods=["POST"])
@login_required
def complete_task():
    try:
        payload: Dict[str, Any] = request.get_json(silent=True) or {}
        task_key = payload.get("task_key")
        notes = payload.get("notes")

        if not isinstance(task_key, str) or not task_key.strip():
            return jsonify({"ok": False, "error": "task_key required"}), 400

        progress = get_or_create_progress(current_user.id)
        if progress.status != "active":
            return jsonify({"ok": False, "error": "Monk Mode not active"}), 409

        try:
            today_day = get_day_row(progress)
        except Exception as e:
            return jsonify({"ok": False, "error": f"Day lookup failed: {e}"}), 409

        try:
            _, deadline_end = compute_today_deadline_window(progress)
        except Exception as e:
            return jsonify({"ok": False, "error": f"Deadline calc failed: {e}"}), 409

        now = utc_now()
        if now >= ensure_utc(deadline_end):
            reset_moniker(progress, reason="Missed 24h deadline (task completion too late)")
            db.session.add(MonkModeLog(progress_id=progress.id, action="fail", message="Missed 24h deadline (task)"))
            db.session.commit()
            return jsonify({"ok": False, "error": "Failed: missed deadline"}), 400

        if today_day.day_index != progress.current_day:
            return jsonify({"ok": False, "error": "Failed: out-of-order day"}), 400

        task = MonkModeTask.query.filter_by(progress_id=progress.id, day_index=today_day.day_index, task_key=task_key).first()
        if not task:
            return jsonify({"ok": False, "error": "Task not found"}), 404

        if task.status == "completed":
            return jsonify({"ok": True, "status": "already_completed"}), 200

        task.status = "completed"
        task.completed_at = now
        task.notes = notes if isinstance(notes, str) else None

        db.session.add(MonkModeLog(progress_id=progress.id, action="complete_task", message=f"Completed task: {task_key}"))
        db.session.commit()

        return jsonify({"ok": True, "task_key": task_key, "status": "completed"}), 200
    except Exception as exc:
        current_app.logger.exception("complete_task crashed")
        return jsonify({"ok": False, "error": f"Server error: {exc}"}), 500




@monk_mode_bp.route("/status", methods=["GET"])
@login_required
def status():
    try:
        progress = get_or_create_progress(current_user.id)
        if progress.status != "active":
            return jsonify({"ok": True, "status": progress.status})

        if MonkModeDay.query.filter_by(progress_id=progress.id).count() < MONK_TOTAL_DAYS:
            ensure_days_and_tasks_initialized(progress)

        level = MonkModeLevel.query.filter_by(progress_id=progress.id).first()
        
        # AAA Touches: Dynamic Mission Focus & Quotes
        mission_focus = [
            "Initiation Phase", "Neural Re-wiring", "Silent Warfare", 
            "The Breaking Point", "Iron Foundations", "Stoic Resilience",
            "The Void Walk", "Neural Optimization", "Final Ascension"
        ][min((progress.current_day - 1) // 10, 8)]
        
        quotes = [
            "Discipline is the bridge between goals and accomplishment.",
            "He who has a why to live can bear almost any how.",
            "Freedom is found in the discipline of the self.",
            "The soul is dyed the color of its thoughts. Keep them pure.",
            "Suffer the pain of discipline or suffer the pain of regret.",
            "Silence is the ultimate weapon of the wise.",
            "A monk is not one who avoids the world, but one who masters it.",
            "Victory belongs to the most persevering.",
            "The transformation is nearly complete. Do not falter."
        ]
        protocol_quote = quotes[min((progress.current_day - 1) // 10, 8)]

        return jsonify(
            {
                "ok": True,
                "status": progress.status,
                "current_day": progress.current_day,
                "streak": progress.streak,
                "mission_focus": mission_focus,
                "protocol_quote": protocol_quote,
                "today": {"day_index": today_day.day_index if today_day else None, "status": today_day.status if today_day else None},
                "tasks": [
                    {"task_key": t.task_key, "status": t.status, "completed_at": t.completed_at.isoformat() if t.completed_at else None}
                    for t in current_tasks
                ],
                "level": {
                    "level_key": level.level_key if level else "weak_mind",
                    "level_index": level.level_index if level else 1,
                    "progress_percent": level.progress_percent if level else 0,
                },
            }
        )
    except Exception as e:
        current_app.logger.exception("Monk status failed")
        return jsonify({"ok": False, "error": f"Server error: {e}"}), 500


# ---------------------------------------------------------------------------
# Multi-page MONK MODE UX flow (to mirror 30-day challenge-style pages)
# ---------------------------------------------------------------------------

def _monk_page_base_context(progress: MonkModeProgress) -> Dict[str, Any]:
    """
    Shared context for all Monk pages. Does not mutate state.
    """
    if progress.status == "not_started":
        return {
            "monk_status": "not_started",
            "monk_current_day": 1,
            "monk_streak": 0,
            "level": {"level_key": "weak_mind", "level_index": 1, "progress_percent": 0},
        }

    # Ensure grid rows exist (safe to call)
    if MonkModeDay.query.filter_by(progress_id=progress.id).count() < MONK_TOTAL_DAYS:
        ensure_days_and_tasks_initialized(progress)

    level = MonkModeLevel.query.filter_by(progress_id=progress.id).first()
    if not level:
        level_key, level_index, pct = level_for_day(progress.current_day)
        level = MonkModeLevel(
            progress_id=progress.id,
            level_key=level_key,
            level_index=level_index,
            progress_percent=pct,
        )
        db.session.add(level)
        db.session.commit()

    return {
        "monk_status": progress.status,
        "monk_current_day": progress.current_day,
        "monk_streak": progress.streak,
        "level": {
            "level_key": level.level_key,
            "level_index": level.level_index,
            "progress_percent": level.progress_percent,
        },
    }


@monk_mode_bp.route("/page/start", methods=["GET"])
@login_required
def monk_start_page():
    try:
        progress = get_or_create_progress(current_user.id)

        # If already active, send user to the current day page.
        if progress.status == "active":
            return redirect(url_for("monk_mode.monk_day_detail", day_index=progress.current_day))

        ctx = _monk_page_base_context(progress)
        return render_template("monk_mode/monk_page_start.html", **ctx)
    except Exception as exc:
        current_app.logger.exception("Monk Mode page/start failed")
        raise exc


@monk_mode_bp.route("/page/days", methods=["GET"])
@login_required
def monk_days_page():
    try:
        progress = get_or_create_progress(current_user.id)

        if progress.status != "active":
            return redirect(url_for("monk_mode.monk_start_page"))

        if MonkModeDay.query.filter_by(progress_id=progress.id).count() < MONK_TOTAL_DAYS:
            ensure_days_and_tasks_initialized(progress)

        today = utc_date()
        days = MonkModeDay.query.filter_by(progress_id=progress.id).order_by(MonkModeDay.day_index.asc()).all()

        ctx = _monk_page_base_context(progress)
        ctx.update(
            {
                "today_scheduled_date": today.isoformat(),
                "days": [
                    {
                        "day_index": d.day_index,
                        "status": d.status,
                        "completed_at": d.completed_at.isoformat() if d.completed_at else None,
                        "scheduled_date": d.scheduled_date.isoformat() if d.scheduled_date else None,
                        "deadline_at": d.deadline_at.isoformat() if d.deadline_at else None,
                    }
                    for d in days
                ],
            }
        )
        return render_template("monk_mode/monk_page_days.html", **ctx)
    except Exception as exc:
        current_app.logger.exception("Monk Mode page/days failed")
        raise exc


@monk_mode_bp.route("/page/day/<int:day_index>", methods=["GET"])
@login_required
def monk_day_detail(day_index: int):
    try:
        progress = get_or_create_progress(current_user.id)
        if progress.status != "active":
            return redirect(url_for("monk_mode.monk_start_page"))

        day_index = clamp_day_index(day_index)

        if MonkModeDay.query.filter_by(progress_id=progress.id).count() < MONK_TOTAL_DAYS:
            ensure_days_and_tasks_initialized(progress)

        day = MonkModeDay.query.filter_by(progress_id=progress.id, day_index=day_index).first()
        if not day:
            return render_template("errors/404.html"), 404

        tasks = MonkModeTask.query.filter_by(progress_id=progress.id, day_index=day_index).order_by(MonkModeTask.task_key.asc()).all()

        ctx = _monk_page_base_context(progress)
        ctx.update(
            {
                "day": {
                    "day_index": day.day_index,
                    "status": day.status,
                    "scheduled_date": day.scheduled_date.isoformat() if day.scheduled_date else None,
                    "deadline_at": day.deadline_at.isoformat() if day.deadline_at else None,
                    "completed_at": day.completed_at.isoformat() if day.completed_at else None,
                    "failed_reason": day.failed_reason,
                },
                "tasks": [
                    {
                        "task_key": t.task_key,
                        "is_required": t.is_required,
                        "status": t.status,
                        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                        "notes": t.notes,
                    }
                    for t in tasks
                ],
            }
        )
        return render_template("monk_mode/monk_page_day_detail.html", **ctx)
    except Exception as exc:
        current_app.logger.exception("Monk Mode page/day/<day_index> failed")
        raise exc


@monk_mode_bp.route("/page/settings", methods=["GET"])
@login_required
def monk_settings_page():
    try:
        progress = get_or_create_progress(current_user.id)

        ctx = _monk_page_base_context(progress)
        return render_template("monk_mode/monk_page_settings.html", **ctx)
    except Exception as exc:
        current_app.logger.exception("Monk Mode page/settings failed")
        raise exc
