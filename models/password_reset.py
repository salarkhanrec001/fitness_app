import random
import string
from datetime import datetime, timedelta, timezone
from extensions import db


def _generate_otp():
    return "".join(random.choices(string.digits, k=6))


class PasswordReset(db.Model):
    __tablename__ = "password_resets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    otp = db.Column(db.String(6), nullable=False, default=_generate_otp)
    is_used = db.Column(db.Boolean, default=False)
    expires_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc) + timedelta(minutes=15),
    )
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def is_expired(self):
        # expires_at is stored as naive UTC; compare with naive utcnow() to avoid
        # TypeError from mixing aware and naive datetimes (common SQLite gotcha).
        naive_now = datetime.utcnow()
        expires = self.expires_at
        if expires.tzinfo is not None:
            expires = expires.replace(tzinfo=None)
        return naive_now > expires

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired

    def __repr__(self):
        return f"<PasswordReset user_id={self.user_id} otp={self.otp}>"
