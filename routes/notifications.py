"""Notification Routes — Ported from Motivaura"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from services.notification_service import NotificationService

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/')
@login_required
def get_all():
    page = request.args.get('page', 1, type=int)
    result = NotificationService.get_all(current_user.id, page=page)
    return jsonify({
        'notifications': [n.to_dict() for n in result.items],
        'total': result.total,
        'pages': result.pages,
        'current_page': result.page,
    })


@notifications_bp.route('/unread')
@login_required
def get_unread():
    notifs = NotificationService.get_unread(current_user.id)
    count = NotificationService.unread_count(current_user.id)
    return jsonify({
        'notifications': [n.to_dict() for n in notifs],
        'count': count,
    })


@notifications_bp.route('/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    success = NotificationService.mark_read(notif_id, current_user.id)
    return jsonify({'success': success})


@notifications_bp.route('/read-all', methods=['POST'])
@login_required
def mark_all_read():
    NotificationService.mark_all_read(current_user.id)
    return jsonify({'success': True})


@notifications_bp.route('/<int:notif_id>', methods=['DELETE'])
@login_required
def delete(notif_id):
    success = NotificationService.delete(notif_id, current_user.id)
    return jsonify({'success': success})
