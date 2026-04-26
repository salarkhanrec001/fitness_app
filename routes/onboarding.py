from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from extensions import db
from models.onboarding import OnboardingProfile

onboarding_bp = Blueprint("onboarding", __name__)


def _get_or_create_profile():
    profile = OnboardingProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = OnboardingProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
    return profile


@onboarding_bp.route("/step1", methods=["GET", "POST"])
@login_required
def step1():
    profile = _get_or_create_profile()
    if request.method == "POST":
        age = request.form.get("age", "").strip()
        if not age.isdigit() or not (10 <= int(age) <= 100):
            flash("Please enter a valid age between 10 and 100.", "error")
            return render_template("onboard/step1_age.html", profile=profile)
        profile.age = int(age)
        db.session.commit()
        return redirect(url_for("onboarding.step2"))
    return render_template("onboard/step1_age.html", profile=profile)


@onboarding_bp.route("/step2", methods=["GET", "POST"])
@login_required
def step2():
    profile = _get_or_create_profile()
    if request.method == "POST":
        gender = request.form.get("gender", "").strip()
        if gender not in ("male", "female", "non_binary", "prefer_not"):
            flash("Please select a valid option.", "error")
            return render_template("onboard/step2_gender.html", profile=profile)
        profile.gender = gender
        db.session.commit()
        return redirect(url_for("onboarding.step3"))
    return render_template("onboard/step2_gender.html", profile=profile)


@onboarding_bp.route("/step3", methods=["GET", "POST"])
@login_required
def step3():
    profile = _get_or_create_profile()
    if request.method == "POST":
        height = request.form.get("height_cm", "").strip()
        try:
            height = float(height)
            if not (50 <= height <= 280):
                raise ValueError
        except ValueError:
            flash("Please enter a valid height between 50 and 280 cm.", "error")
            return render_template("onboard/step3_height.html", profile=profile)
        profile.height_cm = height
        db.session.commit()
        return redirect(url_for("onboarding.step4"))
    return render_template("onboard/step3_height.html", profile=profile)


@onboarding_bp.route("/step4", methods=["GET", "POST"])
@login_required
def step4():
    profile = _get_or_create_profile()
    if request.method == "POST":
        weight = request.form.get("weight_kg", "").strip()
        try:
            weight = float(weight)
            if not (20 <= weight <= 500):
                raise ValueError
        except ValueError:
            flash("Please enter a valid weight between 20 and 500 kg.", "error")
            return render_template("onboard/step4_weight.html", profile=profile)
        profile.weight_kg = weight
        db.session.commit()
        return redirect(url_for("onboarding.step5"))
    return render_template("onboard/step4_weight.html", profile=profile)


@onboarding_bp.route("/step5", methods=["GET", "POST"])
@login_required
def step5():
    profile = _get_or_create_profile()
    valid_goals = ("lose_weight", "build_muscle", "stay_fit", "increase_endurance", "improve_flexibility", "six_pack")
    if request.method == "POST":
        goal = request.form.get("fitness_goal", "").strip()
        if goal not in valid_goals:
            flash("Please select a valid fitness goal.", "error")
            return render_template("onboard/step5_goal.html", profile=profile)
        profile.fitness_goal = goal
        db.session.commit()
        return redirect(url_for("onboarding.step6"))
    return render_template("onboard/step5_goal.html", profile=profile)


@onboarding_bp.route("/step6", methods=["GET", "POST"])
@login_required
def step6():
    profile = _get_or_create_profile()
    if request.method == "POST":
        level = request.form.get("experience_level", "").strip()
        if level not in ("beginner", "intermediate", "advanced"):
            flash("Please select a valid experience level.", "error")
            return render_template("onboard/step6_experience.html", profile=profile)
        profile.experience_level = level
        db.session.commit()

        current_user.onboarding_complete = True
        db.session.commit()

        # Trigger AI plan generation — wrapped so any failure doesn't break onboarding
        try:
            from routes.ai_routes import generate_plan_for_user
            generate_plan_for_user(current_user, profile)
        except Exception:
            pass  # Plan can be regenerated later from the dashboard

        flash("Profile complete! Your personalised plan is ready.", "success")
        return redirect(url_for("dashboard.index"))
    return render_template("onboard/step6_experience.html", profile=profile)


@onboarding_bp.route("/start-challenge/<challenge_type>")
@login_required
def start_challenge(challenge_type):
    """Special route to immediately switch goal and regenerate plan."""
    profile = OnboardingProfile.query.filter_by(user_id=current_user.id).first()
    if challenge_type == "six_pack" and profile:
        profile.fitness_goal = "six_pack"
        db.session.commit()

        from routes.ai_routes import generate_plan_for_user
        generate_plan_for_user(current_user, profile)

        # Trigger daily plan generation for the new goal immediately
        try:
            from services.gemini_service import generate_daily_plan
            from models.daily_recommendation import DailyRecommendation
            data = generate_daily_plan(current_user, profile)
            DailyRecommendation.create_from_data(current_user.id, data)
        except Exception:
            pass

        flash("🔥 30-Day Six Pack Challenge Started! Study the exercises below and start your first session.", "success")
        return redirect(url_for("ai.challenge_six_pack"))

    flash("Challenge not found.", "error")
    return redirect(url_for("dashboard.index"))
