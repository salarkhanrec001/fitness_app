"""
Journal Service
Ported from Motivaura.
"""

from extensions import db
from models.timetable import JournalEntry


class JournalService:

    @staticmethod
    def create_entry(user_id, content, title='', mood='neutral', tags=''):
        entry = JournalEntry(
            user_id=user_id, title=title, content=content, mood=mood, tags=tags,
        )
        db.session.add(entry)
        db.session.commit()
        return entry

    @staticmethod
    def get_entries(user_id, page=1, per_page=10, mood=None, search=None):
        query = JournalEntry.query.filter_by(user_id=user_id)
        if mood:
            query = query.filter_by(mood=mood)
        if search:
            query = query.filter(
                db.or_(
                    JournalEntry.title.ilike(f'%{search}%'),
                    JournalEntry.content.ilike(f'%{search}%'),
                )
            )
        return query.order_by(JournalEntry.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False,
        )

    @staticmethod
    def get_entry(entry_id, user_id):
        return JournalEntry.query.filter_by(id=entry_id, user_id=user_id).first()

    @staticmethod
    def update_entry(entry_id, user_id, **kwargs):
        entry = JournalEntry.query.filter_by(id=entry_id, user_id=user_id).first()
        if not entry:
            return None, 'Entry not found.'
        for k in ['title', 'content', 'mood', 'tags']:
            if k in kwargs and kwargs[k] is not None:
                setattr(entry, k, kwargs[k])
        db.session.commit()
        return entry, None

    @staticmethod
    def delete_entry(entry_id, user_id):
        entry = JournalEntry.query.filter_by(id=entry_id, user_id=user_id).first()
        if not entry:
            return False, 'Entry not found.'
        db.session.delete(entry)
        db.session.commit()
        return True, None

    @staticmethod
    def get_mood_stats(user_id):
        from sqlalchemy import func
        results = db.session.query(
            JournalEntry.mood, func.count(JournalEntry.id)
        ).filter_by(user_id=user_id).group_by(JournalEntry.mood).all()
        return {mood: count for mood, count in results}
