from datetime import datetime, date, timezone
from extensions import db


class WorkoutLog(db.Model):
    """Records each individual exercise set a user completes."""
    __tablename__ = "workout_logs"

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    exercise_name = db.Column(db.String(120), nullable=False)
    logged_date   = db.Column(db.Date, default=date.today, nullable=False, index=True)
    sets_done     = db.Column(db.Integer, default=0)
    reps_done     = db.Column(db.String(40), default="")    # e.g. "12" or "30s"
    weight_kg     = db.Column(db.Float, nullable=True)      # null = bodyweight
    notes         = db.Column(db.String(255), default="")
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<WorkoutLog {self.exercise_name} {self.logged_date}>"

    @classmethod
    def personal_best(cls, user_id: int, exercise_name: str):
        """Return the max weight_kg ever logged for a given exercise."""
        result = (
            db.session.query(db.func.max(cls.weight_kg))
            .filter(cls.user_id == user_id, cls.exercise_name == exercise_name, cls.weight_kg.isnot(None))
            .scalar()
        )
        return result

    @classmethod
    def weekly_counts(cls, user_id: int, weeks: int = 8):
        """Return list of (date, count) per day for the last N weeks."""
        from datetime import timedelta
        cutoff = date.today() - timedelta(weeks=weeks)
        rows = (
            db.session.query(cls.logged_date, db.func.count(cls.id))
            .filter(cls.user_id == user_id, cls.logged_date >= cutoff)
            .group_by(cls.logged_date)
            .order_by(cls.logged_date)
            .all()
        )
        return rows

    @classmethod
    def today_logs(cls, user_id: int):
        """All exercise logs for today."""
        return cls.query.filter_by(user_id=user_id, logged_date=date.today()).all()
