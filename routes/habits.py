"""Habit Routes — Ported from Motivaura"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from forms.habit_forms import HabitForm
from services.habit_service import HabitService

habits_bp = Blueprint('habits', __name__, url_prefix='/habits')


@habits_bp.route('/')
@login_required
def list_habits():
    search = request.args.get('search')
    habits = HabitService.get_user_habits(current_user.id, search=search)
    return render_template('habits/list.html', habits=habits, search=search)


@habits_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = HabitForm()
    if form.validate_on_submit():
        HabitService.create_habit(
            user_id=current_user.id, name=form.name.data,
            description=form.description.data, is_bad_habit=form.is_bad_habit.data,
            frequency=form.frequency.data, color=form.color.data, icon=form.icon.data,
        )
        flash('Habit created!', 'success')
        return redirect(url_for('habits.list_habits'))
    return render_template('habits/create.html', form=form)


@habits_bp.route('/<int:habit_id>/toggle', methods=['POST'])
@login_required
def toggle(habit_id):
    habit, action, error = HabitService.toggle_habit(habit_id, current_user.id)
    if request.is_json:
        if error:
            return jsonify({'error': error}), 400
        return jsonify({'action': action, 'habit': habit.to_dict()})
    flash(f'Habit {"completed" if action == "checked" else "unchecked"}!', 'success')
    return redirect(url_for('habits.list_habits'))


@habits_bp.route('/<int:habit_id>/delete', methods=['POST'])
@login_required
def delete(habit_id):
    success, error = HabitService.delete_habit(habit_id, current_user.id)
    if request.is_json:
        if error:
            return jsonify({'error': error}), 400
        return jsonify({'success': True})
    flash('Habit deleted.' if success else error, 'info' if success else 'danger')
    return redirect(url_for('habits.list_habits'))


@habits_bp.route('/<int:habit_id>/history')
@login_required
def history(habit_id):
    days = request.args.get('days', 30, type=int)
    data, error = HabitService.get_habit_history(habit_id, current_user.id, days)
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'history': data})
