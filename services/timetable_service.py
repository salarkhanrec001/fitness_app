"""
Timetable Service
Ported from Motivaura.
"""

from datetime import datetime, timezone, date
from extensions import db
from models.timetable import Timetable, TimeSlot


class TimetableService:

    @staticmethod
    def create_timetable(user_id, title, description='', color='#6366f1'):
        tt = Timetable(user_id=user_id, title=title, description=description, color=color)
        db.session.add(tt)
        db.session.commit()
        return tt

    @staticmethod
    def get_user_timetables(user_id):
        return Timetable.query.filter_by(user_id=user_id, is_active=True).order_by(
            Timetable.created_at.desc()
        ).all()

    @staticmethod
    def get_timetable(timetable_id, user_id):
        return Timetable.query.filter_by(id=timetable_id, user_id=user_id).first()

    @staticmethod
    def delete_timetable(timetable_id, user_id):
        tt = Timetable.query.filter_by(id=timetable_id, user_id=user_id).first()
        if not tt:
            return False, 'Timetable not found.'
        db.session.delete(tt)
        db.session.commit()
        return True, None

    @staticmethod
    def add_slot(timetable_id, user_id, day_of_week, start_time, end_time, task, category='general', notes=''):
        tt = Timetable.query.filter_by(id=timetable_id, user_id=user_id).first()
        if not tt:
            return None, 'Timetable not found.'
        slot = TimeSlot(
            timetable_id=timetable_id, day_of_week=day_of_week,
            start_time=start_time, end_time=end_time,
            task=task, category=category, notes=notes,
        )
        db.session.add(slot)
        db.session.commit()
        return slot, None

    @staticmethod
    def toggle_slot(slot_id, user_id):
        slot = TimeSlot.query.join(Timetable).filter(
            TimeSlot.id == slot_id, Timetable.user_id == user_id
        ).first()
        if not slot:
            return None, 'Slot not found.'
        slot.is_completed = not slot.is_completed
        db.session.commit()
        return slot, None

    @staticmethod
    def delete_slot(slot_id, user_id):
        slot = TimeSlot.query.join(Timetable).filter(
            TimeSlot.id == slot_id, Timetable.user_id == user_id
        ).first()
        if not slot:
            return False, 'Slot not found.'
        db.session.delete(slot)
        db.session.commit()
        return True, None

    @staticmethod
    def get_today_slots(user_id):
        today_dow = date.today().weekday()
        return TimeSlot.query.join(Timetable).filter(
            Timetable.user_id == user_id, Timetable.is_active == True,
            TimeSlot.day_of_week == today_dow,
        ).order_by(TimeSlot.start_time).all()

    @staticmethod
    def clone_slot(slot_id, user_id, target_days):
        try:
            source = TimeSlot.query.join(Timetable).filter(
                TimeSlot.id == slot_id, Timetable.user_id == user_id
            ).first()
            if not source:
                return False, 'Source slot not found.'
            
            for day in target_days:
                new_slot = TimeSlot(
                    timetable_id=source.timetable_id,
                    day_of_week=day,
                    start_time=source.start_time,
                    end_time=source.end_time,
                    task=source.task,
                    category=source.category,
                    notes=source.notes
                )
                db.session.add(new_slot)
            
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            return False, str(e)
