"""
routes/ai_routes.py
AI-powered routes: daily plans, meal suggestions, fitness coach chat,
and enhanced fitness plan generation using Google Gemini.
"""
import json
from flask import Blueprint, jsonify, request, flash, redirect, url_for, render_template
from flask_login import login_required, current_user
from extensions import db
from models.fitness_plan import FitnessPlan
from models.onboarding import OnboardingProfile
from models.daily_recommendation import DailyRecommendation
from services.gemini_service import has_ai_api_key, get_ai_connection_status

ai_bp = Blueprint("ai", __name__)

# ---------------------------------------------------------------------------
# Fallback plan library — used when no AI API key is configured
# ---------------------------------------------------------------------------

PLANS = {
    "six_pack": {
        "beginner": {
            "title": "30-Day Six Pack Challenge (Beginner)",
            "description": "Build core strength and definition with this high-frequency abdominal programme.",
            "weeks": [
                {"week": 1, "days": [
                    {"day": "Monday",    "workout": "Crunches 3x15, Plank 30s, Leg Raises 3x10"},
                    {"day": "Tuesday",   "workout": "Cardio 20 min + Russian Twists 3x20"},
                    {"day": "Wednesday", "workout": "Crunches 3x15, Bicycle Crunches 3x20"},
                    {"day": "Thursday",  "workout": "Rest / Stretching"},
                    {"day": "Friday",    "workout": "Plank 45s, Leg Raises 3x12, Crunches 3x20"},
                    {"day": "Saturday",  "workout": "Light Cardio 25 min"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 2, "days": [
                    {"day": "Monday",    "workout": "Crunches 4x15, Plank 60s, Leg Raises 3x12"},
                    {"day": "Tuesday",   "workout": "Cardio 25 min + Russian Twists 4x20"},
                    {"day": "Wednesday", "workout": "Bicycle Crunches 4x20, Mountain Climbers 3x30"},
                    {"day": "Thursday",  "workout": "Active Recovery / Yoga"},
                    {"day": "Friday",    "workout": "Plank 60s, Leg Raises 4x12, Crunches 4x20"},
                    {"day": "Saturday",  "workout": "Cardio 30 min"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 3, "days": [
                    {"day": "Monday",    "workout": "Crunches 4x20, Plank 90s, Leg Raises 4x15"},
                    {"day": "Tuesday",   "workout": "HIIT Cardio 20 min + Russian Twists 4x30"},
                    {"day": "Wednesday", "workout": "Bicycle Crunches 4x25, Mountain Climbers 4x40"},
                    {"day": "Thursday",  "workout": "Rest"},
                    {"day": "Friday",    "workout": "Plank 90s, Leg Raises 4x15, Crunches 4x25"},
                    {"day": "Saturday",  "workout": "HIIT 25 min"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 4, "days": [
                    {"day": "Monday",    "workout": "Crunches 5x20, Plank 2 mins, Leg Raises 4x20"},
                    {"day": "Tuesday",   "workout": "HIIT 30 min + Russian Twists 5x30"},
                    {"day": "Wednesday", "workout": "Bicycle Crunches 5x30, Mountain Climbers 5x50"},
                    {"day": "Thursday",  "workout": "Active Recovery"},
                    {"day": "Friday",    "workout": "Plank 2 mins, Leg Raises 5x20, Crunches 5x25"},
                    {"day": "Saturday",  "workout": "The 30-Day Finisher: Max Plank + 100 Crunches"},
                    {"day": "Sunday",    "workout": "Victory Rest"},
                ]},
            ],
        },
        "intermediate": {
            "title": "30-Day Six Pack Challenge (Intermediate)",
            "description": "Intense core conditioning and fat-burning routines to reveal your abs.",
            "weeks": [
                {"week": 1, "days": [
                    {"day": "Monday",    "workout": "Plank 60s, Leg Raises 4x15, Russian Twists 4x30"},
                    {"day": "Tuesday",   "workout": "HIIT 25 min + Bicycle Crunches 4x30"},
                    {"day": "Wednesday", "workout": "Mountain Climbers 4x40, Plank 60s"},
                    {"day": "Thursday",  "workout": "Rest"},
                    {"day": "Friday",    "workout": "Crunches 4x25, Leg Raises 4x15, Bicycle Crunches 4x30"},
                    {"day": "Saturday",  "workout": "Cardio 40 min"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 2, "days": [
                    {"day": "Monday",    "workout": "Plank 90s, Leg Raises 4x20, Russian Twists 4x40"},
                    {"day": "Tuesday",   "workout": "HIIT 30 min + Bicycle Crunches 4x40"},
                    {"day": "Wednesday", "workout": "Mountain Climbers 5x40, Plank 90s"},
                    {"day": "Thursday",  "workout": "Yoga 30 min"},
                    {"day": "Friday",    "workout": "Crunches 5x25, Leg Raises 4x20, Bicycle Crunches 5x30"},
                    {"day": "Saturday",  "workout": "Cardio 45 min"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 3, "days": [
                    {"day": "Monday",    "workout": "Plank 2 mins, Leg Raises 5x20, Russian Twists 5x40"},
                    {"day": "Tuesday",   "workout": "HIIT 35 min + Bicycle Crunches 5x40"},
                    {"day": "Wednesday", "workout": "Mountain Climbers 5x50, Plank 2 mins"},
                    {"day": "Thursday",  "workout": "Rest"},
                    {"day": "Friday",    "workout": "Crunches 5x30, Leg Raises 5x20, Bicycle Crunches 5x40"},
                    {"day": "Saturday",  "workout": "Cardio 50 min"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 4, "days": [
                    {"day": "Monday",    "workout": "Plank 3 mins, Leg Raises 5x25, Russian Twists 5x50"},
                    {"day": "Tuesday",   "workout": "HIIT 40 min + Bicycle Crunches 5x50"},
                    {"day": "Wednesday", "workout": "Mountain Climbers 6x50, Plank 3 mins"},
                    {"day": "Thursday",  "workout": "Active Recovery"},
                    {"day": "Friday",    "workout": "Final Burn: 200 Crunches, 100 Leg Raises"},
                    {"day": "Saturday",  "workout": "Cardio 60 min"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
            ],
        },
        "advanced": {
            "title": "30-Day Six Pack Challenge (Elite)",
            "description": "High-volume, elite-level abdominal training and high-intensity conditioning.",
            "weeks": [
                {"week": 1, "days": [
                    {"day": "Monday",    "workout": "Plank 2 mins, Leg Raises 5x20, Russian Twists 5x40"},
                    {"day": "Tuesday",   "workout": "HIIT 30 min + Bicycle Crunches 5x40"},
                    {"day": "Wednesday", "workout": "Mountain Climbers 5x50, Plank 2 mins"},
                    {"day": "Thursday",  "workout": "Rest"},
                    {"day": "Friday",    "workout": "Crunches 5x30, Leg Raises 5x20, Bicycle Crunches 5x40"},
                    {"day": "Saturday",  "workout": "Cardio 50 min"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 2, "days": [
                    {"day": "Monday",    "workout": "Plank 3 mins, Leg Raises 5x25, Russian Twists 5x50"},
                    {"day": "Tuesday",   "workout": "HIIT 40 min + Bicycle Crunches 5x50"},
                    {"day": "Wednesday", "workout": "Mountain Climbers 6x50, Plank 3 mins"},
                    {"day": "Thursday",  "workout": "Yoga 30 min"},
                    {"day": "Friday",    "workout": "Crunches 6x30, Leg Raises 6x25, Bicycle Crunches 6x50"},
                    {"day": "Saturday",  "workout": "Cardio 60 min"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 3, "days": [
                    {"day": "Monday",    "workout": "Plank 4 mins, Leg Raises 6x30, Russian Twists 6x60"},
                    {"day": "Tuesday",   "workout": "HIIT 50 min + Bicycle Crunches 6x60"},
                    {"day": "Wednesday", "workout": "Mountain Climbers 8x50, Plank 4 mins"},
                    {"day": "Thursday",  "workout": "Rest"},
                    {"day": "Friday",    "workout": "Abs to Failure: Plank, Crunches, Leg Raises"},
                    {"day": "Saturday",  "workout": "HIIT 60 min"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 4, "days": [
                    {"day": "Monday",    "workout": "Plank 5 mins, Leg Raises 8x30, Russian Twists 8x60"},
                    {"day": "Tuesday",   "workout": "HIIT 60 min + Bicycle Crunches 8x60"},
                    {"day": "Wednesday", "workout": "The Ultimate Circuit: 10 rounds of core"},
                    {"day": "Thursday",  "workout": "Active Recovery"},
                    {"day": "Friday",    "workout": "30-Day Finale: 300 Crunches, 5 min Plank"},
                    {"day": "Saturday",  "workout": "HIIT 75 min"},
                    {"day": "Sunday",    "workout": "Warrior Rest"},
                ]},
            ],
        },
    },
    "lose_weight": {
        "beginner": {
            "title": "Beginner Fat-Burn Programme",
            "description": "A gentle 4-week plan combining cardio and bodyweight exercises to ignite fat loss.",
            "weeks": [
                {
                    "week": 1,
                    "days": [
                        {"day": "Monday",    "workout": "30-min brisk cardio + 3×10 squats"},
                        {"day": "Tuesday",   "workout": "Rest / light stretching"},
                        {"day": "Wednesday", "workout": "20-min cardio + 3×10 lunges"},
                        {"day": "Thursday",  "workout": "Rest"},
                        {"day": "Friday",    "workout": "30-min cardio + 3×15 push-ups"},
                        {"day": "Saturday",  "workout": "Yoga / flexibility 20 min"},
                        {"day": "Sunday",    "workout": "Rest"},
                    ],
                },
                {
                    "week": 2,
                    "days": [
                        {"day": "Monday",    "workout": "35-min brisk cardio + 3×12 squats"},
                        {"day": "Tuesday",   "workout": "20-min cardio (30s on / 30s off)"},
                        {"day": "Wednesday", "workout": "Rest"},
                        {"day": "Thursday",  "workout": "25-min cardio + core circuit"},
                        {"day": "Friday",    "workout": "Rest"},
                        {"day": "Saturday",  "workout": "35-min cardio + 3×15 push-ups"},
                        {"day": "Sunday",    "workout": "Rest"},
                    ],
                },
                {
                    "week": 3,
                    "days": [
                        {"day": "Monday",    "workout": "40-min cardio"},
                        {"day": "Tuesday",   "workout": "Full-body circuit × 3 rounds"},
                        {"day": "Wednesday", "workout": "Rest"},
                        {"day": "Thursday",  "workout": "25-min cardio"},
                        {"day": "Friday",    "workout": "30-min cardio or cycle"},
                        {"day": "Saturday",  "workout": "Yoga 30 min"},
                        {"day": "Sunday",    "workout": "Rest"},
                    ],
                },
                {
                    "week": 4,
                    "days": [
                        {"day": "Monday",    "workout": "45-min cardio"},
                        {"day": "Tuesday",   "workout": "cardio 30 min"},
                        {"day": "Wednesday", "workout": "Rest"},
                        {"day": "Thursday",  "workout": "Full-body circuit × 4 rounds"},
                        {"day": "Friday",    "workout": "40-min cycle"},
                        {"day": "Saturday",  "workout": "Active rest — hike or cardio"},
                        {"day": "Sunday",    "workout": "Rest"},
                    ],
                },
            ],
        },
        "intermediate": {
            "title": "Intermediate Fat-Loss Blast",
            "description": "4-week mixed cardio and strength programme to accelerate fat burning.",
            "weeks": [
                {"week": 1, "days": [
                    {"day": "Monday",    "workout": "cardio 30 min + bench press, rows"},
                    {"day": "Tuesday",   "workout": "5 km cardio"},
                    {"day": "Wednesday", "workout": "squats, lunges, deadlift"},
                    {"day": "Thursday",  "workout": "Rest"},
                    {"day": "Friday",    "workout": "cardio 35 min"},
                    {"day": "Saturday",  "workout": "crunches, plank + flexibility"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 2, "days": [
                    {"day": "Monday",    "workout": "cardio 35 min + bench press, rows"},
                    {"day": "Tuesday",   "workout": "6 km cardio"},
                    {"day": "Wednesday", "workout": "squats, lunges, deadlift + core"},
                    {"day": "Thursday",  "workout": "Active rest"},
                    {"day": "Friday",    "workout": "cardio 40 min"},
                    {"day": "Saturday",  "workout": "Yoga 30 min"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 3, "days": [
                    {"day": "Monday",    "workout": "cardio 20 min + bench press, rows"},
                    {"day": "Tuesday",   "workout": "7 km cardio"},
                    {"day": "Wednesday", "workout": "squats, lunges + glutes"},
                    {"day": "Thursday",  "workout": "Rest"},
                    {"day": "Friday",    "workout": "cardio 40 min + overhead press, bicep curls"},
                    {"day": "Saturday",  "workout": "crunches, plank"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 4, "days": [
                    {"day": "Monday",    "workout": "cardio 25 min + bench press, rows, overhead press"},
                    {"day": "Tuesday",   "workout": "8 km cardio"},
                    {"day": "Wednesday", "workout": "squats, lunges, deadlift"},
                    {"day": "Thursday",  "workout": "Rest"},
                    {"day": "Friday",    "workout": "cardio 45 min"},
                    {"day": "Saturday",  "workout": "Deload — yoga / cardio"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
            ],
        },
        "advanced": {
            "title": "Advanced Shred Programme",
            "description": "High-intensity 4-week programme combining heavy lifting and metabolic conditioning.",
            "weeks": [
                {"week": 1, "days": [
                    {"day": "Monday",    "workout": "Heavy squats + cardio finisher"},
                    {"day": "Tuesday",   "workout": "10 km cardio"},
                    {"day": "Wednesday", "workout": "Push: bench press, overhead press, push-ups"},
                    {"day": "Thursday",  "workout": "Pull: pull-ups, rows, bicep curls + crunches"},
                    {"day": "Friday",    "workout": "cardio 45 min"},
                    {"day": "Saturday",  "workout": "Legs: squats, lunges"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 2, "days": [
                    {"day": "Monday",    "workout": "Heavy deadlifts + cardio sprints"},
                    {"day": "Tuesday",   "workout": "12 km cardio"},
                    {"day": "Wednesday", "workout": "bench press, overhead press + cardio 20 min"},
                    {"day": "Thursday",  "workout": "pull-ups, rows + crunches"},
                    {"day": "Friday",    "workout": "cardio 50 min"},
                    {"day": "Saturday",  "workout": "Legs: squats, lunges"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 3, "days": [
                    {"day": "Monday",    "workout": "deadlift, rows + cardio"},
                    {"day": "Tuesday",   "workout": "cardio 10 km"},
                    {"day": "Wednesday", "workout": "bench press, overhead press + cardio"},
                    {"day": "Thursday",  "workout": "pull-ups, rows + crunches, plank"},
                    {"day": "Friday",    "workout": "cardio 55 min"},
                    {"day": "Saturday",  "workout": "squats, lunges + box jumps"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 4, "days": [
                    {"day": "Monday",    "workout": "squats, deadlift max effort"},
                    {"day": "Tuesday",   "workout": "cardio race simulation 12 km"},
                    {"day": "Wednesday", "workout": "bench press, overhead press deload"},
                    {"day": "Thursday",  "workout": "pull-ups, rows deload"},
                    {"day": "Friday",    "workout": "cardio 45 min"},
                    {"day": "Saturday",  "workout": "Full body deload"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
            ],
        },
    },
    "build_muscle": {
        "beginner": {
            "title": "Beginner Muscle-Building Foundation",
            "description": "4-week full-body strength programme to build your lifting base.",
            "weeks": [
                {"week": 1, "days": [
                    {"day": "Monday",    "workout": "Full body A: squat, bench, row 3×8"},
                    {"day": "Tuesday",   "workout": "Rest / light cardio"},
                    {"day": "Wednesday", "workout": "Full body B: deadlift, OHP, pull-ups 3×8"},
                    {"day": "Thursday",  "workout": "Rest"},
                    {"day": "Friday",    "workout": "Full body A: squat, bench, row 3×10"},
                    {"day": "Saturday",  "workout": "Light cardio 20 min"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 2, "days": [
                    {"day": "Monday",    "workout": "Full body A: squat, bench, row 3×10"},
                    {"day": "Tuesday",   "workout": "Rest"},
                    {"day": "Wednesday", "workout": "Full body B: deadlift, OHP, pull-ups 3×10"},
                    {"day": "Thursday",  "workout": "Rest"},
                    {"day": "Friday",    "workout": "Full body A: squat, bench, row 3×12"},
                    {"day": "Saturday",  "workout": "crunches, plank 20 min"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 3, "days": [
                    {"day": "Monday",    "workout": "Full body A: squat, bench, row 4×8 heavier"},
                    {"day": "Tuesday",   "workout": "Rest"},
                    {"day": "Wednesday", "workout": "Full body B: deadlift, OHP, pull-ups 4×8"},
                    {"day": "Thursday",  "workout": "Rest"},
                    {"day": "Friday",    "workout": "Full body A: squat, bench, row 4×10"},
                    {"day": "Saturday",  "workout": "Stretching + mobility"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 4, "days": [
                    {"day": "Monday",    "workout": "Full body A: squat, bench, row deload 2×8"},
                    {"day": "Tuesday",   "workout": "Rest"},
                    {"day": "Wednesday", "workout": "Full body B: deadlift, OHP, pull-ups deload 2×8"},
                    {"day": "Thursday",  "workout": "Rest"},
                    {"day": "Friday",    "workout": "Full body A: squat, bench, row 3×10"},
                    {"day": "Saturday",  "workout": "Active recovery"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
            ],
        },
        "intermediate": {
            "title": "Intermediate Hypertrophy Split",
            "description": "4-week Push/Pull/squats, lunges split for muscle hypertrophy.",
            "weeks": [
                {"week": 1, "days": [
                    {"day": "Monday",    "workout": "Push: bench press, overhead press 4×10"},
                    {"day": "Tuesday",   "workout": "Pull: pull-ups, rows, bicep curls 4×10"},
                    {"day": "Wednesday", "workout": "Legs: squats, lunges, deadlift 4×10"},
                    {"day": "Thursday",  "workout": "Rest"},
                    {"day": "Friday",    "workout": "bench press, overhead press 4×10"},
                    {"day": "Saturday",  "workout": "pull-ups, rows 4×10"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 2, "days": [
                    {"day": "Monday",    "workout": "bench press, overhead press 4×12"},
                    {"day": "Tuesday",   "workout": "pull-ups, rows 4×12"},
                    {"day": "Wednesday", "workout": "squats, lunges 4×12"},
                    {"day": "Thursday",  "workout": "Rest"},
                    {"day": "Friday",    "workout": "bench press, overhead press 4×12"},
                    {"day": "Saturday",  "workout": "pull-ups, rows 4×12"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 3, "days": [
                    {"day": "Monday",    "workout": "bench press, overhead press 5×10 heavier"},
                    {"day": "Tuesday",   "workout": "pull-ups, rows 5×10"},
                    {"day": "Wednesday", "workout": "squats, lunges 5×10"},
                    {"day": "Thursday",  "workout": "Rest"},
                    {"day": "Friday",    "workout": "bench press, overhead press 5×8"},
                    {"day": "Saturday",  "workout": "pull-ups, rows 5×8"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 4, "days": [
                    {"day": "Monday",    "workout": "bench press, overhead press deload 3×8"},
                    {"day": "Tuesday",   "workout": "pull-ups, rows deload 3×8"},
                    {"day": "Wednesday", "workout": "squats, lunges deload 3×10"},
                    {"day": "Thursday",  "workout": "Rest"},
                    {"day": "Friday",    "workout": "push-ups, lunges, crunches 3×15"},
                    {"day": "Saturday",  "workout": "Active recovery"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
            ],
        },
        "advanced": {
            "title": "Advanced Power Hypertrophy",
            "description": "4-week PHUL programme blending power and hypertrophy training.",
            "weeks": [
                {"week": 1, "days": [
                    {"day": "Monday",    "workout": "bench press, rows, overhead press 4×5"},
                    {"day": "Tuesday",   "workout": "squats, deadlift 4×5"},
                    {"day": "Wednesday", "workout": "Rest"},
                    {"day": "Thursday",  "workout": "bench press, rows, overhead press hypertrophy: 4×10-12"},
                    {"day": "Friday",    "workout": "squats, deadlift hypertrophy: 4×10-12"},
                    {"day": "Saturday",  "workout": "Active rest"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 2, "days": [
                    {"day": "Monday",    "workout": "bench press, rows, overhead press 4×5 +weight"},
                    {"day": "Tuesday",   "workout": "squats, deadlift 4×5 +weight"},
                    {"day": "Wednesday", "workout": "Rest"},
                    {"day": "Thursday",  "workout": "bench press, rows, overhead press hypertrophy 4×12"},
                    {"day": "Friday",    "workout": "squats, deadlift hypertrophy 4×12"},
                    {"day": "Saturday",  "workout": "Core + mobility"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 3, "days": [
                    {"day": "Monday",    "workout": "bench press, rows, overhead press 5×5"},
                    {"day": "Tuesday",   "workout": "squats, deadlift 5×5"},
                    {"day": "Wednesday", "workout": "Rest"},
                    {"day": "Thursday",  "workout": "bench press, rows, overhead press hypertrophy 5×10"},
                    {"day": "Friday",    "workout": "squats, deadlift hypertrophy 5×10"},
                    {"day": "Saturday",  "workout": "cardio 20 min"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
                {"week": 4, "days": [
                    {"day": "Monday",    "workout": "bench press, rows, overhead press deload 3×3"},
                    {"day": "Tuesday",   "workout": "squats, deadlift deload 3×3"},
                    {"day": "Wednesday", "workout": "Rest"},
                    {"day": "Thursday",  "workout": "bench press, rows, overhead press hypertrophy deload 3×10"},
                    {"day": "Friday",    "workout": "squats, deadlift hypertrophy deload 3×10"},
                    {"day": "Saturday",  "workout": "Full body mobility"},
                    {"day": "Sunday",    "workout": "Rest"},
                ]},
            ],
        },
    },
}

_GENERIC_PLAN = {
    "title": "General Fitness Programme",
    "description": "A balanced 4-week plan for overall fitness and wellbeing.",
    "weeks": [
        {"week": w, "days": [
            {"day": "Monday",    "workout": "Cardio 30 min"},
            {"day": "Tuesday",   "workout": "bench press, squats, rows 30 min"},
            {"day": "Wednesday", "workout": "Rest"},
            {"day": "Thursday",  "workout": "cardio + crunches, plank 30 min"},
            {"day": "Friday",    "workout": "bench press, squats, rows 30 min"},
            {"day": "Saturday",  "workout": "Active recovery — yoga/cardio"},
            {"day": "Sunday",    "workout": "Rest"},
        ]} for w in range(1, 5)
    ],
}


def generate_plan_for_user(user, profile):
    """
    Generate (or regenerate) a 4-week fitness plan.
    Tries Gemini AI first; falls back to local plan library.
    """
    # Try AI generation first
    try:
        from services.gemini_service import generate_ai_fitness_plan
        ai_plan = generate_ai_fitness_plan(user, profile)
        if ai_plan:
            FitnessPlan.query.filter_by(user_id=user.id, is_active=True).update({"is_active": False})
            db.session.commit()
            new_plan = FitnessPlan(
                user_id=user.id,
                title=ai_plan["title"],
                description=ai_plan["description"],
                plan_json=json.dumps(ai_plan.get("weeks", [])),
                goal=profile.fitness_goal or "stay_fit",
                experience_level=profile.experience_level or "beginner",
                weeks_duration=4,
                is_active=True,
            )
            db.session.add(new_plan)
            db.session.commit()
            return new_plan
    except Exception:
        pass

    # Fallback to static library
    goal = profile.fitness_goal or "stay_fit"
    level = profile.experience_level or "beginner"
    plan_data = PLANS.get(goal, {}).get(level) or _GENERIC_PLAN

    FitnessPlan.query.filter_by(user_id=user.id, is_active=True).update({"is_active": False})
    db.session.commit()

    new_plan = FitnessPlan(
        user_id=user.id,
        title=plan_data["title"],
        description=plan_data["description"],
        plan_json=json.dumps(plan_data.get("weeks", [])),
        goal=goal,
        experience_level=level,
        weeks_duration=4,
        is_active=True,
    )
    db.session.add(new_plan)
    db.session.commit()
    return new_plan


# ---------------------------------------------------------------------------
# Blueprint routes — existing
# ---------------------------------------------------------------------------

@ai_bp.route("/regenerate", methods=["POST"])
@login_required
def regenerate():
    profile = current_user.profile
    if not profile:
        flash("Please complete your profile first.", "error")
        return redirect(url_for("dashboard.index"))
    generate_plan_for_user(current_user, profile)
    flash("New fitness plan generated! 🤖", "success")
    return redirect(url_for("dashboard.index"))


@ai_bp.route("/plan-json")
@login_required
def plan_json():
    plan = current_user.get_active_plan()
    if not plan:
        return jsonify({"error": "No active plan"}), 404
    return jsonify({
        "title": plan.title,
        "description": plan.description,
        "weeks": json.loads(plan.plan_json or "[]"),
    })


# ---------------------------------------------------------------------------
# NEW: Daily AI Plan page
# ---------------------------------------------------------------------------

@ai_bp.route("/daily")
@login_required
def daily():
    profile = current_user.profile
    if not profile:
        flash("Complete your profile first to get personalised plans.", "info")
        return redirect(url_for("onboarding.step1"))

    # Check cache
    rec = DailyRecommendation.get_today(current_user.id)
    ai_available = has_ai_api_key()
    ai_status = get_ai_connection_status()

    return render_template(
        "ai/daily.html",
        rec=rec,
        profile=profile,
        ai_available=ai_available,
        ai_status=ai_status,
    )


@ai_bp.route("/daily/generate", methods=["POST"])
@login_required
def daily_generate():
    """Generate (or refresh) today's AI daily plan."""
    profile = current_user.profile
    if not profile:
        flash("Complete your profile first.", "error")
        return redirect(url_for("ai.daily"))

    from services.gemini_service import generate_daily_plan
    data = generate_daily_plan(current_user, profile)
    DailyRecommendation.create_from_data(current_user.id, data)
    return redirect(url_for("ai.daily"))


# ---------------------------------------------------------------------------
# NEW: AI Coach chat page
# ---------------------------------------------------------------------------

@ai_bp.route("/coach")
@login_required
def coach():
    profile = current_user.profile
    ai_available = has_ai_api_key()
    ai_status = get_ai_connection_status()
    return render_template(
        "ai/coach.html",
        profile=profile,
        ai_available=ai_available,
        ai_status=ai_status,
    )


@ai_bp.route("/chat-api", methods=["POST"])
@login_required
def chat_api():
    """JSON endpoint for AI coach chat."""
    profile = current_user.profile
    payload = request.get_json(silent=True) or {}
    user_message = (payload.get("message") or "").strip()
    history = payload.get("history", [])

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    from services.gemini_service import chat_with_coach
    reply = chat_with_coach(current_user, profile, user_message, history)
    return jsonify({"reply": reply})


@ai_bp.route("/challenge/six-pack")
@login_required
def challenge_six_pack():
    """View all exercises and instructions for the Six Pack Challenge."""
    from models.workout_log import WorkoutLog
    from models.daily_recommendation import DailyRecommendation
    
    active_plan = current_user.get_active_plan()
    days_completed = 0
    start_date = None
    
    challenge_exercise_names = [
        "Leg Raises", "Russian Twists", "Bicycle Crunches", 
        "Forearm Plank", "Mountain Climbers", "Abdominal Crunches"
    ]

    if active_plan and active_plan.goal == "six_pack":
        # Count unique days where user logged at least one challenge exercise AFTER starting the challenge
        days_completed = db.session.query(db.func.count(db.func.distinct(WorkoutLog.logged_date))).filter(
            WorkoutLog.user_id == current_user.id,
            WorkoutLog.created_at >= active_plan.created_at,
            WorkoutLog.exercise_name.in_(challenge_exercise_names)
        ).scalar() or 0

    progress_pct = min(100, int((days_completed / 30) * 100))
    # If 0 days done, you are on Day 1. If 1 day done, you are on Day 2.
    current_day = min(30, days_completed + 1)
    if progress_pct == 0:
        current_day = 1

    challenge_exercises = {
        "leg_raises": {
            "name": "Leg Raises",
            "icon": "⚓",
            "muscles": "Lower Abs",
            "difficulty": "Intermediate",
            "reps": "3x15",
            "instructions": [
                "Lie flat on your back with legs straight.",
                "Place hands under your glutes for support.",
                "Slowly lift your legs until they are vertical.",
                "Lower them back down without touching the floor.",
                "Keep your lower back pressed into the mat."
            ],
            "common_mistakes": "Arching the lower back or using momentum to swing legs.",
            "video_id": "wnXPsXygnVI"
        },
        "russian_twists": {
            "name": "Russian Twists",
            "icon": "🌪️",
            "muscles": "Obliques",
            "difficulty": "Intermediate",
            "reps": "3x30 (15 each side)",
            "instructions": [
                "Sit with knees bent and feet slightly off the floor.",
                "Lean back at a 45-degree angle to engage the core.",
                "Clasp hands together in front of your chest.",
                "Twist your torso to the right, then to the left.",
                "Focus on moving from the waist, not just the arms."
            ],
            "common_mistakes": "Twisting only the arms rather than the entire torso.",
            "video_id": "xcLqUjo8IeE"
        },
        "bicycle_crunches": {
            "name": "Bicycle Crunches",
            "icon": "🚲",
            "muscles": "Full Core / Obliques",
            "difficulty": "Intermediate",
            "reps": "3x20 each side",
            "instructions": [
                "Lie on your back with hands behind your head.",
                "Bring knees toward your chest and lift shoulder blades off floor.",
                "Straighten your right leg while turning upper body to the left.",
                "Bring right elbow toward left knee.",
                "Switch sides in a fluid pedaling motion."
            ],
            "common_mistakes": "Pulling on the neck or moving too fast without control.",
            "video_id": "hlcQQdYSJgY"
        },
        "plank": {
            "name": "Forearm Plank",
            "icon": "🧱",
            "muscles": "Core Stability",
            "difficulty": "Beginner",
            "reps": "3x60s",
            "instructions": [
                "Place forearms on the floor, elbows under shoulders.",
                "Extend legs back, balancing on toes.",
                "Keep body in a straight line from head to heels.",
                "Squeeze your glutes and engage your core.",
                "Hold without letting your hips sag or pike."
            ],
            "common_mistakes": "Allowing the hips to sag or looking too far forward.",
            "video_id": "TvxNkmjdhMM"
        },
        "mountain_climbers": {
            "name": "Mountain Climbers",
            "icon": "⛰️",
            "muscles": "Core / Cardio",
            "difficulty": "Intermediate",
            "reps": "3x40",
            "instructions": [
                "Start in a high plank (push-up) position.",
                "Drive your right knee toward your chest.",
                "Quickly switch legs, driving the left knee forward.",
                "Maintain a flat back throughout the movement.",
                "Keep the pace fast to boost heart rate."
            ],
            "common_mistakes": "Bouncing the hips too high or not bringing knees far enough.",
            "video_id": "lvaQcFaxL00"
        },
        "crunches": {
            "name": "Abdominal Crunches",
            "icon": "🔥",
            "muscles": "Upper Abs",
            "difficulty": "Beginner",
            "reps": "3x20",
            "instructions": [
                "Lie on your back with knees bent and feet flat.",
                "Place hands lightly behind your head or across chest.",
                "Lift your shoulders toward the ceiling using your abs.",
                "Exhale as you crunch up, inhale as you lower.",
                "Do not pull on your neck with your hands."
            ],
            "common_mistakes": "Using the hands to pull the head forward.",
            "video_id": "_M2Etme-tfE"
        }
    }
    return render_template(
        "ai/challenge.html", 
        exercises=challenge_exercises,
        progress_pct=progress_pct,
        days_completed=days_completed,
        current_day=current_day
    )
