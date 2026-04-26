from datetime import datetime, date, timezone
from extensions import db


class Streak(db.Model):
    __tablename__ = "streaks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_activity_date = db.Column(db.Date, nullable=True)
    total_workouts = db.Column(db.Integer, default=0)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def log_activity(self):
        """Call this every time a user completes a workout."""
        today = date.today()
        if self.last_activity_date is None:
            self.current_streak = 1
        elif self.last_activity_date == today:
            # Already logged today — no change
            return
        elif (today - self.last_activity_date).days == 1:
            # Consecutive day
            self.current_streak += 1
        else:
            # Streak broken
            self.current_streak = 1

        self.last_activity_date = today
        self.total_workouts += 1

        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak

    @property
    def display_streak(self):
        """Returns the current streak if it's still valid (today or yesterday), otherwise 0."""
        if not self.last_activity_date:
            return 0
        days_diff = (date.today() - self.last_activity_date).days
        return self.current_streak if days_diff <= 1 else 0

    @property
    def is_active_today(self):
        return self.last_activity_date == date.today()

    def __repr__(self):
        return f"<Streak user_id={self.user_id} current={self.current_streak}>"
