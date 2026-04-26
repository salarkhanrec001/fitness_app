from datetime import datetime, timezone
from extensions import db


class Goal(db.Model):
    __tablename__ = "goals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    target_value = db.Column(db.Float, nullable=True)   # e.g. target weight, reps
    current_value = db.Column(db.Float, default=0.0)
    unit = db.Column(db.String(30), nullable=True)      # kg, reps, km, minutes
    category = db.Column(db.String(50), nullable=True)  # weight, strength, cardio, habit
    deadline = db.Column(db.DateTime, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)

    @property
    def progress_percent(self):
        """Return integer 0-100 progress percentage."""
        if not self.target_value or self.target_value == 0:
            return 0
        pct = (self.current_value / self.target_value) * 100
        return min(int(pct), 100)

    def mark_complete(self):
        self.is_completed = True
        self.current_value = self.target_value
        self.completed_at = datetime.now(timezone.utc)

    def __repr__(self):
        return f"<Goal {self.title}>"
