"""Achievements Routes — Ported from Motivaura"""

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from services.achievement_service import AchievementService

achievements_bp = Blueprint('achievements', __name__, url_prefix='/achievements')


@achievements_bp.route('/')
@login_required
def index():
    all_badges = AchievementService.get_all_badges_status(current_user.id)
    earned_count = sum(1 for b in all_badges if b['earned'])
    return render_template('achievements/index.html', badges=all_badges, earned_count=earned_count)
