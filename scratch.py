import re

with open(r"C:\Users\User\fitness_app\routes\ai_routes.py", "r", encoding="utf-8") as f:
    content = f.read()

replacements = [
    (r"HIIT (.*?) \+ upper body weights", r"cardio \1 + bench press, rows"),
    (r"Lower body strength( \+ core)?", r"squats, lunges, deadlift\1"),
    (r"HIIT(.*?) \+ shoulders/arms", r"cardio\1 + overhead press, bicep curls"),
    (r"Core circuit", r"crunches, plank"),
    (r"Core \+ flexibility", r"crunches, plank + flexibility"),
    (r"Tabata (.*?) \+ chest/back", r"cardio \1 + bench press, rows"),
    (r"Tabata (.*?) \+ full upper body", r"cardio \1 + bench press, rows, overhead press"),
    (r"Full lower body", r"squats, lunges, deadlift"),
    (r"Heavy squats \+ HIIT finisher", r"Heavy squats + cardio finisher"),
    (r"Push \(chest/shoulders/triceps\)", r"Push: bench press, overhead press, push-ups"),
    (r"Pull \(back/biceps\) \+ core", r"Pull: pull-ups, rows, bicep curls + crunches"),
    (r"Legs \+ plyometrics", r"Legs: squats, lunges"),
    (r"Heavy deadlifts \+ sprint intervals", r"Heavy deadlifts + cardio sprints"),
    (r"Push \+ HIIT", r"bench press, overhead press + cardio"),
    (r"Pull \+ core", r"pull-ups, rows + crunches"),
    (r"Power cleans \+ HIIT", r"deadlift, rows + cardio"),
    (r"Tempo run (.*?)", r"cardio \1"),
    (r"Pull \+ heavy core", r"pull-ups, rows + crunches, plank"),
    (r"Legs heavy \+ box jumps", r"squats, lunges + box jumps"),
    (r"Max effort lower body", r"squats, deadlift max effort"),
    (r"Race simulation (.*?)", r"cardio race simulation \1"),
    (r"Push deload", r"bench press, overhead press deload"),
    (r"Pull deload", r"pull-ups, rows deload"),
    (r"Full body circuit (.*?)", r"cardio, squats, push-ups circuit \1"),
    (r"Push: chest/shoulders/triceps", r"Push: bench press, overhead press"),
    (r"Pull: back/biceps", r"Pull: pull-ups, rows, bicep curls"),
    (r"Legs: quads/hamstrings/calves", r"Legs: squats, lunges, deadlift"),
    (r"Push (.*?) heavier", r"bench press, overhead press \1 heavier"),
    (r"Push (.*?)(?!deload)", r"bench press, overhead press \1"),
    (r"Pull (.*?)(?!deload)", r"pull-ups, rows \1"),
    (r"Legs (.*?)(?!deload)", r"squats, lunges \1"),
    (r"Full body pump", r"push-ups, lunges, crunches"),
    (r"Upper Power: bench, row, OHP", r"bench press, rows, overhead press"),
    (r"Lower Power: squat, deadlift", r"squats, deadlift"),
    (r"Upper Hypertrophy", r"bench press, rows, overhead press hypertrophy"),
    (r"Lower Hypertrophy", r"squats, deadlift hypertrophy"),
    (r"Upper Power", r"bench press, rows, overhead press"),
    (r"Lower Power", r"squats, deadlift"),
    (r"Conditioning", r"cardio"),
    (r"Strength training", r"bench press, squats, rows"),
    (r"Cardio \+ core", r"cardio + crunches, plank"),
    (r"Core work", r"crunches, plank"),
    (r"HIIT", r"cardio"),
    (r"jog", r"cardio"),
    (r"run", r"cardio"),
    (r"cycling", r"cardio"),
    (r"swim", r"cardio"),
    (r"walk", r"cardio")
]

new_content = content
for pattern, repl in replacements:
    # Use re.IGNORECASE to match any case, but we need to be careful inside JSON
    # It's safer to just let it match the exact casing in routes/ai_routes.py
    new_content = re.sub(pattern, repl, new_content)

with open(r"C:\Users\User\fitness_app\routes\ai_routes.py", "w", encoding="utf-8") as f:
    f.write(new_content)
    
print("Updated ai_routes.py")
