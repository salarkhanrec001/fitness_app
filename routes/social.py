from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.user import User
from models.friend import Friend, FriendRequest
from models.message import Message

social_bp = Blueprint("social", __name__)

CHAT_TIMEZONE = timezone(timedelta(hours=5), name="PKT")


def _chat_message_payload(message, user_id):
    created_at = message.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    created_at_local = created_at.astimezone(CHAT_TIMEZONE)
    today_local = datetime.now(CHAT_TIMEZONE).date()
    message_date = created_at_local.date()
    if message_date == today_local:
        date_label = "Today"
    elif message_date == today_local - timedelta(days=1):
        date_label = "Yesterday"
    else:
        date_label = created_at_local.strftime("%d %b %Y")

    return {
        "id": message.id,
        "sender_id": message.sender_id,
        "body": message.body,
        "created_at": created_at_local,
        "created_at_display": created_at_local.strftime("%I:%M %p"),
        "created_at_iso": created_at_local.isoformat(),
        "created_at_date_key": created_at_local.strftime("%Y-%m-%d"),
        "created_at_date_label": date_label,
        "is_mine": message.sender_id == user_id,
    }


@social_bp.route("/friends")
@login_required
def friends():
    # All confirmed friends
    friends_list = current_user.get_friends()

    # Pending requests received
    pending_requests = FriendRequest.query.filter_by(
        receiver_id=current_user.id, status="pending"
    ).all()

    # Sent requests still pending
    sent_requests = FriendRequest.query.filter_by(
        sender_id=current_user.id, status="pending"
    ).all()

    # Calculate IDs to exclude from suggestions
    friend_ids = [f.id for f in friends_list]
    pending_sent_ids = [r.receiver_id for r in sent_requests]
    pending_received_ids = [r.sender_id for r in pending_requests]
    exclude_ids = list(set([current_user.id] + friend_ids + pending_sent_ids + pending_received_ids))

    # Fetch suggestions (newest 5 users not connected to current_user)
    suggestions = User.query.filter(User.id.notin_(exclude_ids)).order_by(User.created_at.desc()).limit(15).all()

    # Search
    query = request.args.get("q", "").strip()
    search_results = []
    if query:
        search_results = User.query.filter(
            User.username.ilike(f"%{query}%"),
            User.id != current_user.id,
        ).limit(10).all()

    return render_template(
        "social/friends.html",
        friends=friends_list,
        pending_requests=pending_requests,
        sent_requests=sent_requests,
        suggestions=suggestions,
        search_results=search_results,
        query=query,
    )


@social_bp.route("/send-request/<int:user_id>", methods=["POST"])
@login_required
def send_request(user_id):
    target = db.get_or_404(User, user_id)
    if target.id == current_user.id:
        flash("You can't add yourself.", "error")
        return redirect(url_for("social.friends"))

    existing = FriendRequest.query.filter(
        ((FriendRequest.sender_id == current_user.id) & (FriendRequest.receiver_id == target.id))
        | ((FriendRequest.sender_id == target.id) & (FriendRequest.receiver_id == current_user.id))
    ).first()

    if existing:
        flash("Friend request already exists.", "info")
        return redirect(url_for("social.friends"))

    if current_user.is_friend_with(target):
        flash("Already friends!", "info")
        return redirect(url_for("social.friends"))

    req = FriendRequest(sender_id=current_user.id, receiver_id=target.id)
    db.session.add(req)
    db.session.commit()
    flash(f"Friend request sent to {target.username}!", "success")
    return redirect(url_for("social.friends"))


@social_bp.route("/accept-request/<int:request_id>", methods=["POST"])
@login_required
def accept_request(request_id):
    freq = db.get_or_404(FriendRequest, request_id)
    if freq.receiver_id != current_user.id:
        flash("Not authorised.", "error")
        return redirect(url_for("social.friends"))

    freq.status = "accepted"
    if not current_user.is_friend_with(freq.sender):
        friendship = Friend(user_id=freq.sender_id, friend_id=freq.receiver_id)
        db.session.add(friendship)
    db.session.commit()
    flash(f"You are now friends with {freq.sender.username}!", "success")
    return redirect(url_for("social.friends"))


@social_bp.route("/reject-request/<int:request_id>", methods=["POST"])
@login_required
def reject_request(request_id):
    freq = db.get_or_404(FriendRequest, request_id)
    if freq.receiver_id != current_user.id:
        flash("Not authorised.", "error")
        return redirect(url_for("social.friends"))
    freq.status = "rejected"
    db.session.commit()
    flash("Request rejected.", "info")
    return redirect(url_for("social.friends"))


@social_bp.route("/chat/<int:friend_id>")
@login_required
def chat(friend_id):
    friend = db.get_or_404(User, friend_id)
    if not current_user.is_friend_with(friend):
        flash("You must be friends to chat.", "error")
        return redirect(url_for("social.friends"))

    # Mark received messages as read
    Message.query.filter_by(
        sender_id=friend_id,
        receiver_id=current_user.id,
        is_read=False,
    ).update({"is_read": True})
    db.session.commit()

    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == friend_id))
        | ((Message.sender_id == friend_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()

    messages = [_chat_message_payload(message, current_user.id) for message in messages]

    return render_template(
        "social/chat.html",
        friend=friend,
        messages=messages,
    )


@social_bp.route("/send-message/<int:friend_id>", methods=["POST"])
@login_required
def send_message(friend_id):
    friend = db.get_or_404(User, friend_id)
    if not current_user.is_friend_with(friend):
        flash("Not friends.", "error")
        return redirect(url_for("social.friends"))

    body = request.form.get("body", "").strip()
    if not body:
        flash("Message cannot be empty.", "error")
        return redirect(url_for("social.chat", friend_id=friend_id))

    msg = Message(sender_id=current_user.id, receiver_id=friend_id, body=body)
    db.session.add(msg)
    db.session.commit()
    return redirect(url_for("social.chat", friend_id=friend_id))


@social_bp.route("/messages-api/<int:friend_id>")
@login_required
def messages_api(friend_id):
    """JSON endpoint for live message polling."""
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == friend_id))
        | ((Message.sender_id == friend_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()

    return jsonify([
        _chat_message_payload(m, current_user.id)
        for m in messages
    ])
