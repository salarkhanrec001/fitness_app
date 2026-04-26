from datetime import datetime, timezone
from extensions import db


class FitnessPlan(db.Model):
    __tablename__ = "fitness_plans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    plan_json = db.Column(db.Text, nullable=True)   # JSON string of weekly plan
    goal = db.Column(db.String(100), nullable=True)
    experience_level = db.Column(db.String(50), nullable=True)
    weeks_duration = db.Column(db.Integer, default=4)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def deactivate_others(self):
        """Deactivate all other plans for this user."""
        FitnessPlan.query.filter(
            FitnessPlan.user_id == self.user_id,
            FitnessPlan.id != self.id
        ).update({"is_active": False})

    def __repr__(self):
        return f"<FitnessPlan {self.title}>"
