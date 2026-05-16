"""
Notification Service
Business logic for creating and managing in-app notifications.
Ported from Motivaura.
"""

from extensions import db
from models.notification import Notification


class NotificationService:

    @staticmethod
    def create(user_id, title, message, category='info', icon='🔔', link=None):
        notif = Notification(
            user_id=user_id, title=title, message=message,
            category=category, icon=icon, link=link,
        )
        db.session.add(notif)
        db.session.commit()
        return notif

    @staticmethod
    def get_unread(user_id, limit=20):
        return Notification.query.filter_by(
            user_id=user_id, is_read=False
        ).order_by(Notification.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_all(user_id, page=1, per_page=20):
        return Notification.query.filter_by(user_id=user_id).order_by(
            Notification.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def mark_read(notification_id, user_id):
        notif = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notif:
            notif.is_read = True
            db.session.commit()
            return True
        return False

    @staticmethod
    def mark_all_read(user_id):
        Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
        db.session.commit()

    @staticmethod
    def unread_count(user_id):
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()

    @staticmethod
    def delete(notification_id, user_id):
        notif = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notif:
            db.session.delete(notif)
            db.session.commit()
            return True
        return False
