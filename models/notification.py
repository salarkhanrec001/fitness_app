"""
Notification Model
In-app notifications for goal reminders, achievements, etc.
Ported from Motivaura.
"""

from datetime import datetime, timezone
from extensions import db


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(30), default='info')  # info, success, warning, danger
    icon = db.Column(db.String(50), default='🔔')
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(255), nullable=True)  # optional redirect URL

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def mark_as_read(self):
        """Mark the notification as read."""
        self.is_read = True

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'category': self.category,
            'icon': self.icon,
            'is_read': self.is_read,
            'link': self.link,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Notification {self.title[:30]}>'
