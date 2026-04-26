"""
services/gemini_service.py
All Google Gemini AI interactions for FitAI.
Falls back to static data if no API key is configured.
"""

import json
import os
import re


def _get_client():
    """Return a configured Gemini GenerativeModel, or None if no key."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-2.0-flash")
    except Exception:
        return None


def _get_chat_client():
    """Return a lighter Gemini model for chat — tries flash models in order."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        # Try the latest lite model first (lowest quota usage)
        for model_name in ["gemini-2.0-flash-lite", "gemini-2.0-flash", "gemini-1.5-flash"]:
            try:
                return genai.GenerativeModel(model_name)
            except Exception:
                continue
    except Exception:
        pass
    return None


def build_user_context(user, profile) -> str:
    """Assemble a rich user context string for prompt injection."""
    goal_map = {
        "lose_weight": "Lose Weight",
        "build_muscle": "Build Muscle",
        "stay_fit": "Stay Fit / Maintain",
        "increase_endurance": "Increase Endurance",
        "improve_flexibility": "Improve Flexibility",
        "six_pack": "Get a Six Pack",
    }
    lines = [
        f"User: {user.username}",
        f"Age: {profile.age or 'unknown'}",
        f"Gender: {profile.gender or 'unspecified'}",
        f"Height: {profile.height_cm or '?'} cm",
        f"Weight: {profile.weight_kg or '?'} kg",
        f"BMI: {profile.bmi or '?'} ({profile.bmi_category})",
        f"Fitness Goal: {goal_map.get(profile.fitness_goal, profile.fitness_goal or 'General fitness')}",
        f"Experience Level: {profile.experience_level or 'beginner'}",
    ]
    return "\n".join(lines)


def _parse_json_from_response(text: str) -> dict | None:
    """Extract and parse the first JSON object from a Gemini response."""
    # Try to find a ```json ... ``` block first
    match = re.search(r"```json\s*([\s\S]*?)```", text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # Try raw JSON
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


# ---------------------------------------------------------------------------
# Daily Plan Generation
# ---------------------------------------------------------------------------

_FALLBACK_DAILY = {
    "workout": [
        {"exercise": "Push-Ups",         "sets": 3, "reps": "10-15", "rest": "60s", "muscles": "Chest, Triceps, Shoulders", "icon": "💪"},
        {"exercise": "Bodyweight Squats", "sets": 3, "reps": "12-15", "rest": "60s", "muscles": "Quads, Glutes, Hamstrings", "icon": "🦵"},
        {"exercise": "Plank Hold",        "sets": 3, "reps": "30-45s","rest": "45s", "muscles": "Core, Shoulders",           "icon": "🧱"},
        {"exercise": "Lunges",            "sets": 3, "reps": "10 each","rest": "60s", "muscles": "Quads, Glutes",             "icon": "🏃"},
        {"exercise": "Mountain Climbers", "sets": 3, "reps": "20 each","rest": "60s", "muscles": "Core, Shoulders, Cardio",   "icon": "⛰️"},
    ],
    "meal_plan": {
        "breakfast": {"name": "Oats with banana & honey", "calories": 380, "protein": "12g", "carbs": "68g", "fat": "6g"},
        "lunch":     {"name": "Grilled chicken salad with quinoa", "calories": 520, "protein": "42g", "carbs": "35g", "fat": "14g"},
        "dinner":    {"name": "Baked salmon with roasted vegetables", "calories": 480, "protein": "38g", "carbs": "28g", "fat": "18g"},
        "snacks":    [
            {"name": "Greek yogurt with berries", "calories": 160},
            {"name": "Handful of almonds",         "calories": 140},
        ],
        "total_calories": 1680,
    },
    "tips": [
        "Drink at least 2–3 litres of water today.",
        "Focus on form over speed — quality reps beat quantity every time.",
        "Get 7–8 hours of sleep to maximise recovery and fat loss.",
    ],
    "workout_title": "Full-Body Starter Session",
    "workout_notes": "Rest 60–90 seconds between sets. Stop if you feel sharp pain.",
}


def generate_daily_plan(user, profile) -> dict:
    """
    Generate today's workout + meal plan + tips for the user.
    Returns a dict with keys: workout, meal_plan, tips, workout_title, workout_notes.
    Falls back to _FALLBACK_DAILY if no API key or call fails.
    """
    model = _get_client()
    if model is None:
        return _adapt_fallback_to_goal(profile)

    context = build_user_context(user, profile)
    prompt = f"""
You are an expert personal trainer and nutritionist. Based on the user profile below, create a personalised daily fitness and nutrition plan.

USER PROFILE:
{context}

Respond ONLY with valid JSON matching this exact structure (no extra text, no markdown except the ```json wrapper):

```json
{{
  "workout_title": "short title for today's session",
  "workout_notes": "brief general guidance (1-2 sentences)",
  "workout": [
    {{
      "exercise": "Exercise Name",
      "sets": 3,
      "reps": "10-12",
      "rest": "60s",
      "muscles": "Primary muscles",
      "icon": "single emoji",
      "notes": "optional form tip",
      "instructions": ["Step-by-step instruction 1", "Step-by-step instruction 2"]
    }}
  ],
  "meal_plan": {{
    "breakfast": {{"name": "meal name", "calories": 400, "protein": "20g", "carbs": "50g", "fat": "10g"}},
    "lunch":     {{"name": "meal name", "calories": 550, "protein": "35g", "carbs": "45g", "fat": "15g"}},
    "dinner":    {{"name": "meal name", "calories": 500, "protein": "40g", "carbs": "30g", "fat": "18g"}},
    "snacks":    [
      {{"name": "snack name", "calories": 150}},
      {{"name": "snack name", "calories": 120}}
    ],
    "total_calories": 1720
  }},
  "tips": [
    "Personalised tip 1",
    "Personalised tip 2",
    "Personalised tip 3"
  ]
}}
```

Rules:
- Include 4-6 exercises appropriate for the user's experience level and goal
- Calorie targets should match goal (deficit for weight loss, surplus for muscle gain)
- Tips must be specific to this user's stats and goal
- All values must be realistic and safe
"""

    try:
        response = model.generate_content(prompt)
        data = _parse_json_from_response(response.text)
        if data and "workout" in data and "meal_plan" in data:
            return data
    except Exception:
        pass

    return _adapt_fallback_to_goal(profile)


def _adapt_fallback_to_goal(profile) -> dict:
    """Return a goal-adapted version of the fallback daily plan."""
    import copy
    plan = copy.deepcopy(_FALLBACK_DAILY)
    goal = profile.fitness_goal if profile else "stay_fit"

    if goal == "build_muscle":
        plan["workout_title"] = "Strength & Hypertrophy Session"
        plan["meal_plan"]["total_calories"] = 2400
        plan["tips"] = [
            "Eat 1.6–2g of protein per kg of body weight today.",
            "Focus on progressive overload — add a rep or small weight each session.",
            "Sleep is anabolic — aim for 8 hours tonight.",
        ]
    elif goal == "lose_weight":
        plan["workout_title"] = "Fat-Burn Circuit"
        plan["meal_plan"]["total_calories"] = 1500
        plan["tips"] = [
            "Stay in a moderate calorie deficit — don't skip meals.",
            "Add 10-minute walks after each meal to boost fat oxidation.",
            "Track your food intake today for better awareness.",
        ]
    elif goal == "increase_endurance":
        plan["workout_title"] = "Cardio Endurance Day"
        plan["tips"] = [
            "Warm up for 10 minutes before your main session.",
            "Zone 2 cardio (conversational pace) is key for aerobic base.",
            "Hydrate well — endurance work needs extra electrolytes.",
        ]
    elif goal == "six_pack":
        plan["workout_title"] = "30-Day Core Shred"
        plan["meal_plan"]["total_calories"] = 1600
        plan["tips"] = [
            "Abs are made in the kitchen — maintain your calorie deficit.",
            "Focus on full range of motion for every ab exercise.",
            "Don't forget your obliques and lower back for a balanced core.",
        ]
    return plan


# ---------------------------------------------------------------------------
# AI Coach Chat
# ---------------------------------------------------------------------------

def chat_with_coach(user, profile, user_message: str, history: list) -> str:
    """
    Send a message to the AI fitness coach and get a response.
    history: list of {"role": "user"|"model", "parts": ["text"]} dicts.
    Returns the AI response string.
    """
    model = _get_chat_client()
    if model is None:
        return (
            "I'm not connected to the AI service right now — please add your "
            "GEMINI_API_KEY to the .env file to enable the AI coach. 💪"
        )

    # Build a concise system context to minimise token usage
    goal_map = {
        "lose_weight": "Lose Weight", "build_muscle": "Build Muscle",
        "stay_fit": "Stay Fit", "increase_endurance": "Increase Endurance",
        "improve_flexibility": "Improve Flexibility",
        "six_pack": "Get a Six Pack",
    }
    if profile:
        ctx = (
            f"User: {user.username}, Age: {profile.age}, Gender: {profile.gender}, "
            f"BMI: {profile.bmi} ({profile.bmi_category}), "
            f"Goal: {goal_map.get(profile.fitness_goal, 'General fitness')}, "
            f"Level: {profile.experience_level or 'beginner'}"
        )
    else:
        ctx = f"User: {user.username}"

    system_prompt = (
        f"You are FitAI Coach, an expert personal trainer and nutritionist. "
        f"User profile: {ctx}. "
        f"Give personalised, actionable, encouraging advice. Be concise (under 200 words). "
        f"Never recommend unsafe practices."
    )

    try:
        # Use a minimal history (last 6 turns) to reduce tokens
        recent_history = history[-6:] if len(history) > 6 else history

        chat_history = [
            {"role": "user",  "parts": [system_prompt + " Acknowledge briefly."]},
            {"role": "model", "parts": ["Ready to help! 💪"]},
        ]
        chat_history.extend(recent_history)

        chat = model.start_chat(history=chat_history)
        response = chat.send_message(user_message)
        return response.text

    except Exception as e:
        err = str(e)
        if "429" in err or "quota" in err.lower():
            return (
                "⏳ The AI is temporarily rate-limited (free tier quota). "
                "Please wait a minute and try again — or check your Gemini API quota at "
                "https://aistudio.google.com/"
            )
        return f"Sorry, I ran into an issue. Please try again."


# ---------------------------------------------------------------------------
# Enhanced Fitness Plan (replaces static library)
# ---------------------------------------------------------------------------

def generate_ai_fitness_plan(user, profile) -> dict | None:
    """
    Generate a full 4-week structured fitness plan using Gemini.
    Returns a dict with title, description, weeks (list) — or None on failure.
    """
    model = _get_client()
    if model is None:
        return None

    context = build_user_context(user, profile)
    prompt = f"""
You are an expert personal trainer. Create a 4-week fitness plan for this user.
IMPORTANT: Always include explicit, specific exercise names (e.g. squats, push-ups, lunges, bench press, cardio, crunches, rows, overhead press, deadlift, pull-ups) in your workout descriptions. NEVER use generic terms like "Push", "Pull", "Lower body", "Upper body", or "HIIT" without explicitly listing the core exercises involved.

USER PROFILE:
{context}

Respond ONLY with valid JSON:

```json
{{
  "title": "Plan Name",
  "description": "1-2 sentence plan description",
  "weeks": [
    {{
      "week": 1,
      "days": [
        {{"day": "Monday",    "workout": "Description of workout"}},
        {{"day": "Tuesday",   "workout": "Rest / light activity"}},
        {{"day": "Wednesday", "workout": "Description"}},
        {{"day": "Thursday",  "workout": "Description"}},
        {{"day": "Friday",    "workout": "Description"}},
        {{"day": "Saturday",  "workout": "Description"}},
        {{"day": "Sunday",    "workout": "Rest"}}
      ]
    }}
  ]
}}
```

Include all 4 weeks. Workouts should progressively increase in intensity.
"""
    try:
        response = model.generate_content(prompt)
        data = _parse_json_from_response(response.text)
        if data and "weeks" in data:
            return data
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# GeminiService class — thin wrapper so routes can do:
#   from services.gemini_service import GeminiService
#   svc = GeminiService()
#   svc.generate_content(prompt)
# ---------------------------------------------------------------------------

class GeminiService:
    """Convenience class wrapper around the module-level Gemini helpers."""

    def generate_content(self, prompt: str) -> str:
        """
        Send a plain-text prompt to Gemini and return the response text.
        Falls back to an informative message if no API key is set.
        """
        model = _get_client()
        if model is None:
            return (
                "AI service is not configured. Please set GEMINI_API_KEY "
                "in your .env file to enable AI-powered features."
            )
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower():
                return (
                    "⏳ AI quota exceeded. Please wait a moment and try again."
                )
            return f"Sorry, AI is temporarily unavailable. Please try again."


def get_proactive_insight(user, profile):
    """Generate a quick, proactive fitness insight based on user profile and recent activity."""
    import random
    from models.workout_log import WorkoutLog
    from datetime import date
    
    # Check if user logged anything today
    today_logs = WorkoutLog.query.filter_by(user_id=user.id, logged_date=date.today()).all()
    has_logged_today = len(today_logs) > 0
    
    goal = profile.fitness_goal if profile else "stay_fit"
    
    # Adaptive responses based on activity
    if has_logged_today:
        success_messages = [
            f"Great work on today's session, {user.username}! Your consistency is paying off. 📈",
            "I saw you logged your workout today. Boom! That's how you build a six-pack. 🚀",
            "Session complete! Focus on your post-workout meal to maximize recovery. 🥗",
            "High five! 👋 You've put in the work today. Enjoy that post-workout endorphin rush.",
            "You crushed it today! Remember to hydrate and get plenty of rest tonight. 💧"
        ]
        return random.choice(success_messages)

    # General tips if nothing logged yet
    insights = {
        "six_pack": [
            "Abs are revealed in the kitchen! Focus on high-protein, whole foods today. 🥩",
            "Remember: Quality over quantity. Slow down your leg raises for max tension. 🐢",
            "Core stability is foundation. Have you practiced your deep breathing during planks? 🧘",
            "Consistency wins. Even a 5-minute core session keeps the momentum alive. ⚡",
            "Hydration keeps your muscles looking sharp and defined. Drink up! 💧"
        ],
        "build_muscle": [
            "Don't skip your sleep! 8 hours of rest is where the real growth happens. 😴",
            "Focus on progressive overload. Can you add 1kg to your main lift today? 🏋️",
            "Protein is your building block. Aim for 1.6g per kg of bodyweight. 🍖",
            "Compound movements like squats and rows are your best friends. 🛠️",
            "Mind-muscle connection is real. Visualize the muscle working on every rep. 🧠"
        ],
        "lose_weight": [
            "Every step counts. A 15-minute walk after lunch can boost your metabolism. 🚶",
            "Fiber is your secret weapon for feeling full. Add some greens to your plate! 🥦",
            "Don't drink your calories. Stick to water, tea, or black coffee today. ☕",
            "Listen to your body. There's a difference between hard work and pain. 👂",
            "Small wins lead to big changes. Celebrate making it to the gym today! 🎉"
        ],
        "stay_fit": [
            "Variety is the spice of life. Try a new exercise or path for your run! 🌈",
            "Mobility is just as important as strength. Spend 10 mins stretching. 🧘",
            "Energy follows action. Even if you feel tired, just start the warm-up. ⚡",
            "Fitness is a marathon, not a sprint. Enjoy the journey today! 🏁",
            "Balance is key. It's okay to enjoy a treat if you've stayed active. 🍦"
        ]
    }
    
    # Fallback to stay_fit if goal not found
    options = insights.get(goal, insights["stay_fit"])
    return random.choice(options)


