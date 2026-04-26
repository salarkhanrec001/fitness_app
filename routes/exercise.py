import json
import re
from datetime import date, timedelta
from collections import defaultdict
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.streak import Streak
from models.workout_log import WorkoutLog

exercise_bp = Blueprint("exercise", __name__)

EXERCISE_LIBRARY = {
    "push-ups": {
        "name": "Push-Ups",
        "muscles": "Chest, Triceps, Shoulders",
        "difficulty": "Beginner",
        "instructions": [
            "Start in a high plank position with hands shoulder-width apart.",
            "Lower your chest to the floor keeping elbows at ~45°.",
            "Push back up explosively.",
            "Keep your core braced throughout.",
        ],
        "sets": 3, "reps": "10–15", "rest": "60s", "icon": "💪",
    },
    "yoga": {
        "name": "Yoga & Mobility",
        "muscles": "Full Body",
        "difficulty": "Beginner",
        "instructions": [
            "Flow through gentle stretches and poses.",
            "Focus on deep breathing.",
            "Hold tight spots for 30 seconds.",
            "Stay hydrated and relaxed."
        ],
        "sets": 1, "reps": "20-30 min", "rest": "N/A", "icon": "🧘",
    },
    "circuit": {
        "name": "Full Body Circuit",
        "muscles": "Full Body",
        "difficulty": "Intermediate",
        "instructions": [
            "Perform a mix of squats, push-ups, and core exercises.",
            "Keep rest minimal between exercises.",
            "Complete the designated number of rounds.",
            "Pace yourself to maintain form."
        ],
        "sets": 4, "reps": "1 circuit", "rest": "90s", "icon": "⚡",
    },
    "squats": {
        "name": "Bodyweight Squats",
        "muscles": "Quads, Hamstrings, Glutes",
        "difficulty": "Beginner",
        "instructions": [
            "Stand with feet shoulder-width apart, toes slightly out.",
            "Drive hips back and bend knees, lowering until thighs are parallel.",
            "Keep chest tall and knees tracking over toes.",
            "Drive through heels to stand.",
        ],
        "sets": 3, "reps": "12–15", "rest": "60s", "icon": "🦵",
    },
    "plank": {
        "name": "Plank Hold",
        "muscles": "Core, Shoulders, Glutes",
        "difficulty": "Beginner",
        "instructions": [
            "Place forearms on the floor, elbows under shoulders.",
            "Form a straight line from head to heels.",
            "Squeeze glutes and brace core.",
            "Hold for the designated time.",
        ],
        "sets": 3, "reps": "30–60s", "rest": "45s", "icon": "🧱",
    },
    "lunges": {
        "name": "Forward Lunges",
        "muscles": "Quads, Glutes, Hamstrings",
        "difficulty": "Beginner",
        "instructions": [
            "Stand tall with feet together.",
            "Step forward with one leg, lowering the back knee toward the floor.",
            "Front knee stays over ankle.",
            "Push through front heel to return.",
        ],
        "sets": 3, "reps": "10 each leg", "rest": "60s", "icon": "🏃",
    },
    "burpees": {
        "name": "Burpees",
        "muscles": "Full Body",
        "difficulty": "Intermediate",
        "instructions": [
            "Stand, then drop hands to floor.",
            "Jump feet back to plank.",
            "Perform a push-up.",
            "Jump feet forward, then explode upward with arms overhead.",
        ],
        "sets": 4, "reps": "8–12", "rest": "90s", "icon": "🔥",
    },
    "deadlift": {
        "name": "Romanian Deadlift",
        "muscles": "Hamstrings, Glutes, Lower Back",
        "difficulty": "Intermediate",
        "instructions": [
            "Hold dumbbells/barbell in front of thighs.",
            "Hinge at hips, pushing them back.",
            "Lower weight along legs keeping back flat.",
            "Drive hips forward to stand.",
        ],
        "sets": 4, "reps": "8–10", "rest": "90s", "icon": "🏋️",
    },
    "pull-ups": {
        "name": "Pull-Ups",
        "muscles": "Lats, Biceps, Rear Delts",
        "difficulty": "Advanced",
        "instructions": [
            "Hang from bar with overhand grip, shoulder-width.",
            "Retract scapulae and pull chest to bar.",
            "Lower under control.",
            "Avoid swinging.",
        ],
        "sets": 4, "reps": "6–10", "rest": "90s", "icon": "⬆️",
    },
    "mountain-climbers": {
        "name": "Mountain Climbers",
        "muscles": "Core, Shoulders, Hip Flexors",
        "difficulty": "Intermediate",
        "instructions": [
            "Start in a high plank position.",
            "Drive right knee toward chest.",
            "Quickly switch legs in a running motion.",
            "Keep hips level.",
        ],
        "sets": 3, "reps": "20 each leg", "rest": "60s", "icon": "⛰️",
    },
    "bench-press": {
        "name": "Bench Press",
        "muscles": "Chest, Triceps, Shoulders",
        "difficulty": "Intermediate",
        "instructions": [
            "Lie flat on a bench, gripping the bar slightly wider than shoulder-width.",
            "Lower the bar under control to your mid-chest.",
            "Press the bar back up until your arms are fully extended.",
            "Keep your feet flat on the floor and core braced.",
        ],
        "sets": 3, "reps": "8-10", "rest": "90s", "icon": "🏋️‍♂️",
    },
    "rows": {
        "name": "Dumbbell/Barbell Rows",
        "muscles": "Lats, Rhomboids, Biceps",
        "difficulty": "Intermediate",
        "instructions": [
            "Hinge forward at the hips, keeping your back straight.",
            "Pull the weight(s) up toward your lower ribcage.",
            "Squeeze your shoulder blades together at the top.",
            "Lower the weight under control.",
        ],
        "sets": 3, "reps": "10-12", "rest": "60s", "icon": "🚣",
    },
    "overhead-press": {
        "name": "Overhead Press",
        "muscles": "Shoulders, Triceps, Core",
        "difficulty": "Intermediate",
        "instructions": [
            "Stand tall holding the bar or dumbbells at shoulder level.",
            "Press the weight overhead until arms are fully extended.",
            "Keep your core tight and avoid leaning back excessively.",
            "Lower the weight back to your shoulders.",
        ],
        "sets": 3, "reps": "8-10", "rest": "90s", "icon": "🏋️",
    },
    "cardio": {
        "name": "Cardio / Running",
        "muscles": "Cardiovascular, Legs",
        "difficulty": "Beginner",
        "instructions": [
            "Maintain a steady pace that elevates your heart rate.",
            "Focus on consistent breathing.",
            "Use a treadmill, bike, or run outdoors.",
            "Warm up and cool down for 5 minutes.",
        ],
        "sets": 1, "reps": "20-30 min", "rest": "N/A", "icon": "🏃‍♂️",
    },
    "crunches": {
        "name": "Crunches",
        "muscles": "Core (Abs)",
        "difficulty": "Beginner",
        "instructions": [
            "Lie on your back with knees bent and feet flat on the floor.",
            "Place your hands lightly behind your head.",
            "Lift your shoulders off the ground by contracting your abs.",
            "Lower back down under control.",
        ],
        "sets": 3, "reps": "15-20", "rest": "45s", "icon": "🔥",
    },
    "bicep-curls": {
        "name": "Bicep Curls",
        "muscles": "Biceps",
        "difficulty": "Beginner",
        "instructions": [
            "Stand holding dumbbells by your sides, palms facing forward.",
            "Keep your upper arms stationary and curl the weights up.",
            "Squeeze your biceps at the top.",
            "Lower the weights slowly back to the starting position.",
        ],
        "sets": 3, "reps": "12-15", "rest": "60s", "icon": "💪",
    },
    "yoga": {
        "name": "Yoga & Mobility",
        "muscles": "Full Body",
        "difficulty": "Beginner",
        "instructions": [
            "Flow through gentle stretches and poses.",
            "Focus on deep breathing.",
            "Hold tight spots for 30 seconds.",
            "Stay hydrated and relaxed."
        ],
        "sets": 1, "reps": "20-30 min", "rest": "N/A", "icon": "🧘",
    },
    "circuit": {
        "name": "Full Body Circuit",
        "muscles": "Full Body",
        "difficulty": "Intermediate",
        "instructions": [
            "Perform a mix of squats, push-ups, and core exercises.",
            "Keep rest minimal between exercises.",
            "Complete the designated number of rounds.",
            "Pace yourself to maintain form."
        ],
        "sets": 4, "reps": "1 circuit", "rest": "90s", "icon": "⚡",
    },
    "leg-raises": {
        "name": "Leg Raises",
        "muscles": "Lower Abs, Hip Flexors",
        "difficulty": "Intermediate",
        "instructions": [
            "Lie on your back with legs straight.",
            "Keep hands under your glutes for support.",
            "Lift legs until they are vertical.",
            "Lower them slowly without touching the floor.",
        ],
        "sets": 3, "reps": "12-15", "rest": "45s", "icon": "🦵",
    },
    "russian-twists": {
        "name": "Russian Twists",
        "muscles": "Obliques, Core",
        "difficulty": "Beginner",
        "instructions": [
            "Sit with knees bent and feet slightly off the floor.",
            "Lean back slightly to engage your core.",
            "Twist your torso from side to side.",
            "Touch the floor with your hands on each side.",
        ],
        "sets": 3, "reps": "20 total", "rest": "45s", "icon": "🌪️",
    },
    "bicycle-crunches": {
        "name": "Bicycle Crunches",
        "muscles": "Full Core, Obliques",
        "difficulty": "Intermediate",
        "instructions": [
            "Lie on your back with hands behind your head.",
            "Bring one knee toward your chest while twisting the opposite elbow to meet it.",
            "Switch sides in a pedaling motion.",
            "Keep your shoulders off the floor.",
        ],
        "sets": 3, "reps": "20 total", "rest": "45s", "icon": "🚲",
    },
}

YOUTUBE_LINKS_BY_NAME = {
    "Crunches": "https://www.youtube.com/results?search_query=how+to+do+crunches+exercise",
    "Leg Raises": "https://www.youtube.com/results?search_query=how+to+do+leg+raises+exercise",
    "Russian Twists": "https://www.youtube.com/results?search_query=how+to+do+russian+twists+exercise",
    "Bicycle Crunches": "https://www.youtube.com/results?search_query=how+to+do+bicycle+crunches+exercise",
    "Plank Hold": "https://www.youtube.com/results?search_query=how+to+do+plank+hold+exercise",
}


def _attach_video_links(exercises):
    """Attach YouTube demo links to exercises when available."""
    enriched = []
    for ex in exercises or []:
        ex_copy = dict(ex)
        youtube_url = YOUTUBE_LINKS_BY_NAME.get(ex_copy.get("name"))
        if youtube_url:
            ex_copy["youtube_url"] = youtube_url
        enriched.append(ex_copy)
    return enriched


def _format_workout_text(text: str) -> str:
    """Expand workout shorthand into user-friendly language."""
    if not text:
        return ""
    friendly = str(text).strip()
    friendly = re.sub(r"(?i)\bHIIT\b", "high-intensity interval training", friendly)
    friendly = re.sub(r"(?i)\bOHP\b", "overhead press", friendly)
    friendly = re.sub(r"(?i)\b(\d+)\s*[×x]\s*(\d+)\b", r"\1 sets of \2 reps", friendly)
    friendly = friendly.replace(" / ", " or ")
    return friendly


def _format_plan_weeks(plan_weeks):
    """Attach display-friendly workout text to each day in a plan."""
    formatted_weeks = []
    for week in plan_weeks or []:
        week_copy = dict(week)
        week_copy["days"] = []
        for day in week.get("days", []):
            day_copy = dict(day)
            day_copy["display_workout"] = _format_workout_text(day_copy.get("workout", ""))
            week_copy["days"].append(day_copy)
        formatted_weeks.append(week_copy)
    return formatted_weeks


def _build_heatmap(user_id: int, days: int = 84):
    """Build a dict {date_str: count} for the heatmap."""
    rows = WorkoutLog.weekly_counts(user_id, weeks=days // 7)
    counts = {str(r.logged_date): r[1] for r in rows}
    # Fill all days in range
    today = date.today()
    heatmap = {}
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        heatmap[str(d)] = counts.get(str(d), 0)
    return heatmap


def _match_exercises_for_day(workout_text: str):
    """
    Given a day's workout text (e.g. "Push-ups, Squats 3x12, Plank 30s"),
    return a list of exercise dicts from EXERCISE_LIBRARY that match,
    in the order they appear in the text. If nothing matches (e.g. rest day),
    return an empty list.
    """
    if not workout_text:
        return []

    text_lower = workout_text.lower()

    # Alias map (keep in sync with frontend aliases in workout.html)
    aliases = {
        "push-ups":          ["push-ups", "push ups", "pushup", "push up", "pushups"],
        "squats":            ["squat", "squats"],
        "plank":             ["plank", "planks"],
        "lunges":            ["lunge", "lunges"],
        "burpees":           ["burpee", "burpees"],
        "deadlift":          ["deadlift", "deadlifts", "romanian deadlift", "rdl"],
        "pull-ups":          ["pull-ups", "pull ups", "pullup", "pull up", "pullups"],
        "mountain-climbers": ["mountain climber", "mountain climbers", "mountain-climber"],
        "bench-press":       ["bench press", "bench", "chest press"],
        "rows":              ["row", "rows", "barbell row", "dumbbell row"],
        "overhead-press":    ["overhead press", "ohp", "shoulder press", "military press"],
        "cardio":            ["cardio", "run", "running", "jog", "jogging", "bike", "cycling", "cycle", "treadmill"],
        "yoga":              ["yoga", "stretch", "stretching", "mobility", "flexibility", "active recovery", "deload"],
        "circuit":           ["circuit", "full body", "full-body"],
        "crunches":          ["crunch", "crunches", "sit up", "sit ups", "sit-up", "sit-ups"],
        "bicep-curls":       ["curl", "curls", "bicep curl", "bicep curls"],
    }

    # Find first position of each matched exercise so we can preserve order
    matched = []
    for key, names in aliases.items():
        first_pos = -1
        for alias in names:
            idx = text_lower.find(alias)
            if idx != -1 and (first_pos == -1 or idx < first_pos):
                first_pos = idx
        if first_pos != -1 and key in EXERCISE_LIBRARY:
            matched.append((first_pos, EXERCISE_LIBRARY[key]))

    matched.sort(key=lambda t: t[0])
    return [ex for _, ex in matched]


@exercise_bp.route("/workout")
@login_required
def workout():

    plan = current_user.get_active_plan()
    plan_weeks = []
    if plan and plan.plan_json:
        plan_weeks = _format_plan_weeks(json.loads(plan.plan_json))

    streak = Streak.query.filter_by(user_id=current_user.id).first()
    exercises = _attach_video_links(list(EXERCISE_LIBRARY.values()))

    # Today's logs for checkbox state
    today_logs = WorkoutLog.today_logs(current_user.id)
    done_today = {log.exercise_name for log in today_logs}

    # Personal bests
    personal_bests = {}
    for ex in exercises:
        pb = WorkoutLog.personal_best(current_user.id, ex["name"])
        if pb:
            personal_bests[ex["name"]] = pb

    return render_template(
        "exercise/workout.html",
        exercises=exercises,
        plan_weeks=plan_weeks,
        plan=plan,
        streak=streak,
        done_today=done_today,
        personal_bests=personal_bests,
    )


@exercise_bp.route("/workout/day/<int:week_index>/<int:day_index>")
@login_required
def day_detail(week_index: int, day_index: int):
    """
    Show a dedicated page for a single day of the user's plan, with a
    card for every exercise (instructions, sets/reps, inline logging).
    """
    plan = current_user.get_active_plan()
    if not plan or not plan.plan_json:
        flash("You don't have an active plan yet. Generate one first!", "warning")
        return redirect(url_for("exercise.workout"))

    plan_weeks = _format_plan_weeks(json.loads(plan.plan_json))

    if week_index < 0 or week_index >= len(plan_weeks):
        flash("That week doesn't exist in your plan.", "warning")
        return redirect(url_for("exercise.workout"))

    week = plan_weeks[week_index]
    days = week.get("days", [])
    if day_index < 0 or day_index >= len(days):
        flash("That day doesn't exist in your plan.", "warning")
        return redirect(url_for("exercise.workout"))

    day = days[day_index]
    workout_text = day.get("display_workout") or day.get("workout", "")
    is_rest = "rest" in workout_text.lower()

    day_exercises = _attach_video_links(_match_exercises_for_day(workout_text))

    # Personal bests + today's logs for the matching exercises
    today_logs = WorkoutLog.today_logs(current_user.id)
    done_today = {log.exercise_name for log in today_logs}

    personal_bests = {}
    for ex in day_exercises:
        pb = WorkoutLog.personal_best(current_user.id, ex["name"])
        if pb:
            personal_bests[ex["name"]] = pb

    # Previous / Next navigation indices
    prev_idx = (week_index, day_index - 1) if day_index > 0 else \
               (week_index - 1, len(plan_weeks[week_index - 1]["days"]) - 1) if week_index > 0 else None
    next_idx = None
    if day_index + 1 < len(days):
        next_idx = (week_index, day_index + 1)
    elif week_index + 1 < len(plan_weeks):
        next_idx = (week_index + 1, 0)

    streak = Streak.query.filter_by(user_id=current_user.id).first()

    return render_template(
        "exercise/day_detail.html",
        plan=plan,
        week=week,
        week_index=week_index,
        day=day,
        day_index=day_index,
        workout_text=workout_text,
        is_rest=is_rest,
        day_exercises=day_exercises,
        done_today=done_today,
        personal_bests=personal_bests,
        prev_idx=prev_idx,
        next_idx=next_idx,
        streak=streak,
        total_weeks=len(plan_weeks),
    )


@exercise_bp.route("/log-exercise", methods=["POST"])
@login_required
def log_exercise():

    """Log a single exercise set with weight and reps."""
    exercise_name = request.form.get("exercise_name", "").strip()
    sets_done     = int(request.form.get("sets_done", 0) or 0)
    reps_done     = request.form.get("reps_done", "").strip()
    weight_kg_raw = request.form.get("weight_kg", "").strip()
    weight_kg     = float(weight_kg_raw) if weight_kg_raw else None
    notes         = request.form.get("notes", "").strip()

    if not exercise_name:
        flash("Please specify an exercise.", "warning")
        return redirect(url_for("exercise.workout"))

    log = WorkoutLog(
        user_id=current_user.id,
        exercise_name=exercise_name,
        sets_done=sets_done,
        reps_done=reps_done,
        weight_kg=weight_kg,
        notes=notes,
    )
    db.session.add(log)

    # Also update streak on exercise log
    streak = Streak.query.filter_by(user_id=current_user.id).first()
    if not streak:
        streak = Streak(user_id=current_user.id)
        db.session.add(streak)
    streak.log_activity()

    db.session.commit()

    pb = WorkoutLog.personal_best(current_user.id, exercise_name)
    if weight_kg and pb and weight_kg > pb:
        flash(f"🏅 New personal best on {exercise_name}: {weight_kg}kg!", "success")
    else:
        flash(f"✅ {exercise_name} logged!", "success")

    return redirect(url_for("exercise.workout"))


@exercise_bp.route("/log-workout", methods=["POST"])
@login_required
def log_workout():
    """Quick 'log all today' button — just updates streak."""
    streak = Streak.query.filter_by(user_id=current_user.id).first()
    if not streak:
        streak = Streak(user_id=current_user.id)
        db.session.add(streak)
    streak.log_activity()
    db.session.commit()
    flash("Workout logged! Keep up the streak! 🔥", "success")
    return redirect(url_for("exercise.workout"))


@exercise_bp.route("/history")
@login_required
def history():
    """Workout history page with heatmap and per-exercise PBs."""
    heatmap = _build_heatmap(current_user.id, days=84)
    recent_logs = (
        WorkoutLog.query
        .filter_by(user_id=current_user.id)
        .order_by(WorkoutLog.created_at.desc())
        .limit(50)
        .all()
    )
    # Build personal bests per exercise
    personal_bests = {}
    for ex in EXERCISE_LIBRARY.values():
        pb = WorkoutLog.personal_best(current_user.id, ex["name"])
        if pb:
            personal_bests[ex["name"]] = pb

    return render_template(
        "exercise/history.html",
        heatmap=heatmap,
        recent_logs=recent_logs,
        personal_bests=personal_bests,
    )


@exercise_bp.route("/api/substitute", methods=["POST"])
@login_required
def get_substitutes():
    """AI exercise substitution endpoint (#12)."""
    data          = request.get_json(silent=True) or {}
    exercise_name = data.get("exercise", "").strip()
    if not exercise_name:
        return jsonify({"error": "No exercise specified"}), 400

    try:
        from services.gemini_service import GeminiService
        svc = GeminiService()
        prompt = (
            f"Give me exactly 3 substitute exercises for '{exercise_name}'. "
            "The user may have limited equipment or joint limitations. "
            "For each, give: name, why it's a good substitute, and sets×reps. "
            "Keep the answer under 100 words total. Use bullet points."
        )
        result = svc.generate_content(prompt)
        return jsonify({"substitutes": result})
    except Exception as e:
        return jsonify({"substitutes": f"Could not generate substitutes: {str(e)}"}), 200
