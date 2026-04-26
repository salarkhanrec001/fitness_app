from datetime import datetime, timezone

from extensions import db


class WeightLog(db.Model):
    """Records a user's weight measurements over time."""

    __tablename__ = "weight_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    weight_kg = db.Column(db.Float, nullable=False)
    recorded_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    def __repr__(self):
        return f"<WeightLog user_id={self.user_id} weight_kg={self.weight_kg} recorded_at={self.recorded_at}>"

    @classmethod
    def recent_for_user(cls, user_id: int, limit: int = 8):
        """Return the most recent weight entries for a user in chronological order."""
        return (
            cls.query.filter_by(user_id=user_id)
            .order_by(cls.recorded_at.desc())
            .limit(limit)
            .all()
        )[::-1]
