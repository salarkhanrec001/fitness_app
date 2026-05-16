"""Journal Routes — Ported from Motivaura"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from forms.journal_forms import JournalEntryForm
from services.journal_service import JournalService
from services.achievement_service import AchievementService

journal_bp = Blueprint('journal', __name__, url_prefix='/journal')


@journal_bp.route('/')
@login_required
def list_entries():
    page = request.args.get('page', 1, type=int)
    mood = request.args.get('mood', None)
    search = request.args.get('search', None)
    pagination = JournalService.get_entries(current_user.id, page=page, mood=mood, search=search)
    mood_stats = JournalService.get_mood_stats(current_user.id)
    return render_template('journal/list.html', pagination=pagination, mood_stats=mood_stats,
                           current_mood=mood, search=search)


@journal_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = JournalEntryForm()
    if form.validate_on_submit():
        JournalService.create_entry(
            user_id=current_user.id,
            title=form.title.data,
            content=form.content.data,
            mood=form.mood.data,
            tags=form.tags.data,
        )
        AchievementService.check_and_award(current_user.id)
        flash('Journal entry saved!', 'success')
        return redirect(url_for('journal.list_entries'))
    return render_template('journal/create.html', form=form)


@journal_bp.route('/<int:entry_id>')
@login_required
def view(entry_id):
    entry = JournalService.get_entry(entry_id, current_user.id)
    if not entry:
        flash('Entry not found.', 'danger')
        return redirect(url_for('journal.list_entries'))
    return render_template('journal/view.html', entry=entry)


@journal_bp.route('/<int:entry_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(entry_id):
    entry = JournalService.get_entry(entry_id, current_user.id)
    if not entry:
        flash('Entry not found.', 'danger')
        return redirect(url_for('journal.list_entries'))
    form = JournalEntryForm(obj=entry)
    if form.validate_on_submit():
        JournalService.update_entry(
            entry_id=entry_id, user_id=current_user.id,
            title=form.title.data, content=form.content.data,
            mood=form.mood.data, tags=form.tags.data,
        )
        flash('Entry updated!', 'success')
        return redirect(url_for('journal.view', entry_id=entry_id))
    return render_template('journal/edit.html', form=form, entry=entry)


@journal_bp.route('/<int:entry_id>/delete', methods=['POST'])
@login_required
def delete(entry_id):
    success, error = JournalService.delete_entry(entry_id, current_user.id)
    if error:
        flash(error, 'danger')
    else:
        flash('Entry deleted.', 'info')
    return redirect(url_for('journal.list_entries'))
