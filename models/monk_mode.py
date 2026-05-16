"""
MONK MODE — 90 Day Rebirth Protocol (isolated module)

Core rule enforced:
- No pause / no skip.
- If the user misses EVEN ONE DAY, Monk Mode resets:
  - current day -> 1
  - streak -> 0
  - badges (Monk Mode badges) become locked again (implemented by monk_mode_progress reset)
  - daily progress becomes invalid (monk_mode_days marked reset)

This file contains ONLY Monk Mode isolated models/tables.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from extensions import db


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MonkModeProgress(db.Model):
    __tablename__ = "monk_mode_progress"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)

    # Activation / state
    started_at = db.Column(db.DateTime(timezone=True), nullable=True)
    status = db.Column(db.String(20), default="not_started")  # not_started, active, completed, reset

    # Day / streak state
    current_day = db.Column(db.Integer, default=1)  # 1..90 when active
    streak = db.Column(db.Integer, default=0)  # increments on each completed day (resets on miss)

    # Deadline anchor: the daily window is [deadline_at, deadline_at+24h)
    # We generate monk_mode_days with per-day deadline_at.
    timezone_label = db.Column(db.String(40), default="UTC")  # for transparency; server logic is UTC-safe

    # Timestamps
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=_utc_now,
        onupdate=_utc_now,
    )
    created_at = db.Column(db.DateTime(timezone=True), default=_utc_now)

    days = db.relationship("MonkModeDay", backref="progress", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<MonkModeProgress user_id={self.user_id} status={self.status} current_day={self.current_day}>"


class MonkModeDay(db.Model):
    __tablename__ = "monk_mode_days"

    id = db.Column(db.Integer, primary_key=True)
    progress_id = db.Column(db.Integer, db.ForeignKey("monk_mode_progress.id"), nullable=False, index=True)

    day_index = db.Column(db.Integer, nullable=False)  # 1..90
    # Daily window anchored at deadline_at; completion must happen before deadline_at+24h
    deadline_at = db.Column(db.DateTime(timezone=True), nullable=False)
    scheduled_date = db.Column(db.Date, nullable=False)  # UTC date portion of deadline_at

    status = db.Column(db.String(20), default="locked")  # locked, pending, completed, failed, reset

    # Completion record
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    failed_reason = db.Column(db.String(200), nullable=True)

    # Ensure per-day completion uniqueness
    __table_args__ = (
        db.UniqueConstraint("progress_id", "day_index", name="uq_monk_mode_day_progress_day"),
        db.Index("idx_monk_mode_day_progress_scheduled_date", "progress_id", "scheduled_date"),
    )

    def mark_completed(self, completed_at: datetime) -> None:
        self.status = "completed"
        self.completed_at = completed_at
        self.failed_reason = None

    def mark_failed(self, reason: str) -> None:
        self.status = "failed"
        self.failed_reason = reason


class MonkModeTask(db.Model):
    __tablename__ = "monk_mode_tasks"

    id = db.Column(db.Integer, primary_key=True)
    progress_id = db.Column(db.Integer, db.ForeignKey("monk_mode_progress.id"), nullable=False, index=True)

    day_index = db.Column(db.Integer, nullable=False)  # 1..90 for which day this task belongs
    task_key = db.Column(db.String(80), nullable=False)

    # Completion / failure
    is_required = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default="pending")  # pending, completed, failed, reset

    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # One completion attempt per task per day
    __table_args__ = (
        db.UniqueConstraint("progress_id", "day_index", "task_key", name="uq_monk_mode_task_progress_day_key"),
    )


class MonkModeBadge(db.Model):
    __tablename__ = "monk_mode_badges"

    id = db.Column(db.Integer, primary_key=True)
    progress_id = db.Column(db.Integer, db.ForeignKey("monk_mode_progress.id"), nullable=False, index=True)

    badge_key = db.Column(db.String(80), nullable=False)
    rarity = db.Column(db.String(20), default="common")  # common, rare, epic, legend

    earned_at = db.Column(db.DateTime(timezone=True), nullable=True)
    status = db.Column(db.String(20), default="locked")  # locked, unlocked

    __table_args__ = (
        db.UniqueConstraint("progress_id", "badge_key", name="uq_monk_mode_badge_progress_key"),
    )


class MonkModeLog(db.Model):
    __tablename__ = "monk_mode_logs"

    id = db.Column(db.Integer, primary_key=True)
    progress_id = db.Column(db.Integer, db.ForeignKey("monk_mode_progress.id"), nullable=False, index=True)

    action = db.Column(db.String(60), nullable=False)  # start, complete_task, complete_day, reset, fail
    message = db.Column(db.String(500), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), default=_utc_now, nullable=False)


class MonkModeReset(db.Model):
    __tablename__ = "monk_mode_resets"

    id = db.Column(db.Integer, primary_key=True)
    progress_id = db.Column(db.Integer, db.ForeignKey("monk_mode_progress.id"), nullable=False, index=True)

    reset_reason = db.Column(db.String(200), nullable=False)
    triggered_at = db.Column(db.DateTime(timezone=True), default=_utc_now, nullable=False)

    previous_current_day = db.Column(db.Integer, nullable=True)
    previous_streak = db.Column(db.Integer, nullable=True)


class MonkModeLevel(db.Model):
    """
    Stores user's current level and progression (derived from day completion milestones).
    """
    __tablename__ = "monk_mode_levels"

    id = db.Column(db.Integer, primary_key=True)
    progress_id = db.Column(db.Integer, db.ForeignKey("monk_mode_progress.id"), nullable=False, unique=True, index=True)

    level_key = db.Column(db.String(40), default="weak_mind")  # weak_mind..unrecognizable
    level_index = db.Column(db.Integer, default=1)  # 1..7
    progress_percent = db.Column(db.Integer, default=0)  # 0..100 of current level

    updated_at = db.Column(db.DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)
