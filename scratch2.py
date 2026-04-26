import re

with open('routes/ai_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('ccardioches', 'crunches')
with open('routes/ai_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)

with open('routes/exercise.py', 'r', encoding='utf-8') as f:
    content = f.read()

yoga_dict = '''    "yoga": {
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
    },'''

# Insert after bicep-curls block
content = content.replace('"icon": "💪",\n    },', '"icon": "💪",\n    },\n' + yoga_dict)

aliases_addition = '''        "cardio":            ["cardio", "run", "running", "jog", "jogging", "bike", "cycling", "cycle", "treadmill"],
        "yoga":              ["yoga", "stretch", "stretching", "mobility", "flexibility", "active recovery", "deload"],
        "circuit":           ["circuit"],'''

content = re.sub(r'"cardio":\s*\[.*?\]\,', aliases_addition, content)

with open('routes/exercise.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
