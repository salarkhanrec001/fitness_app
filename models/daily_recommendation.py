"""
models/daily_recommendation.py
Caches per-user daily AI recommendations to avoid redundant API calls.
"""
import json
from datetime import datetime, date, timezone
from extensions import db


class DailyRecommendation(db.Model):
    __tablename__ = "daily_recommendations"

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date         = db.Column(db.Date, nullable=False, default=date.today)
    workout_json = db.Column(db.Text, nullable=True)    # JSON list of exercises
    meal_json    = db.Column(db.Text, nullable=True)    # JSON meal plan dict
    tips_json    = db.Column(db.Text, nullable=True)    # JSON list of tips
    workout_title= db.Column(db.String(200), nullable=True)
    workout_notes= db.Column(db.Text, nullable=True)
    generated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint("user_id", "date", name="unique_user_daily"),
    )

    @property
    def workout(self):
        return json.loads(self.workout_json or "[]")

    @property
    def meal_plan(self):
        return json.loads(self.meal_json or "{}")

    @property
    def tips(self):
        return json.loads(self.tips_json or "[]")

    @classmethod
    def get_today(cls, user_id: int):
        return cls.query.filter_by(user_id=user_id, date=date.today()).first()

    @classmethod
    def create_from_data(cls, user_id: int, data: dict):
        """Create (or replace) today's recommendation from AI-returned dict."""
        # Delete stale record if exists
        existing = cls.get_today(user_id)
        if existing:
            db.session.delete(existing)
            db.session.flush()

        rec = cls(
            user_id       = user_id,
            date          = date.today(),
            workout_json  = json.dumps(data.get("workout", [])),
            meal_json     = json.dumps(data.get("meal_plan", {})),
            tips_json     = json.dumps(data.get("tips", [])),
            workout_title = data.get("workout_title", "Today's Workout"),
            workout_notes = data.get("workout_notes", ""),
        )
        db.session.add(rec)
        db.session.commit()
        return rec

    def __repr__(self):
        return f"<DailyRecommendation user_id={self.user_id} date={self.date}>"
