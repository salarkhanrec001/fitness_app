from datetime import datetime, timezone
from extensions import db


class Friend(db.Model):
    """Confirmed friendship (bidirectional record)."""
    __tablename__ = "friends"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint("user_id", "friend_id", name="unique_friendship"),)

    def __repr__(self):
        return f"<Friend {self.user_id} <-> {self.friend_id}>"


class FriendRequest(db.Model):
    """Pending friend request."""
    __tablename__ = "friend_requests"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint("sender_id", "receiver_id", name="unique_friend_request"),)

    def __repr__(self):
        return f"<FriendRequest {self.sender_id} -> {self.receiver_id} [{self.status}]>"
