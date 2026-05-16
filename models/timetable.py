"""
Timetable, TimeSlot, JournalEntry, and Achievement Models
Schedule tasks with specific time slots, journal entries with mood tracking,
and gamification badges.
Ported from Motivaura.
"""

from datetime import datetime, timezone
from extensions import db


class Timetable(db.Model):
    __tablename__ = 'timetables'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    color = db.Column(db.String(7), default='#6366f1')
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    slots = db.relationship('TimeSlot', backref='timetable', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'color': self.color,
            'is_active': self.is_active,
            'slots': [s.to_dict() for s in self.slots.all()],
        }

    def __repr__(self):
        return f'<Timetable {self.title}>'


class TimeSlot(db.Model):
    __tablename__ = 'time_slots'

    id = db.Column(db.Integer, primary_key=True)
    timetable_id = db.Column(db.Integer, db.ForeignKey('timetables.id', ondelete='CASCADE'), nullable=False)

    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Mon, 6=Sun
    start_time = db.Column(db.String(5), nullable=False)  # HH:MM
    end_time = db.Column(db.String(5), nullable=False)    # HH:MM
    task = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), default='general')  # study, workout, work, personal, etc.
    is_completed = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, default='')

    DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    @property
    def day_name(self):
        return self.DAY_NAMES[self.day_of_week] if 0 <= self.day_of_week <= 6 else 'Unknown'

    @property
    def start_time_12(self):
        try:
            from datetime import datetime
            return datetime.strptime(self.start_time, '%H:%M').strftime('%I:%M %p').lstrip('0')
        except Exception:
            return self.start_time

    @property
    def end_time_12(self):
        try:
            from datetime import datetime
            return datetime.strptime(self.end_time, '%H:%M').strftime('%I:%M %p').lstrip('0')
        except Exception:
            return self.end_time

    @property
    def duration_formatted(self):
        try:
            from datetime import datetime
            start = datetime.strptime(self.start_time, '%H:%M')
            end = datetime.strptime(self.end_time, '%H:%M')
            diff = (end - start).total_seconds() / 60
            if diff < 0:
                diff += 24 * 60
            mins = int(diff)
            if mins >= 60:
                h = mins // 60
                m = mins % 60
                return f"{h}h {m}m" if m else f"{h}h"
            return f"{mins}m"
        except Exception:
            return ""

    def to_dict(self):
        return {
            'id': self.id,
            'day_of_week': self.day_of_week,
            'day_name': self.day_name,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'task': self.task,
            'category': self.category,
            'is_completed': self.is_completed,
            'notes': self.notes,
        }

    def __repr__(self):
        return f'<TimeSlot {self.day_name} {self.start_time}-{self.end_time}>'


class JournalEntry(db.Model):
    __tablename__ = 'journal_entries'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    title = db.Column(db.String(200), default='')
    content = db.Column(db.Text, nullable=False)
    mood = db.Column(db.String(20), default='neutral')  # great, good, neutral, bad, terrible
    tags = db.Column(db.String(500), default='')
    is_private = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    MOOD_ICONS = {
        'great': '🤩', 'good': '😊', 'neutral': '😐', 'bad': '😔', 'terrible': '😢'
    }

    @property
    def mood_icon(self):
        return self.MOOD_ICONS.get(self.mood, '😐')

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()] if self.tags else []

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'mood': self.mood,
            'mood_icon': self.mood_icon,
            'tags': self.tag_list,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<JournalEntry {self.title[:30]}>'


class Achievement(db.Model):
    __tablename__ = 'achievements'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    badge_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), default='')
    icon = db.Column(db.String(10), default='🏆')
    earned_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'badge_type': self.badge_type,
            'title': self.title,
            'description': self.description,
            'icon': self.icon,
            'earned_at': self.earned_at.isoformat() if self.earned_at else None,
        }

    def __repr__(self):
        return f'<Achievement {self.title}>'
