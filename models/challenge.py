"""
Challenge & ChallengeParticipant Models
Social challenges where users compete on habits.
Ported from Motivaura.
"""

from datetime import datetime, timezone
from extensions import db


class Challenge(db.Model):
    __tablename__ = 'challenges'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # The habit being tracked (shared type)
    habit_name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(10), default='🤝')

    # Status and Timing
    status = db.Column(db.String(20), default='active')  # active, completed, failed
    duration_days = db.Column(db.Integer, default=30)
    start_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    participants = db.relationship('ChallengeParticipant', backref='challenge', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Challenge {self.name}>'


class ChallengeParticipant(db.Model):
    __tablename__ = 'challenge_participants'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)

    # status: invited, accepted, declined
    status = db.Column(db.String(20), default='pending')

    # Personal progress in the challenge
    is_failed = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('challenge_memberships', lazy='dynamic'))
