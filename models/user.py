from datetime import datetime, timezone
from extensions import db, bcrypt, login_manager
from flask_login import UserMixin



@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    avatar = db.Column(db.String(200), default="default_avatar.png")
    bio = db.Column(db.Text, default="")
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    onboarding_complete = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    profile = db.relationship("OnboardingProfile", backref="user", uselist=False, cascade="all, delete-orphan")
    fitness_plans = db.relationship("FitnessPlan", backref="user", lazy=True, cascade="all, delete-orphan")
    goals = db.relationship("Goal", backref="user", lazy=True, cascade="all, delete-orphan")
    streak = db.relationship("Streak", backref="user", uselist=False, cascade="all, delete-orphan")
    sent_messages = db.relationship("Message", foreign_keys="Message.sender_id", backref="sender", lazy=True)
    received_messages = db.relationship("Message", foreign_keys="Message.receiver_id", backref="receiver", lazy=True)
    sent_requests = db.relationship("FriendRequest", foreign_keys="FriendRequest.sender_id", backref="sender", lazy=True)
    received_requests = db.relationship("FriendRequest", foreign_keys="FriendRequest.receiver_id", backref="receiver", lazy=True)
    password_resets = db.relationship("PasswordReset", backref="user", lazy=True, cascade="all, delete-orphan")

    # ── Motivaura feature relationships ──
    habits = db.relationship("Habit", backref="owner", lazy="dynamic", cascade="all, delete-orphan",
                             foreign_keys="Habit.user_id")
    timetables = db.relationship("Timetable", backref="owner", lazy="dynamic", cascade="all, delete-orphan")
    journal_entries = db.relationship("JournalEntry", backref="owner", lazy="dynamic", cascade="all, delete-orphan")
    achievements = db.relationship("Achievement", backref="owner", lazy="dynamic", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref="owner", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_active_plan(self):
        from models.fitness_plan import FitnessPlan
        return FitnessPlan.query.filter_by(user_id=self.id, is_active=True).first()


    def get_friends(self):
        from models.friend import Friend
        friend_ids = [
            f.friend_id if f.user_id == self.id else f.user_id
            for f in Friend.query.filter(
                (Friend.user_id == self.id) | (Friend.friend_id == self.id)
            ).all()
        ]
        return User.query.filter(User.id.in_(friend_ids)).all()

    def is_friend_with(self, other_user):
        from models.friend import Friend
        return Friend.query.filter(
            ((Friend.user_id == self.id) & (Friend.friend_id == other_user.id))
            | ((Friend.user_id == other_user.id) & (Friend.friend_id == self.id))
        ).first() is not None

    def __repr__(self):
        return f"<User {self.username}>"
