"""
Achievement Service — Gamification badges
Ported from Motivaura.
"""

from extensions import db
from models.timetable import Achievement
from services.notification_service import NotificationService

# Badge definitions
BADGE_DEFS = {
    'first_goal': {'title': 'Goal Setter', 'desc': 'Created your first goal', 'icon': '🎯'},
    'first_habit': {'title': 'Habit Builder', 'desc': 'Created your first habit', 'icon': '🔁'},
    'streak_7': {'title': 'Week Warrior', 'desc': '7-day streak on any habit', 'icon': '🔥'},
    'streak_30': {'title': 'Monthly Master', 'desc': '30-day streak on any habit', 'icon': '💎'},
    'goals_5': {'title': 'Ambitious', 'desc': 'Completed 5 goals', 'icon': '⭐'},
    'goals_10': {'title': 'Unstoppable', 'desc': 'Completed 10 goals', 'icon': '🚀'},
    'journal_7': {'title': 'Reflector', 'desc': 'Wrote 7 journal entries', 'icon': '📓'},
    'challenge_complete': {'title': 'Challenge Champion', 'desc': 'Completed a 30-day challenge', 'icon': '🏆'},
    'early_bird': {'title': 'Early Bird', 'desc': 'Logged in before 6 AM', 'icon': '🌅'},
    'night_owl': {'title': 'Night Owl', 'desc': 'Active past midnight', 'icon': '🦉'},
    'first_workout': {'title': 'First Steps', 'desc': 'Completed your first workout', 'icon': '💪'},
    'workout_streak_7': {'title': 'Workout Warrior', 'desc': '7-day workout streak', 'icon': '🏋️'},
}


class AchievementService:

    @staticmethod
    def get_user_achievements(user_id):
        return Achievement.query.filter_by(user_id=user_id).order_by(
            Achievement.earned_at.desc()
        ).all()

    @staticmethod
    def has_badge(user_id, badge_type):
        return Achievement.query.filter_by(user_id=user_id, badge_type=badge_type).first() is not None

    @staticmethod
    def award_badge(user_id, badge_type):
        if AchievementService.has_badge(user_id, badge_type):
            return None
        defn = BADGE_DEFS.get(badge_type, {})
        badge = Achievement(
            user_id=user_id, badge_type=badge_type,
            title=defn.get('title', badge_type),
            description=defn.get('desc', ''),
            icon=defn.get('icon', '🏆'),
        )
        db.session.add(badge)
        db.session.commit()
        NotificationService.create(
            user_id=user_id,
            title=f'Badge Earned: {badge.icon} {badge.title}',
            message=badge.description,
            category='success', icon=badge.icon,
        )
        return badge

    @staticmethod
    def check_and_award(user_id):
        from models.goal import Goal
        from models.habit import Habit
        from models.timetable import JournalEntry

        # First goal
        if Goal.query.filter_by(user_id=user_id).count() >= 1:
            AchievementService.award_badge(user_id, 'first_goal')
        # First habit
        if Habit.query.filter_by(user_id=user_id).count() >= 1:
            AchievementService.award_badge(user_id, 'first_habit')
        # 5 completed goals
        completed = Goal.query.filter_by(user_id=user_id, is_completed=True).count()
        if completed >= 5:
            AchievementService.award_badge(user_id, 'goals_5')
        if completed >= 10:
            AchievementService.award_badge(user_id, 'goals_10')
        # Streak badges
        habits = Habit.query.filter_by(user_id=user_id).all()
        for h in habits:
            if h.current_streak >= 7:
                AchievementService.award_badge(user_id, 'streak_7')
            if h.current_streak >= 30:
                AchievementService.award_badge(user_id, 'streak_30')
            if h.is_bad_habit and h.challenge_completed:
                AchievementService.award_badge(user_id, 'challenge_complete')
        # Journal entries
        if JournalEntry.query.filter_by(user_id=user_id).count() >= 7:
            AchievementService.award_badge(user_id, 'journal_7')

    @staticmethod
    def get_all_badges_status(user_id):
        earned = {a.badge_type for a in Achievement.query.filter_by(user_id=user_id).all()}
        result = []
        for key, defn in BADGE_DEFS.items():
            result.append({**defn, 'badge_type': key, 'earned': key in earned})
        return result
