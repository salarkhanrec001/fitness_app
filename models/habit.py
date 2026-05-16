"""
Habit & HabitLog Models
Tracks habits, daily check-ins, and bad habits with 30-day challenges.
Ported from Motivaura.
"""

from datetime import datetime, timezone, date
from extensions import db


class Habit(db.Model):
    __tablename__ = 'habits'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default='')
    is_bad_habit = db.Column(db.Boolean, default=False)
    frequency = db.Column(db.String(20), default='daily')  # daily, weekly
    color = db.Column(db.String(7), default='#6366f1')  # hex color for UI
    icon = db.Column(db.String(50), default='⭐')

    # Streak tracking
    current_streak = db.Column(db.Integer, default=0)
    best_streak = db.Column(db.Integer, default=0)
    total_completions = db.Column(db.Integer, default=0)

    # 30-day challenge
    challenge_days = db.Column(db.Integer, default=30)  # target days to break habit
    challenge_start = db.Column(db.DateTime, nullable=True)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    logs = db.relationship('HabitLog', backref='habit', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def completed_today(self):
        """Check if this habit was completed today."""
        today = date.today()
        return self.logs.filter(
            db.func.date(HabitLog.logged_at) == today
        ).first() is not None

    @property
    def streak_display(self):
        """Display streak with fire emoji."""
        if self.current_streak > 0:
            return f'🔥 {self.current_streak}'
        return '0'

    @property
    def challenge_progress(self):
        """Progress percentage for 30-day challenge (bad habits only)."""
        if not self.is_bad_habit or not self.challenge_days:
            return 0
        return min(100, round((self.current_streak / self.challenge_days) * 100))

    @property
    def challenge_days_remaining(self):
        """Days left to complete the challenge."""
        if not self.is_bad_habit:
            return 0
        remaining = self.challenge_days - self.current_streak
        return max(0, remaining)

    @property
    def challenge_completed(self):
        """Whether the 30-day challenge is complete."""
        return self.is_bad_habit and self.current_streak >= self.challenge_days

    def to_dict(self):
        """Serialize habit for JSON responses."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_bad_habit': self.is_bad_habit,
            'frequency': self.frequency,
            'color': self.color,
            'icon': self.icon,
            'current_streak': self.current_streak,
            'best_streak': self.best_streak,
            'total_completions': self.total_completions,
            'completed_today': self.completed_today,
            'is_active': self.is_active,
            'challenge_days': self.challenge_days,
            'challenge_progress': self.challenge_progress,
            'challenge_days_remaining': self.challenge_days_remaining,
            'challenge_completed': self.challenge_completed,
        }

    def __repr__(self):
        return f'<Habit {self.name}>'


class HabitLog(db.Model):
    __tablename__ = 'habit_logs'

    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habits.id', ondelete='CASCADE'), nullable=False)
    logged_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    note = db.Column(db.String(255), default='')

    def __repr__(self):
        return f'<HabitLog habit={self.habit_id} date={self.logged_at}>'
