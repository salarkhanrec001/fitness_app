"""
Habit Service
Business logic for habit tracking, streaks, and history.
Ported from Motivaura.
"""

from datetime import datetime, timezone, date, timedelta
from extensions import db
from models.habit import Habit, HabitLog
from services.notification_service import NotificationService


class HabitService:

    @staticmethod
    def create_habit(user_id, name, description='', is_bad_habit=False,
                     frequency='daily', color='#6366f1', icon='⭐'):
        habit = Habit(
            user_id=user_id, name=name, description=description,
            is_bad_habit=is_bad_habit, frequency=frequency, color=color, icon=icon,
        )
        db.session.add(habit)
        db.session.commit()
        NotificationService.create(
            user_id=user_id, title='New Habit Added ✨',
            message=f'"{name}" is now being tracked.', category='info', icon='✨', link='/habits',
        )
        return habit

    @staticmethod
    def toggle_habit(habit_id, user_id):
        habit = Habit.query.filter_by(id=habit_id, user_id=user_id).first()
        if not habit:
            return None, None, 'Habit not found.'
        today = date.today()
        existing = HabitLog.query.filter(
            HabitLog.habit_id == habit_id, db.func.date(HabitLog.logged_at) == today
        ).first()
        if existing:
            db.session.delete(existing)
            habit.total_completions = max(0, habit.total_completions - 1)
            HabitService._recalculate_streak(habit)
            db.session.commit()
            return habit, 'unchecked', None
        else:
            db.session.add(HabitLog(habit_id=habit_id))
            habit.total_completions += 1
            HabitService._recalculate_streak(habit)
            db.session.commit()
            if habit.current_streak > 0 and habit.current_streak % 7 == 0:
                NotificationService.create(
                    user_id=user_id, title=f'🔥 {habit.current_streak}-Day Streak!',
                    message=f'You maintained "{habit.name}" for {habit.current_streak} days!',
                    category='success', icon='🔥', link='/habits',
                )
            return habit, 'checked', None

    @staticmethod
    def _recalculate_streak(habit):
        today = date.today()
        streak = 0
        check_date = today
        while True:
            log = HabitLog.query.filter(
                HabitLog.habit_id == habit.id, db.func.date(HabitLog.logged_at) == check_date
            ).first()
            if log:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        habit.current_streak = streak
        if streak > habit.best_streak:
            habit.best_streak = streak

    @staticmethod
    def delete_habit(habit_id, user_id):
        habit = Habit.query.filter_by(id=habit_id, user_id=user_id).first()
        if not habit:
            return False, 'Habit not found.'
        db.session.delete(habit)
        db.session.commit()
        return True, None

    @staticmethod
    def get_user_habits(user_id, include_inactive=False, search=None):
        query = Habit.query.filter_by(user_id=user_id)
        if not include_inactive:
            query = query.filter_by(is_active=True)
        if search:
            query = query.filter(Habit.name.ilike(f'%{search}%'))
        return query.order_by(Habit.created_at.desc()).all()

    @staticmethod
    def get_habit_history(habit_id, user_id, days=30):
        habit = Habit.query.filter_by(id=habit_id, user_id=user_id).first()
        if not habit:
            return None, 'Habit not found.'
        today = date.today()
        start = today - timedelta(days=days - 1)
        logs = HabitLog.query.filter(
            HabitLog.habit_id == habit_id,
            HabitLog.logged_at >= datetime.combine(start, datetime.min.time()),
        ).all()
        log_dates = {log.logged_at.date() for log in logs}
        history = []
        for i in range(days):
            d = start + timedelta(days=i)
            history.append({'date': d.isoformat(), 'completed': d in log_dates, 'label': d.strftime('%b %d')})
        return history, None

    @staticmethod
    def get_stats(user_id):
        habits = Habit.query.filter_by(user_id=user_id, is_active=True).all()
        total = len(habits)
        good = sum(1 for h in habits if not h.is_bad_habit)
        bad = sum(1 for h in habits if h.is_bad_habit)
        total_streak = sum(h.current_streak for h in habits)
        best = max((h.best_streak for h in habits), default=0)
        done_today = sum(1 for h in habits if h.completed_today)
        today = date.today()
        weekly = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            count = sum(
                1 for h in habits
                if HabitLog.query.filter(HabitLog.habit_id == h.id, db.func.date(HabitLog.logged_at) == d).first()
            )
            weekly.append({'date': d.strftime('%a'), 'count': count, 'total': total})
        return {
            'total_habits': total, 'good_habits': good, 'bad_habits': bad,
            'total_streak': total_streak, 'best_streak': best,
            'completed_today': done_today, 'weekly_data': weekly,
        }
