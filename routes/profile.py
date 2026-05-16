import os
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models.user import User
from models.weight_log import WeightLog

profile_bp = Blueprint("profile", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_AVATAR_SIZE = (400, 400)   # px — resized with Pillow


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _save_avatar(file, user_id):
    """
    Save uploaded image as a square JPEG thumbnail.
    Returns the saved filename, or None on failure.
    Deletes any old avatar for this user.
    """
    try:
        from PIL import Image
        import io
        import time

        ext = file.filename.rsplit(".", 1)[1].lower()
        # Save as JPEG always for consistency (except GIF stays GIF)
        save_ext = "gif" if ext == "gif" else "jpg"
        # Add a timestamp to break browser caching
        timestamp = int(time.time())
        filename = f"avatar_{user_id}_{timestamp}.{save_ext}"
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        save_path = os.path.join(upload_folder, filename)

        img = Image.open(file.stream)

        # Convert to RGB (handles RGBA/palette PNGs)
        if save_ext == "jpg" and img.mode not in ("RGB",):
            img = img.convert("RGB")

        # Crop to square from centre then resize
        w, h = img.size
        min_dim = min(w, h)
        left   = (w - min_dim) // 2
        top    = (h - min_dim) // 2
        img    = img.crop((left, top, left + min_dim, top + min_dim))
        
        # Use getattr for compatibility with Pillow >= 10.0
        resample_filter = getattr(Image, 'Resampling', Image).LANCZOS
        img    = img.resize(MAX_AVATAR_SIZE, resample_filter)

        img.save(save_path, quality=88, optimize=True)
        # Ensure the web server can read the file
        try:
            os.chmod(save_path, 0o644)
        except OSError:
            pass
        return filename

    except Exception as e:
        current_app.logger.error(f"Avatar save error: {e}")
        return None


def _delete_old_avatar(avatar_filename):
    """Delete the previous avatar file if it's not the default."""
    if not avatar_filename or avatar_filename == "default_avatar.png":
        return
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    path = os.path.join(upload_folder, avatar_filename)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


@profile_bp.route("/")
@login_required
def index():
    return render_template("profile.html", user=current_user)


@profile_bp.route("/upload-avatar", methods=["POST"])
@login_required
def upload_avatar():
    """Dedicated endpoint for avatar-only upload — called via AJAX or direct form post."""
    if "avatar" not in request.files:
        flash("No file selected.", "error")
        return redirect(url_for("profile.index"))

    file = request.files["avatar"]
    if not file or not file.filename:
        flash("No file selected.", "error")
        return redirect(url_for("profile.index"))

    if not _allowed_file(file.filename):
        flash("Invalid file type. Please upload PNG, JPG, WEBP or GIF.", "error")
        return redirect(url_for("profile.index"))

    # Check raw size before processing
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    if file_size > 2 * 1024 * 1024:   # 2 MB hard limit
        flash("Image too large. Max size is 2 MB.", "error")
        return redirect(url_for("profile.index"))

    old_avatar = current_user.avatar
    filename = _save_avatar(file, current_user.id)

    if not filename:
        flash("Could not process the image. Please try a different file.", "error")
        return redirect(url_for("profile.index"))

    # Delete old avatar (if not default) and save new one
    _delete_old_avatar(old_avatar)
    current_user.avatar = filename
    db.session.commit()

    flash("Profile photo updated! 🎉", "success")
    return redirect(url_for("profile.index"))


@profile_bp.route("/remove-avatar", methods=["POST"])
@login_required
def remove_avatar():
    """Reset avatar back to the default."""
    old_avatar = current_user.avatar
    _delete_old_avatar(old_avatar)
    current_user.avatar = "default_avatar.png"
    db.session.commit()
    flash("Profile photo removed.", "info")
    return redirect(url_for("profile.index"))


@profile_bp.route("/edit", methods=["POST"])
@login_required
def edit():
    username = request.form.get("username", "").strip()
    bio = request.form.get("bio", "").strip()

    errors = []
    if not username or len(username) < 3:
        errors.append("Username must be at least 3 characters.")

    existing = User.query.filter(
        User.username == username, User.id != current_user.id
    ).first()
    if existing:
        errors.append("Username already taken.")

    if errors:
        for e in errors:
            flash(e, "error")
        return redirect(url_for("profile.index"))

    current_user.username = username
    current_user.bio = bio
    db.session.commit()
    flash("Profile updated successfully!", "success")
    return redirect(url_for("profile.index"))


@profile_bp.route("/update-stats", methods=["POST"])
@login_required
def update_stats():
    profile = current_user.profile
    if not profile:
        flash("Complete onboarding first.", "error")
        return redirect(url_for("profile.index"))

    try:
        weight = request.form.get("weight_kg", "").strip()
        height = request.form.get("height_cm", "").strip()
        if weight:
            weight_value = float(weight)
            profile.weight_kg = weight_value
            db.session.add(WeightLog(user_id=current_user.id, weight_kg=weight_value))
        if height:
            profile.height_cm = float(height)
    except ValueError:
        flash("Invalid values entered.", "error")
        return redirect(url_for("profile.index"))

    db.session.commit()
    flash("Stats updated!", "success")
    return redirect(url_for("profile.index"))


# ── Public Profile URL (#10) ─────────────────────────────────
@profile_bp.route("/user/<username>")
def public_profile(username):
    """Public profile page — accessible by anyone."""
    user = User.query.filter_by(username=username).first_or_404()
    from models.streak import Streak
    from models.goal import Goal
    from models.workout_log import WorkoutLog
    streak = Streak.query.filter_by(user_id=user.id).first()
    goals  = Goal.query.filter_by(user_id=user.id, is_completed=False).limit(5).all()
    recent_logs = (
        WorkoutLog.query
        .filter_by(user_id=user.id)
        .order_by(WorkoutLog.created_at.desc())
        .limit(5)
        .all()
    )
    return render_template(
        "profile/public.html",
        viewed_user=user,
        streak=streak,
        goals=goals,
        recent_logs=recent_logs,
    )
