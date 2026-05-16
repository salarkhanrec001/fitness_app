"""Timetable Routes — Ported from Motivaura"""

from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from forms.timetable_forms import TimetableForm, TimeSlotForm
from services.timetable_service import TimetableService
from models.timetable import TimeSlot

timetable_bp = Blueprint('timetable', __name__, url_prefix='/timetable')


def _calc_end_time(start_time_str, duration_minutes):
    """Calculate end time from start time and duration."""
    try:
        start = datetime.strptime(start_time_str, '%H:%M')
        end = start + timedelta(minutes=int(duration_minutes))
        return end.strftime('%H:%M')
    except (ValueError, TypeError):
        return start_time_str


@timetable_bp.route('/')
@login_required
def list_timetables():
    timetables = TimetableService.get_user_timetables(current_user.id)
    today_slots = TimetableService.get_today_slots(current_user.id)
    return render_template('timetable/list.html', timetables=timetables, today_slots=today_slots)


@timetable_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = TimetableForm()
    if form.validate_on_submit():
        TimetableService.create_timetable(
            user_id=current_user.id,
            title=form.title.data,
            description=form.description.data,
            color=form.color.data or '#6366f1',
        )
        flash('Timetable created!', 'success')
        return redirect(url_for('timetable.list_timetables'))
    return render_template('timetable/create.html', form=form)


@timetable_bp.route('/<int:tt_id>')
@login_required
def view(tt_id):
    tt = TimetableService.get_timetable(tt_id, current_user.id)
    if not tt:
        flash('Timetable not found.', 'danger')
        return redirect(url_for('timetable.list_timetables'))
    slot_form = TimeSlotForm()
    slots_by_day = {}
    for slot in tt.slots.order_by(TimeSlot.start_time).all():
        slots_by_day.setdefault(slot.day_of_week, []).append(slot)
    return render_template('timetable/view.html', timetable=tt, slot_form=slot_form, slots_by_day=slots_by_day)


@timetable_bp.route('/<int:tt_id>/add-slot', methods=['POST'])
@login_required
def add_slot(tt_id):
    form = TimeSlotForm()
    if form.validate_on_submit():
        end_time = form.end_time.data
        if not end_time:
            end_time = _calc_end_time(form.start_time.data, form.duration.data)
        slot, error = TimetableService.add_slot(
            timetable_id=tt_id, user_id=current_user.id,
            day_of_week=form.day_of_week.data,
            start_time=form.start_time.data,
            end_time=end_time,
            task=form.task.data,
            category=form.category.data,
            notes=form.notes.data,
        )
        if error:
            flash(error, 'danger')
        else:
            flash('Slot added!', 'success')
    else:
        for field, errors in form.errors.items():
            for err in errors:
                flash(f'{field}: {err}', 'danger')
    return redirect(url_for('timetable.view', tt_id=tt_id))


@timetable_bp.route('/slot/<int:slot_id>/toggle', methods=['POST'])
@login_required
def toggle_slot(slot_id):
    slot, error = TimetableService.toggle_slot(slot_id, current_user.id)
    if request.is_json:
        if error:
            return jsonify({'error': error}), 404
        return jsonify({'action': 'completed' if slot.is_completed else 'uncompleted', 'slot': slot.to_dict()})
    flash('Slot updated!', 'success')
    return redirect(request.referrer or url_for('timetable.list_timetables'))


@timetable_bp.route('/slot/<int:slot_id>/clone', methods=['POST'])
@login_required
def clone_slot(slot_id):
    target_days = request.form.getlist('target_days')
    if not target_days:
        flash('Select at least one day to clone to.', 'warning')
        return redirect(request.referrer or url_for('timetable.list_timetables'))
    
    success, error = TimetableService.clone_slot(slot_id, current_user.id, [int(d) for d in target_days])
    if error:
        flash(error, 'danger')
    else:
        flash(f'Slot duplicated to {len(target_days)} days!', 'success')
    return redirect(request.referrer or url_for('timetable.list_timetables'))


@timetable_bp.route('/slot/<int:slot_id>/delete', methods=['POST'])
@login_required
def delete_slot(slot_id):
    success, error = TimetableService.delete_slot(slot_id, current_user.id)
    if error:
        flash(error, 'danger')
    else:
        flash('Slot removed.', 'info')
    return redirect(request.referrer or url_for('timetable.list_timetables'))


@timetable_bp.route('/<int:tt_id>/delete', methods=['POST'])
@login_required
def delete(tt_id):
    success, error = TimetableService.delete_timetable(tt_id, current_user.id)
    if error:
        flash(error, 'danger')
    else:
        flash('Timetable deleted.', 'info')
    return redirect(url_for('timetable.list_timetables'))
