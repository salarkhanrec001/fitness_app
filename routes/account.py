import os

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, logout_user
from sqlalchemy import or_

from extensions import bcrypt, db
from models.friend import Friend, FriendRequest
from models.message import Message
from models.password_reset import PasswordReset
from models.user import User
from models.workout_log import WorkoutLog
from flask_mail import Message as MailMessage
from extensions import mail

account_bp = Blueprint("account", __name__)


def _delete_avatar_file(avatar_filename):
    if not avatar_filename or avatar_filename == "default_avatar.png":
        return

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    path = os.path.join(upload_folder, avatar_filename)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


@account_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        # Always show success message to prevent email enumeration
        if user:
            # Invalidate previous resets
            PasswordReset.query.filter_by(user_id=user.id, is_used=False).update({"is_used": True})
            reset = PasswordReset(user_id=user.id)
            db.session.add(reset)
            db.session.commit()
            
            # Send the OTP via email
            try:
                msg = MailMessage(
                    subject="FitAI Password Reset Code",
                    recipients=[user.email]
                )
                msg.body = f"Hello {user.username},\n\nYour password reset OTP is: {reset.otp}\n\nThis code will expire shortly. If you did not request a password reset, you can safely ignore this email.\n\nBest regards,\nThe FitAI Team"
                mail.send(msg)
                flash("An OTP has been sent to your email address.", "success")
            except Exception as e:
                current_app.logger.error(f"Failed to send OTP email: {e}")
                flash(f"Failed to send email. Error: {str(e)}", "error")
        else:
            flash("If that email is registered, you will receive an OTP.", "info")

        return redirect(url_for("account.reset_password"))

    return render_template("account/forgot_password.html")


@account_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        otp = request.form.get("otp", "").strip()
        new_password = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("User not found.", "error")
            return render_template("account/reset_password.html")

        reset = PasswordReset.query.filter_by(
            user_id=user.id, otp=otp, is_used=False
        ).first()

        if not reset or not reset.is_valid:
            flash("Invalid or expired OTP.", "error")
            return render_template("account/reset_password.html")

        if len(new_password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("account/reset_password.html")

        if new_password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("account/reset_password.html")

        user.set_password(new_password)
        reset.is_used = True
        db.session.commit()

        flash("Password reset successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("account/reset_password.html")


@account_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    current_pw = request.form.get("current_password", "")
    new_pw = request.form.get("new_password", "")
    confirm = request.form.get("confirm_password", "")

    if not current_user.check_password(current_pw):
        flash("Current password is incorrect.", "error")
        return redirect(url_for("profile.index"))

    if len(new_pw) < 6:
        flash("New password must be at least 6 characters.", "error")
        return redirect(url_for("profile.index"))

    if new_pw != confirm:
        flash("Passwords do not match.", "error")
        return redirect(url_for("profile.index"))

    current_user.set_password(new_pw)
    db.session.commit()
    flash("Password changed successfully!", "success")
    return redirect(url_for("profile.index"))


@account_bp.route("/delete-account", methods=["POST"])
@login_required
def delete_account():
    user = current_user._get_current_object()
    current_pw = request.form.get("current_password", "")
    confirm = request.form.get("confirm_delete", "").strip().upper()

    if not user.check_password(current_pw):
        flash("Current password is incorrect.", "error")
        return redirect(url_for("profile.index"))

    if confirm != "DELETE":
        flash('Type DELETE in the confirmation box to permanently delete your account.', "error")
        return redirect(url_for("profile.index"))

    user_id = user.id
    avatar_filename = user.avatar

    try:
        Message.query.filter(or_(Message.sender_id == user_id, Message.receiver_id == user_id)).delete(synchronize_session=False)
        FriendRequest.query.filter(or_(FriendRequest.sender_id == user_id, FriendRequest.receiver_id == user_id)).delete(synchronize_session=False)
        Friend.query.filter(or_(Friend.user_id == user_id, Friend.friend_id == user_id)).delete(synchronize_session=False)
        WorkoutLog.query.filter_by(user_id=user_id).delete(synchronize_session=False)

        _delete_avatar_file(avatar_filename)

        db.session.delete(user)
        db.session.commit()
        logout_user()
        flash("Your account has been deleted permanently.", "success")
        return redirect(url_for("landing.index"))
    except Exception:
        db.session.rollback()
        flash("Could not delete your account right now. Please try again.", "error")
        return redirect(url_for("profile.index"))
